"""Moteur de stock local de IL-2 Korea Stock Manager.

Ce module ne connaît pas Tkinter et ne contient aucun texte destiné
à l'interface utilisateur.

Responsabilités Phase 2B :
- stock initial STANDARD d'une nouvelle carrière ;
- signature/snapshot de synchronisation ;
- synchronisation incrémentale avec ammoQty ;
- delta ammoQty reçu pendant l'exécution ;
- consommation atomique du stock lors d'une mission ;
- opérations directes de maintenance du stock local.

IMPORTANT :
- la DB IL-2 n'est jamais ouverte ici ;
- une baisse de ammoQty ne retire JAMAIS de stock concret ;
- les calculs de répartition sont exécutés AVANT les transactions
  d'écriture afin d'éviter les auto-verrouillages SQLite.
"""

from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

import local_database as local_db

from app_data import (
    AVIONS_EMPORTS,
    trier_munitions_logiquement,
)


# ============================================================
# STOCK INITIAL STANDARD
# ============================================================

STOCK_INITIAL_STANDARD_PAR_AVION = {
    "F-51D": {
        'Roquette aérienne semi-perforante à haute vitesse HVAR 5"': 420,
        'Roquette aérienne à haute vitesse HVAR 5"': 900,
        "Réservoir de napalm 110 gal": 180,
        "Réservoir largable 110 gal": 180,
        "Réservoir largable 75 gal": 140,
        "AN-M64A1 500 lb": 320,
        "AN-M65A1 1000 lb": 80,
        "Bombe éclairante à parachute AN-M26A1": 30,
        "M26A2 500 lb à sous-munitions": 90,
        "M29A1 500 lb à sous-munitions": 70,
        'Roquette ATAR 6,5"': 180,
    },

    "F-80C-10": {
        "M29A1 500 lb à sous-munitions": 80,
        'Roquette aérienne à haute vitesse HVAR 5"': 820,
        "Réservoir de napalm 110 gal": 170,
        "Réservoir largable 165 gal": 180,
        "Réservoir largable 265 gal": 120,
        "AN-M57A1 250 lb": 260,
        "AN-M64A1 500 lb": 320,
        "AN-M65A1 1000 lb": 90,
        "AN-M88 220 lb à fragmentation": 180,
        "Bombe éclairante à parachute AN-M26A1": 28,
        "M26A2 500 lb à sous-munitions": 90,
    },

    "F-84E": {
        "M29A1 500 lb à sous-munitions": 90,
        'Roquette Tiny Tim 12"': 40,
        'Roquette aérienne à haute vitesse HVAR 5"': 900,
        "Réservoir de napalm 110 gal": 190,
        "Réservoir largable 230 gal": 220,
        "AN-M57A1 250 lb": 280,
        "AN-M64A1 500 lb": 360,
        "AN-M65A1 1000 lb": 100,
        "AN-M88 220 lb à fragmentation": 200,
        "Bombe éclairante à parachute AN-M26A1": 30,
        "M26A2 500 lb à sous-munitions": 100,
    },

    "F-86A-5": {
        "Réservoir de napalm 110 gal": 60,
        "Réservoir largable 120 gal": 160,
        "Réservoir largable 245 gal": 260,
        "AN-M64A1 500 lb": 140,
        "AN-M65A1 1000 lb": 40,
        "Bombe éclairante à parachute AN-M26A1": 18,
        "M26A2 500 lb à sous-munitions": 40,
        "M29A1 500 lb à sous-munitions": 35,
        'Roquette aérienne à haute vitesse HVAR 5"': 300,
    },

    "IL-10": {
        "M-13UK 132 mm": 300,
        "M-8 82 mm": 620,
        "PTAB-10-2.5": 420,
        "PTAB-2,5-1,5": 900,
        "SAB-100-55": 45,
        "AO-10sc": 520,
        "AO-2,5sc": 900,
        "AO-25sl": 360,
        "FAB-100sc": 300,
        "FAB-250 M43": 120,
        "FAB-50sc": 460,
    },

    "MiG-15bis": {
        "FAB-100sc": 80,
        "Réservoir largable 250 L": 240,
        "SAB-100-55": 18,
    },

    "Yak-9P": {},
    "La-11": {},
}


FACTEUR_STOCK_INITIAL_PAR_NIVEAU = {
    "TRÈS ÉLEVÉE": 1.15,
    "ÉLEVÉE": 1.00,
    "NORMALE": 0.78,
    "FAIBLE": 0.50,
    "TRÈS FAIBLE": 0.25,
    "INDISPONIBLE": 0.00,
}


def calculer_stock_initial_standard_carriere(
    avion: str,
    donnees_carriere: dict,
    *,
    extraire_annee_mois_carriere: Callable,
    lire_standard_mensuel_munition: Callable,
    niveau_standard_munition: Callable,
) -> dict[str, int]:
    """Construit le stock concret initial d'une carrière neuve."""
    compatibles = trier_munitions_logiquement(
        AVIONS_EMPORTS.get(
            avion,
            []
        )
    )

    if not compatibles:
        return {}

    annee, mois = extraire_annee_mois_carriere(
        donnees_carriere
    )

    profil = STOCK_INITIAL_STANDARD_PAR_AVION.get(
        avion,
        {}
    )

    resultat = {}

    for munition in compatibles:
        quantite_nominale = max(
            0,
            int(
                profil.get(
                    munition,
                    0
                )
            )
        )

        try:
            niveau = lire_standard_mensuel_munition(
                annee,
                mois,
                avion,
                munition
            )[
                "niveau"
            ]

        except Exception:
            niveau = niveau_standard_munition(
                munition
            )

        facteur = FACTEUR_STOCK_INITIAL_PAR_NIVEAU.get(
            niveau,
            0.78
        )

        resultat[
            munition
        ] = max(
            0,
            int(
                round(
                    quantite_nominale
                    * facteur
                )
            )
        )

    return resultat


# ============================================================
# MAINTENANCE DIRECTE DU STOCK LOCAL
# ============================================================

def remplacer_stock_local(
    fichier_base: Path,
    nouvelles_valeurs: dict[str, int],
) -> dict[str, int]:
    """Remplace entièrement le stock concret local.

    Toutes les munitions connues de la table sont d'abord remises à zéro,
    puis les quantités fournies sont appliquées dans une transaction courte.

    Cette fonction ne touche ni à ammoQty, ni à carriere_sync, ni aux
    rapports, directives, boosts ou livraisons.
    """
    fichier_base = Path(
        fichier_base
    )

    valeurs = {
        str(
            nom
        ): max(
            0,
            int(
                quantite
            )
        )
        for nom, quantite in nouvelles_valeurs.items()
    }

    connexion = sqlite3.connect(
        fichier_base,
        timeout=5.0
    )

    try:
        connexion.execute(
            "PRAGMA busy_timeout = 5000"
        )
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        curseur.execute(
            """
            UPDATE munitions
            SET stock = 0
            """
        )

        for nom, quantite in valeurs.items():
            curseur.execute(
                """
                UPDATE munitions
                SET stock = ?
                WHERE nom = ?
                """,
                (
                    quantite,
                    nom,
                )
            )

        connexion.commit()

        return dict(
            valeurs
        )

    except Exception:
        connexion.rollback()
        raise

    finally:
        connexion.close()


def definir_quantites_stock(
    fichier_base: Path,
    nouvelles_valeurs: dict[str, int],
) -> dict[str, int]:
    """Modifie uniquement les munitions explicitement fournies.

    Utilisé notamment par l'outil Admin. Les autres lignes de stock restent
    intactes. Aucune table hors ``munitions`` n'est modifiée.
    """
    fichier_base = Path(
        fichier_base
    )

    valeurs = {
        str(
            nom
        ): max(
            0,
            int(
                quantite
            )
        )
        for nom, quantite in nouvelles_valeurs.items()
    }

    if not valeurs:
        return {}

    connexion = sqlite3.connect(
        fichier_base,
        timeout=5.0
    )

    try:
        connexion.execute(
            "PRAGMA busy_timeout = 5000"
        )
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        for nom, quantite in valeurs.items():
            curseur.execute(
                """
                UPDATE munitions
                SET stock = ?
                WHERE nom = ?
                """,
                (
                    quantite,
                    nom,
                )
            )

        connexion.commit()

        return dict(
            valeurs
        )

    except Exception:
        connexion.rollback()
        raise

    finally:
        connexion.close()


# ============================================================
# SNAPSHOT CARRIÈRE
# ============================================================

def signature_snapshot_carriere(
    donnees_carriere: dict
) -> str:
    texte = (
        str(
            local_db.cle_sync_carriere(
                donnees_carriere
            )
        )
        + "|"
        + str(
            donnees_carriere.get(
                "avion",
                ""
            )
        )
        + "|"
        + str(
            donnees_carriere.get(
                "ammo_qty",
                0
            )
        )
    )

    return hashlib.sha256(
        texte.encode(
            "utf-8"
        )
    ).hexdigest()


def seed_snapshot_carriere(
    donnees_carriere: dict
) -> int:
    signature = signature_snapshot_carriere(
        donnees_carriere
    )

    return int(
        signature[
            :16
        ],
        16
    )


# ============================================================
# HELPERS DB
# ============================================================

def _stock_compatible(
    fichier_base: Path,
    avion: str
) -> dict[str, int]:
    return {
        nom: local_db.lire_stock_unitaire(
            fichier_base,
            nom
        )
        for nom in AVIONS_EMPORTS.get(
            avion,
            []
        )
    }


def _ecrire_snapshot(
    curseur,
    *,
    fichier: str,
    avion: str,
    ammo_qty: int,
    signature: str,
    avec_secondes: bool,
):
    format_date = (
        "%d.%m.%Y - %H:%M:%S"
        if avec_secondes
        else "%d.%m.%Y - %H:%M"
    )

    curseur.execute(
        """
        INSERT INTO carriere_sync (
            fichier,
            avion,
            ammo_qty,
            signature,
            date_sync
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(fichier)
        DO UPDATE SET
            avion = excluded.avion,
            ammo_qty = excluded.ammo_qty,
            signature = excluded.signature,
            date_sync = excluded.date_sync
        """,
        (
            fichier,
            avion,
            int(
                ammo_qty
            ),
            signature,
            datetime.now().strftime(
                format_date
            ),
        )
    )


def _appliquer_repartition_absolue(
    curseur,
    repartition: dict[str, int]
):
    curseur.execute(
        """
        UPDATE munitions
        SET stock = 0
        """
    )

    for nom, quantite in repartition.items():
        curseur.execute(
            """
            UPDATE munitions
            SET stock = ?
            WHERE nom = ?
            """,
            (
                max(
                    0,
                    int(
                        quantite
                    )
                ),
                nom,
            )
        )


def _appliquer_ajouts(
    curseur,
    ajouts: dict[str, int],
    *,
    verifier: bool
) -> dict:
    changements = {}

    for nom, quantite_brute in ajouts.items():
        quantite = int(
            quantite_brute
        )

        if quantite <= 0:
            continue

        ligne = curseur.execute(
            """
            SELECT
                id,
                stock
            FROM munitions
            WHERE nom = ?
            ORDER BY id
            LIMIT 1
            """,
            (
                nom,
            )
        ).fetchone()

        if ligne is None:
            curseur.execute(
                """
                INSERT INTO munitions (
                    nom,
                    stock
                )
                VALUES (?, ?)
                """,
                (
                    nom,
                    quantite,
                )
            )

            avant = 0
            apres = quantite

        else:
            identifiant = int(
                ligne[
                    0
                ]
            )

            avant = int(
                ligne[
                    1
                ]
            )

            apres = (
                avant
                + quantite
            )

            curseur.execute(
                """
                UPDATE munitions
                SET stock = ?
                WHERE id = ?
                """,
                (
                    apres,
                    identifiant,
                )
            )

        if verifier:
            ligne_verification = curseur.execute(
                """
                SELECT stock
                FROM munitions
                WHERE nom = ?
                ORDER BY id
                LIMIT 1
                """,
                (
                    nom,
                )
            ).fetchone()

            if (
                ligne_verification is None
                or int(
                    ligne_verification[
                        0
                    ]
                ) != apres
            ):
                raise RuntimeError(
                    "stock_verification_failed:"
                    + str(
                        nom
                    )
                )

            changements[
                nom
            ] = {
                "delta": quantite,
                "avant": avant,
                "apres": apres,
            }

        else:
            changements[
                nom
            ] = quantite

    return changements


# ============================================================
# SYNCHRONISATION AU DÉMARRAGE
# ============================================================

def synchroniser_stock_avec_carriere(
    fichier_base: Path,
    donnees_carriere: dict,
    *,
    calculer_stock_initial: Callable,
    calculer_repartition: Callable,
) -> dict:
    """Synchronisation incrémentale avec ammoQty.

    Les callbacks de calcul sont exécutés hors transaction d'écriture.
    """
    resultat_vide = {
        "recalcule": False,
        "type_changement": "aucun",
        "avion": None,
        "ancienne_valeur": None,
        "nouvelle_valeur": 0,
        "delta": 0,
        "changements": {},
        "stock": {},
    }

    if not donnees_carriere:
        return resultat_vide

    fichier_base = Path(
        fichier_base
    )

    fichier = local_db.cle_sync_carriere(
        donnees_carriere
    )

    avion = donnees_carriere.get(
        "avion"
    )

    ammo_qty = int(
        donnees_carriere.get(
            "ammo_qty",
            0
        )
    )

    if (
        avion is None
        or avion not in AVIONS_EMPORTS
    ):
        resultat_vide[
            "avion"
        ] = avion

        resultat_vide[
            "nouvelle_valeur"
        ] = ammo_qty

        return resultat_vide

    signature = signature_snapshot_carriere(
        donnees_carriere
    )

    # Prélecture sans verrou d'écriture.
    connexion = sqlite3.connect(
        fichier_base,
        timeout=5.0
    )

    try:
        connexion.execute(
            "PRAGMA busy_timeout = 5000"
        )

        ligne = connexion.execute(
            """
            SELECT
                avion,
                ammo_qty,
                signature
            FROM carriere_sync
            WHERE fichier = ?
            LIMIT 1
            """,
            (
                fichier,
            )
        ).fetchone()

    finally:
        connexion.close()

    # --------------------------------------------------------
    # PREMIÈRE SYNCHRONISATION
    # --------------------------------------------------------
    if ligne is None:
        repartition = calculer_stock_initial(
            avion,
            donnees_carriere
        )

        connexion = sqlite3.connect(
            fichier_base,
            timeout=5.0
        )

        try:
            connexion.execute(
                "PRAGMA busy_timeout = 5000"
            )
            connexion.execute(
                "BEGIN IMMEDIATE"
            )

            curseur = connexion.cursor()

            # Un autre passage a pu initialiser entre-temps.
            deja = curseur.execute(
                """
                SELECT 1
                FROM carriere_sync
                WHERE fichier = ?
                LIMIT 1
                """,
                (
                    fichier,
                )
            ).fetchone()

            if deja is not None:
                connexion.rollback()

                return synchroniser_stock_avec_carriere(
                    fichier_base,
                    donnees_carriere,
                    calculer_stock_initial=calculer_stock_initial,
                    calculer_repartition=calculer_repartition,
                )

            _appliquer_repartition_absolue(
                curseur,
                repartition
            )

            _ecrire_snapshot(
                curseur,
                fichier=fichier,
                avion=avion,
                ammo_qty=ammo_qty,
                signature=signature,
                avec_secondes=False,
            )

            connexion.commit()

        except Exception:
            connexion.rollback()
            raise

        finally:
            connexion.close()

        return {
            "recalcule": True,
            "type_changement": "initialisation",
            "avion": avion,
            "ancienne_valeur": None,
            "nouvelle_valeur": ammo_qty,
            "delta": ammo_qty,
            "changements": {
                nom: int(
                    quantite
                )
                for nom, quantite in repartition.items()
                if int(
                    quantite
                ) > 0
            },
            "stock": dict(
                repartition
            ),
        }

    ancien_avion = str(
        ligne[
            0
        ]
    )
    ancien_ammo = int(
        ligne[
            1
        ]
    )
    ancienne_signature = str(
        ligne[
            2
        ]
    )

    # --------------------------------------------------------
    # AUCUN CHANGEMENT
    # --------------------------------------------------------
    if (
        ancien_avion == avion
        and ancien_ammo == ammo_qty
        and ancienne_signature == signature
    ):
        return {
            "recalcule": False,
            "type_changement": "aucun",
            "avion": avion,
            "ancienne_valeur": ancien_ammo,
            "nouvelle_valeur": ammo_qty,
            "delta": 0,
            "changements": {},
            "stock": _stock_compatible(
                fichier_base,
                avion
            ),
        }

    # Calcul métier HORS transaction.
    repartition_absolue = None
    ajouts = None

    if ancien_avion != avion:
        repartition_absolue = calculer_repartition(
            avion,
            ammo_qty,
            donnees_carriere
        )

        type_changement = "appareil_change"
        delta = ammo_qty - ancien_ammo

    elif ammo_qty > ancien_ammo:
        delta = ammo_qty - ancien_ammo

        donnees_delta = dict(
            donnees_carriere
        )

        donnees_delta[
            "fichier"
        ] = (
            fichier
            + f"#delta:{ancien_ammo}->{ammo_qty}"
        )

        donnees_delta[
            "ammo_qty"
        ] = delta

        ajouts = calculer_repartition(
            avion,
            delta,
            donnees_delta
        )

        type_changement = "augmentation"

    else:
        # IMPORTANT :
        # une baisse ammoQty ne retire aucun stock concret.
        delta = ammo_qty - ancien_ammo
        type_changement = "diminution_reference"

    connexion = sqlite3.connect(
        fichier_base,
        timeout=5.0
    )

    try:
        connexion.execute(
            "PRAGMA busy_timeout = 5000"
        )
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        ligne_verrouillee = curseur.execute(
            """
            SELECT
                avion,
                ammo_qty,
                signature
            FROM carriere_sync
            WHERE fichier = ?
            LIMIT 1
            """,
            (
                fichier,
            )
        ).fetchone()

        # Si le snapshot a changé pendant le calcul, on repart proprement.
        if (
            ligne_verrouillee is None
            or str(
                ligne_verrouillee[
                    0
                ]
            ) != ancien_avion
            or int(
                ligne_verrouillee[
                    1
                ]
            ) != ancien_ammo
            or str(
                ligne_verrouillee[
                    2
                ]
            ) != ancienne_signature
        ):
            connexion.rollback()

            return synchroniser_stock_avec_carriere(
                fichier_base,
                donnees_carriere,
                calculer_stock_initial=calculer_stock_initial,
                calculer_repartition=calculer_repartition,
            )

        if repartition_absolue is not None:
            _appliquer_repartition_absolue(
                curseur,
                repartition_absolue
            )

            changements = {
                nom: int(
                    quantite
                )
                for nom, quantite in repartition_absolue.items()
                if int(
                    quantite
                ) > 0
            }

        elif ajouts is not None:
            changements = _appliquer_ajouts(
                curseur,
                ajouts,
                verifier=False
            )

        else:
            changements = {}

        _ecrire_snapshot(
            curseur,
            fichier=fichier,
            avion=avion,
            ammo_qty=ammo_qty,
            signature=signature,
            avec_secondes=False,
        )

        connexion.commit()

    except Exception:
        connexion.rollback()
        raise

    finally:
        connexion.close()

    return {
        "recalcule": True,
        "type_changement": type_changement,
        "avion": avion,
        "ancienne_valeur": ancien_ammo,
        "nouvelle_valeur": ammo_qty,
        "delta": delta,
        "changements": changements,
        "stock": _stock_compatible(
            fichier_base,
            avion
        ),
    }


# ============================================================
# DELTA À CHAUD
# ============================================================

def appliquer_delta_carriere_temps_reel(
    fichier_base: Path,
    donnees_carriere: dict,
    ancienne_valeur: int,
    nouvelle_valeur: int,
    *,
    calculer_repartition: Callable,
) -> dict:
    """Applique un changement ammoQty pendant l'exécution.

    Le calcul métier est toujours terminé avant BEGIN IMMEDIATE.
    """
    fichier_base = Path(
        fichier_base
    )

    avion = donnees_carriere.get(
        "avion"
    )

    fichier = local_db.cle_sync_carriere(
        donnees_carriere
    )

    ancienne_valeur_demandee = int(
        ancienne_valeur
    )

    nouvelle_valeur = int(
        nouvelle_valeur
    )

    resultat = {
        "recalcule": False,
        "type_changement": "aucun",
        "avion": avion,
        "ancienne_valeur": ancienne_valeur_demandee,
        "nouvelle_valeur": nouvelle_valeur,
        "delta": nouvelle_valeur - ancienne_valeur_demandee,
        "changements": {},
        "stock": {},
    }

    if (
        avion is None
        or avion not in AVIONS_EMPORTS
    ):
        return resultat

    for _tentative in range(
        2
    ):
        connexion_lecture = sqlite3.connect(
            fichier_base,
            timeout=5.0
        )

        try:
            connexion_lecture.execute(
                "PRAGMA busy_timeout = 5000"
            )

            ligne_sync = connexion_lecture.execute(
                """
                SELECT ammo_qty
                FROM carriere_sync
                WHERE fichier = ?
                LIMIT 1
                """,
                (
                    fichier,
                )
            ).fetchone()

        finally:
            connexion_lecture.close()

        ancienne_valeur_effective = (
            int(
                ligne_sync[
                    0
                ]
            )
            if ligne_sync is not None
            else ancienne_valeur_demandee
        )

        if ancienne_valeur_effective == nouvelle_valeur:
            resultat.update(
                {
                    "recalcule": False,
                    "type_changement": "deja_applique",
                    "ancienne_valeur": ancienne_valeur_effective,
                    "nouvelle_valeur": nouvelle_valeur,
                    "delta": 0,
                    "changements": {},
                    "stock": _stock_compatible(
                        fichier_base,
                        avion
                    ),
                }
            )

            return resultat

        delta = nouvelle_valeur - ancienne_valeur_effective

        resultat[
            "ancienne_valeur"
        ] = ancienne_valeur_effective

        resultat[
            "delta"
        ] = delta

        # Calcul complet HORS transaction d'écriture.
        ajouts = {}

        if delta > 0:
            donnees_delta = dict(
                donnees_carriere
            )

            donnees_delta[
                "fichier"
            ] = (
                fichier
                + f"#live:{ancienne_valeur_effective}->{nouvelle_valeur}"
            )

            donnees_delta[
                "ammo_qty"
            ] = delta

            ajouts = calculer_repartition(
                avion,
                delta,
                donnees_delta
            )

        connexion = sqlite3.connect(
            fichier_base,
            timeout=5.0
        )

        try:
            connexion.execute(
                "PRAGMA busy_timeout = 5000"
            )
            connexion.execute(
                "BEGIN IMMEDIATE"
            )

            curseur = connexion.cursor()

            ligne_verrouillee = curseur.execute(
                """
                SELECT ammo_qty
                FROM carriere_sync
                WHERE fichier = ?
                LIMIT 1
                """,
                (
                    fichier,
                )
            ).fetchone()

            reference_verrouillee = (
                int(
                    ligne_verrouillee[
                        0
                    ]
                )
                if ligne_verrouillee is not None
                else ancienne_valeur_demandee
            )

            if reference_verrouillee == nouvelle_valeur:
                connexion.commit()

                resultat.update(
                    {
                        "recalcule": False,
                        "type_changement": "deja_applique",
                        "ancienne_valeur": reference_verrouillee,
                        "nouvelle_valeur": nouvelle_valeur,
                        "delta": 0,
                        "changements": {},
                        "stock": _stock_compatible(
                            fichier_base,
                            avion
                        ),
                    }
                )

                return resultat

            if reference_verrouillee != ancienne_valeur_effective:
                connexion.rollback()
                continue

            if delta > 0:
                changements = _appliquer_ajouts(
                    curseur,
                    ajouts,
                    verifier=True
                )

                type_changement = "augmentation"

            else:
                # Une baisse ammoQty ne retire jamais de stock concret.
                changements = {}
                type_changement = "diminution_reference"

            _ecrire_snapshot(
                curseur,
                fichier=fichier,
                avion=avion,
                ammo_qty=nouvelle_valeur,
                signature=signature_snapshot_carriere(
                    donnees_carriere
                ),
                avec_secondes=True,
            )

            connexion.commit()

        except Exception:
            connexion.rollback()
            raise

        finally:
            connexion.close()

        resultat.update(
            {
                "recalcule": True,
                "type_changement": type_changement,
                "changements": changements,
                "stock": _stock_compatible(
                    fichier_base,
                    avion
                ),
            }
        )

        return resultat

    raise RuntimeError(
        "ammo_snapshot_changed_during_supply"
    )


# ============================================================
# CONSOMMATION DE MISSION
# ============================================================

class StockInsuffisantError(RuntimeError):
    """Erreur métier interne, sans texte d'interface."""

    def __init__(
        self,
        nom: str,
        demande: int,
        disponible: int
    ):
        super().__init__(
            "stock_insuffisant"
        )

        self.nom = str(
            nom
        )
        self.demande = int(
            demande
        )
        self.disponible = int(
            disponible
        )


def enregistrer_mission_et_consommer(
    fichier_base: Path,
    *,
    date_heure: str,
    avion: str,
    nombre_avions: int,
    demandes: Iterable[tuple[str, int]],
) -> dict:
    """Décrémente le stock concret et enregistre la mission atomiquement."""
    fichier_base = Path(
        fichier_base
    )

    demandes_normalisees = [
        (
            str(
                nom
            ),
            max(
                0,
                int(
                    total
                )
            )
        )
        for nom, total in demandes
        if int(
            total
        ) > 0
    ]

    if not demandes_normalisees:
        return {
            "armement": "",
            "stock_apres": {},
        }

    connexion = sqlite3.connect(
        fichier_base,
        timeout=5.0
    )

    try:
        connexion.execute(
            "PRAGMA busy_timeout = 5000"
        )
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        stocks_avant = {}

        for nom, total in demandes_normalisees:
            ligne = curseur.execute(
                """
                SELECT stock
                FROM munitions
                WHERE nom = ?
                ORDER BY id
                LIMIT 1
                """,
                (
                    nom,
                )
            ).fetchone()

            disponible = (
                int(
                    ligne[
                        0
                    ]
                )
                if ligne is not None
                else 0
            )

            if total > disponible:
                raise StockInsuffisantError(
                    nom,
                    total,
                    disponible
                )

            stocks_avant[
                nom
            ] = disponible

        stock_apres = {}

        for nom, total in demandes_normalisees:
            apres = stocks_avant[
                nom
            ] - total

            curseur.execute(
                """
                UPDATE munitions
                SET stock = ?
                WHERE nom = ?
                """,
                (
                    apres,
                    nom,
                )
            )

            stock_apres[
                nom
            ] = apres

        armement = " | ".join(
            f"{total}x {nom}"
            for nom, total in demandes_normalisees
        )

        curseur.execute(
            """
            INSERT INTO missions (
                date_heure,
                avion,
                nombre_avions,
                armement
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                str(
                    date_heure
                ),
                str(
                    avion
                ),
                int(
                    nombre_avions
                ),
                armement,
            )
        )

        connexion.commit()

        return {
            "armement": armement,
            "stock_apres": stock_apres,
        }

    except Exception:
        connexion.rollback()
        raise

    finally:
        connexion.close()
