"""Couche SQLite locale de IL-2 Korea Stock Manager.

Ce module ne connaît pas Tkinter et ne dépend d'aucune fenêtre.

Responsabilités :
- identité stable d'une carrière ;
- chemin de la DB locale par carrière ;
- migration douce de l'ancien stock.db ;
- création/migration du schéma SQLite local ;
- métadonnées de carrière ;
- accès simples : stock, missions, presets, paramètres logistiques.

IMPORTANT :
La base de carrière IL-2 n'est JAMAIS ouverte ici. Elle reste gérée en
lecture seule par career_reader.py.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
from pathlib import Path
from typing import Iterable

from app_data import (
    MUNITIONS,
    PARAMETRES_RAVITAILLEMENT_DEFAUT,
    PROFILS_SIMULATION,
    construire_modele_avance_defaut,
)


# ============================================================
# POINTS DE COMMANDEMENT
# ============================================================
#
# Les points sont stockés en DIXIÈMES pour gérer proprement les gains
# journaliers de 0,1 / 0,5 point sans dépendre des flottants SQLite.
#
# La clé historique "points_commandement" reste maintenue en parallèle
# pour compatibilité avec d'anciennes versions.
# ============================================================

ECHELLE_POINTS_COMMANDEMENT = 10
POINTS_COMMANDEMENT_DEPART_X10 = 10
GAIN_POINTS_JOURNALIER_DEFAUT_X10 = 10

# Version usine du système de commandement.
# La version 3 impose une seule fois le nouveau départ à 1 point
# même sur une carrière locale déjà existante.
VERSION_USINE_POINTS_COMMANDEMENT = 3
GAINS_POINTS_JOURNALIERS_AUTORISES_X10 = (
    1,
    5,
    10,
    20,
    30,
)


def _lire_etat_commandement_int(
    curseur,
    cle
):
    ligne = curseur.execute(
        """
        SELECT valeur
        FROM commandement_etat
        WHERE cle = ?
        LIMIT 1
        """,
        (
            str(
                cle
            ),
        )
    ).fetchone()

    if ligne is None:
        return None

    return int(
        ligne[
            0
        ]
    )


def _ecrire_etat_commandement_int(
    curseur,
    cle,
    valeur
):
    curseur.execute(
        """
        INSERT INTO commandement_etat (
            cle,
            valeur
        )
        VALUES (?, ?)
        ON CONFLICT(cle)
        DO UPDATE SET
            valeur = excluded.valeur
        """,
        (
            str(
                cle
            ),
            int(
                valeur
            )
        )
    )


def appliquer_usine_points_commandement_si_necessaire_transaction(
    curseur
):
    """
    Applique UNE SEULE FOIS les nouveaux paramètres d'usine du système
    de commandement à une carrière locale existante.

    Version usine 3 :
    - solde = 1 point ;
    - gain = +1 point/jour ;
    - date de référence journalière effacée pour repartir depuis la date
      courante au prochain passage.

    Une fois la version enregistrée, les futurs lancements ne réinitialisent
    plus le solde du joueur.
    """
    version_actuelle = _lire_etat_commandement_int(
        curseur,
        "version_usine_points_commandement"
    )

    if (
        version_actuelle is not None
        and int(
            version_actuelle
        ) >= VERSION_USINE_POINTS_COMMANDEMENT
    ):
        return False

    _ecrire_etat_commandement_int(
        curseur,
        "points_commandement_x10",
        POINTS_COMMANDEMENT_DEPART_X10
    )

    _ecrire_etat_commandement_int(
        curseur,
        "points_commandement",
        POINTS_COMMANDEMENT_DEPART_X10
        // ECHELLE_POINTS_COMMANDEMENT
    )

    _ecrire_etat_commandement_int(
        curseur,
        "gain_points_journalier_x10",
        GAIN_POINTS_JOURNALIER_DEFAUT_X10
    )

    curseur.execute(
        """
        DELETE FROM commandement_etat
        WHERE cle = 'derniere_date_gain_points'
        """
    )

    _ecrire_etat_commandement_int(
        curseur,
        "version_usine_points_commandement",
        VERSION_USINE_POINTS_COMMANDEMENT
    )

    return True


def assurer_etat_points_commandement_transaction(
    curseur
):
    """
    Assure l'état du système de points.

    Depuis la version usine 3, une carrière existante est recalée UNE FOIS
    à 1 point afin d'appliquer les nouveaux paramètres d'usine.
    """
    appliquer_usine_points_commandement_si_necessaire_transaction(
        curseur
    )

    points_x10 = _lire_etat_commandement_int(
        curseur,
        "points_commandement_x10"
    )

    if points_x10 is None:
        points_legacy = _lire_etat_commandement_int(
            curseur,
            "points_commandement"
        )

        if points_legacy is None:
            points_legacy = 1

        points_x10 = max(
            0,
            int(
                points_legacy
            )
            * ECHELLE_POINTS_COMMANDEMENT
        )

        _ecrire_etat_commandement_int(
            curseur,
            "points_commandement_x10",
            points_x10
        )

    gain_x10 = _lire_etat_commandement_int(
        curseur,
        "gain_points_journalier_x10"
    )

    if gain_x10 is None:
        gain_x10 = GAIN_POINTS_JOURNALIER_DEFAUT_X10

        _ecrire_etat_commandement_int(
            curseur,
            "gain_points_journalier_x10",
            gain_x10
        )

    return (
        max(
            0,
            int(
                points_x10
            )
        ),
        max(
            0,
            int(
                gain_x10
            )
        )
    )


def synchroniser_points_legacy_transaction(
    curseur,
    points_x10
):
    """
    Maintient la vieille clé entière pour permettre un retour arrière
    vers une ancienne version sans solde totalement incohérent.
    """
    points_entiers = max(
        0,
        int(
            points_x10
        )
        // ECHELLE_POINTS_COMMANDEMENT
    )

    _ecrire_etat_commandement_int(
        curseur,
        "points_commandement",
        points_entiers
    )


def lire_points_commandement_x10(
    fichier_base: Path
) -> int:
    connexion = sqlite3.connect(
        Path(
            fichier_base
        )
    )

    try:
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        points_x10, _ = assurer_etat_points_commandement_transaction(
            curseur
        )

        synchroniser_points_legacy_transaction(
            curseur,
            points_x10
        )

        connexion.commit()

        return points_x10

    except Exception:
        connexion.rollback()
        raise

    finally:
        connexion.close()


def lire_gain_points_journalier_x10(
    fichier_base: Path
) -> int:
    connexion = sqlite3.connect(
        Path(
            fichier_base
        )
    )

    try:
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        _, gain_x10 = assurer_etat_points_commandement_transaction(
            curseur
        )

        connexion.commit()

        return gain_x10

    except Exception:
        connexion.rollback()
        raise

    finally:
        connexion.close()


def actualiser_points_commandement_journaliers(
    fichier_base: Path,
    date_ordinal: int
) -> dict:
    """
    Crédite les jours de campagne écoulés.

    - premier passage : initialise la date de référence, sans rétroactivité ;
    - date avancée : crédite chaque jour écoulé ;
    - retour à une sauvegarde plus ancienne : recale la référence sans débit.

    Tout est fait avec des entiers en dixièmes de point.
    """
    date_ordinal = int(
        date_ordinal
    )

    connexion = sqlite3.connect(
        Path(
            fichier_base
        ),
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

        (
            points_x10,
            gain_x10
        ) = assurer_etat_points_commandement_transaction(
            curseur
        )

        derniere_date = _lire_etat_commandement_int(
            curseur,
            "derniere_date_gain_points"
        )

        jours_ajoutes = 0
        ajout_x10 = 0

        if derniere_date is None:
            _ecrire_etat_commandement_int(
                curseur,
                "derniere_date_gain_points",
                date_ordinal
            )

        elif date_ordinal > derniere_date:
            jours_ajoutes = (
                date_ordinal
                - derniere_date
            )

            ajout_x10 = (
                jours_ajoutes
                * gain_x10
            )

            points_x10 += ajout_x10

            _ecrire_etat_commandement_int(
                curseur,
                "points_commandement_x10",
                points_x10
            )

            _ecrire_etat_commandement_int(
                curseur,
                "derniere_date_gain_points",
                date_ordinal
            )

        elif date_ordinal < derniere_date:
            # Chargement d'une sauvegarde plus ancienne :
            # jamais de retrait de points.
            _ecrire_etat_commandement_int(
                curseur,
                "derniere_date_gain_points",
                date_ordinal
            )

        synchroniser_points_legacy_transaction(
            curseur,
            points_x10
        )

        connexion.commit()

        return {
            "points_x10": int(
                points_x10
            ),
            "gain_x10": int(
                gain_x10
            ),
            "jours_ajoutes": int(
                jours_ajoutes
            ),
            "ajout_x10": int(
                ajout_x10
            ),
            "date_ordinal": int(
                date_ordinal
            )
        }

    except Exception:
        connexion.rollback()
        raise

    finally:
        connexion.close()


def definir_gain_points_journalier_x10(
    fichier_base: Path,
    gain_x10: int
) -> int:
    gain_x10 = int(
        gain_x10
    )

    if gain_x10 not in GAINS_POINTS_JOURNALIERS_AUTORISES_X10:
        raise ValueError(
            "Gain journalier non autorisé."
        )

    connexion = sqlite3.connect(
        Path(
            fichier_base
        ),
        timeout=5.0
    )

    try:
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        assurer_etat_points_commandement_transaction(
            curseur
        )

        _ecrire_etat_commandement_int(
            curseur,
            "gain_points_journalier_x10",
            gain_x10
        )

        connexion.commit()

        return gain_x10

    except Exception:
        connexion.rollback()
        raise

    finally:
        connexion.close()


def definir_points_commandement_x10(
    fichier_base: Path,
    points_x10: int
) -> int:
    points_x10 = max(
        0,
        int(
            points_x10
        )
    )

    connexion = sqlite3.connect(
        Path(
            fichier_base
        ),
        timeout=5.0
    )

    try:
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        assurer_etat_points_commandement_transaction(
            curseur
        )

        _ecrire_etat_commandement_int(
            curseur,
            "points_commandement_x10",
            points_x10
        )

        synchroniser_points_legacy_transaction(
            curseur,
            points_x10
        )

        connexion.commit()

        return points_x10

    except Exception:
        connexion.rollback()
        raise

    finally:
        connexion.close()


def debiter_points_commandement_transaction(
    curseur,
    cout_points,
    gratuit=False
):
    """
    Débit à utiliser DANS une transaction déjà ouverte.
    """
    (
        points_x10,
        _
    ) = assurer_etat_points_commandement_transaction(
        curseur
    )

    if gratuit:
        return (
            True,
            None
        )

    cout_x10 = max(
        0,
        int(
            round(
                float(
                    cout_points
                )
                * ECHELLE_POINTS_COMMANDEMENT
            )
        )
    )

    if points_x10 < cout_x10:
        return (
            False,
            points_x10
            / ECHELLE_POINTS_COMMANDEMENT
        )

    points_x10 -= cout_x10

    _ecrire_etat_commandement_int(
        curseur,
        "points_commandement_x10",
        points_x10
    )

    synchroniser_points_legacy_transaction(
        curseur,
        points_x10
    )

    return (
        True,
        points_x10
        / ECHELLE_POINTS_COMMANDEMENT
    )


# État usine : aucune munition concrète codée en dur.
STOCKS_INITIAUX = {
    nom: 0
    for nom in MUNITIONS
}


def obtenir_identifiant_carriere(donnees_carriere: dict) -> str:
    """Retourne l'identité stable de la carrière.

    Priorité :
    1. career.cuid ;
    2. career.personageId ;
    3. hash SHA-256 du chemin absolu.
    """
    cuid = str(
        donnees_carriere.get(
            "career_cuid",
            ""
        )
        or ""
    ).strip()

    if cuid:
        return cuid

    personage = str(
        donnees_carriere.get(
            "career_personage_id",
            ""
        )
        or ""
    ).strip()

    if personage:
        return personage

    chemin = str(
        Path(
            donnees_carriere.get(
                "fichier",
                ""
            )
        ).resolve()
    )

    return hashlib.sha256(
        chemin.encode(
            "utf-8"
        )
    ).hexdigest()


def nom_fichier_carriere_locale(
    identifiant_carriere: str
) -> str:
    """Transforme un identifiant de carrière en nom de fichier sûr."""
    propre = re.sub(
        r"[^A-Za-z0-9_-]",
        "_",
        str(
            identifiant_carriere
        )
    ).strip(
        "_"
    )

    if not propre:
        propre = hashlib.sha256(
            str(
                identifiant_carriere
            ).encode(
                "utf-8"
            )
        ).hexdigest()

    return propre


def cle_sync_carriere(
    donnees_carriere: dict
) -> str:
    """Clé stable utilisée dans carriere_sync/capacite_carriere."""
    return obtenir_identifiant_carriere(
        donnees_carriere
    )


def chemin_base_locale_carriere(
    donnees_carriere: dict,
    dossier_carrieres: Path
) -> Path:
    """Calcule le chemin de la DB locale dédiée à la carrière."""
    identifiant = obtenir_identifiant_carriere(
        donnees_carriere
    )

    nom_local = nom_fichier_carriere_locale(
        identifiant
    )

    return (
        Path(
            dossier_carrieres
        )
        / f"{nom_local}.db"
    )


def base_locale_carriere_existe(
    donnees_carriere: dict,
    dossier_carrieres: Path
) -> bool:
    """True si la carrière possède déjà une DB locale."""
    return chemin_base_locale_carriere(
        donnees_carriere,
        dossier_carrieres
    ).exists()


def configurer_base_locale_carriere(
    donnees_carriere: dict,
    dossier_carrieres: Path,
    fichier_base_heritage: Path,
    ancien_chemin_config: str = ""
) -> tuple[Path, bool]:
    """Choisit la DB locale et effectue la migration legacy si nécessaire.

    Retour :
        (chemin_db_locale, migration_effectuee)
    """
    dossier_carrieres = Path(
        dossier_carrieres
    )

    dossier_carrieres.mkdir(
        parents=True,
        exist_ok=True
    )

    destination = chemin_base_locale_carriere(
        donnees_carriere,
        dossier_carrieres
    )

    chemin_actuel = str(
        Path(
            donnees_carriere.get(
                "fichier",
                ""
            )
        ).resolve()
    )

    ancien_chemin = str(
        ancien_chemin_config
        or ""
    )

    fichier_base_heritage = Path(
        fichier_base_heritage
    )

    migration_effectuee = False

    if (
        not destination.exists()
        and fichier_base_heritage.exists()
        and ancien_chemin
    ):
        try:
            meme_carriere = (
                Path(
                    ancien_chemin
                ).resolve()
                == Path(
                    chemin_actuel
                ).resolve()
            )
        except Exception:
            meme_carriere = False

        if meme_carriere:
            shutil.copy2(
                fichier_base_heritage,
                destination
            )

            migration_effectuee = True

    return (
        destination,
        migration_effectuee
    )


def normaliser_cles_base_migree(
    fichier_base: Path,
    donnees_carriere: dict
) -> None:
    """Convertit les anciennes clés chemin vers l'identifiant stable."""
    fichier_base = Path(
        fichier_base
    )

    if not fichier_base.exists():
        return

    cle = cle_sync_carriere(
        donnees_carriere
    )

    ancien_chemin = str(
        Path(
            donnees_carriere.get(
                "fichier",
                ""
            )
        ).resolve()
    )

    with sqlite3.connect(
        fichier_base
    ) as connexion:
        curseur = connexion.cursor()

        curseur.execute(
            """
            DELETE FROM carriere_sync
            WHERE fichier != ?
            """,
            (
                ancien_chemin,
            )
        )

        curseur.execute(
            """
            UPDATE carriere_sync
            SET fichier = ?
            WHERE fichier = ?
            """,
            (
                cle,
                ancien_chemin
            )
        )

        curseur.execute(
            """
            DELETE FROM capacite_carriere
            WHERE fichier != ?
            """,
            (
                ancien_chemin,
            )
        )

        curseur.execute(
            """
            UPDATE capacite_carriere
            SET fichier = ?
            WHERE fichier = ?
            """,
            (
                cle,
                ancien_chemin
            )
        )


def enregistrer_meta_carriere_locale(
    fichier_base: Path,
    donnees_carriere: dict
) -> None:
    """Enregistre les métadonnées lisibles de la carrière locale."""
    with sqlite3.connect(
        Path(
            fichier_base
        )
    ) as connexion:
        curseur = connexion.cursor()

        curseur.execute(
            """
            CREATE TABLE IF NOT EXISTS carriere_locale_meta (
                cle TEXT PRIMARY KEY,
                valeur TEXT NOT NULL
            )
            """
        )

        valeurs = {
            "career_id": obtenir_identifiant_carriere(
                donnees_carriere
            ),
            "source_db": str(
                donnees_carriere.get(
                    "fichier",
                    ""
                )
            ),
            "avion_derniere_lecture": str(
                donnees_carriere.get(
                    "avion",
                    ""
                )
            )
        }

        for cle, valeur in valeurs.items():
            curseur.execute(
                """
                INSERT INTO carriere_locale_meta (
                    cle,
                    valeur
                )
                VALUES (?, ?)
                ON CONFLICT(cle)
                DO UPDATE SET
                    valeur = excluded.valeur
                """,
                (
                    cle,
                    valeur
                )
            )


def initialiser_base(
    fichier_base: Path
) -> None:
    """Crée/migre le schéma de la DB locale sans écraser les données."""
    fichier_base = Path(
        fichier_base
    )

    fichier_base.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with sqlite3.connect(
        fichier_base
    ) as connexion:
        curseur = connexion.cursor()

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS munitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                stock INTEGER NOT NULL
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS missions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_heure TEXT NOT NULL,
                avion TEXT NOT NULL,
                nombre_avions INTEGER NOT NULL,
                armement TEXT NOT NULL
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                avion TEXT NOT NULL,
                contenu TEXT NOT NULL,
                UNIQUE(nom, avion)
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS ravitaillement_parametres (
                cle TEXT PRIMARY KEY,
                valeur REAL NOT NULL
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS ravitaillements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_heure TEXT NOT NULL,
                avion TEXT NOT NULL,
                budget_prevu REAL NOT NULL,
                budget_reel REAL NOT NULL,
                modificateur REAL NOT NULL,
                details TEXT NOT NULL
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS modeles_simulation (
                profil TEXT PRIMARY KEY,
                donnees TEXT NOT NULL
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS carriere_sync (
                fichier TEXT PRIMARY KEY,
                avion TEXT NOT NULL,
                ammo_qty INTEGER NOT NULL,
                signature TEXT NOT NULL,
                date_sync TEXT NOT NULL
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS rapports_carriere (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_jeu TEXT NOT NULL,
                date_locale TEXT NOT NULL,
                type_changement TEXT NOT NULL,
                ancienne_valeur INTEGER,
                nouvelle_valeur INTEGER NOT NULL,
                delta INTEGER NOT NULL,
                details TEXT NOT NULL,
                valide INTEGER NOT NULL DEFAULT 0
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS capacite_carriere (
                fichier TEXT PRIMARY KEY,
                reference_max INTEGER NOT NULL
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS preferences_repartition (
                cle TEXT PRIMARY KEY,
                valeur TEXT NOT NULL
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS commandement_etat (
                cle TEXT PRIMARY KEY,
                valeur INTEGER NOT NULL
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS livraisons_urgentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_demande_jeu TEXT NOT NULL,
                date_arrivee_jeu TEXT NOT NULL,
                avion TEXT NOT NULL,
                munition TEXT NOT NULL,
                taille TEXT NOT NULL,
                quantite_min INTEGER NOT NULL,
                quantite_max INTEGER NOT NULL,
                quantite_reelle INTEGER NOT NULL,
                cout INTEGER NOT NULL,
                statut TEXT NOT NULL DEFAULT 'EN_TRANSIT',
                date_reception_locale TEXT NOT NULL DEFAULT ''
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS boosts_commandement (
                annee INTEGER NOT NULL,
                mois INTEGER NOT NULL,
                avion TEXT NOT NULL,
                munition TEXT NOT NULL,
                boost_pourcent REAL NOT NULL,
                cout_total INTEGER NOT NULL,
                date_demande TEXT NOT NULL,
                PRIMARY KEY (
                    annee,
                    mois,
                    avion,
                    munition
                )
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS directives_standard_commandement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                avion TEXT NOT NULL,
                annee_effet INTEGER NOT NULL,
                mois_effet INTEGER NOT NULL,
                mode TEXT NOT NULL,
                cout INTEGER NOT NULL DEFAULT 0,
                date_creation TEXT NOT NULL
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS directives_standard_priorites (
                directive_id INTEGER NOT NULL,
                munition TEXT NOT NULL,
                niveau TEXT NOT NULL,
                PRIMARY KEY (
                    directive_id,
                    munition
                )
            )
        """)

        curseur.execute(
            """
            INSERT OR IGNORE INTO commandement_etat (
                cle,
                valeur
            )
            VALUES (
                'points_commandement',
                1
            )
            """
        )

        curseur.execute(
            """
            INSERT OR IGNORE INTO commandement_etat (
                cle,
                valeur
            )
            VALUES (
                'mode_developpeur',
                0
            )
            """
        )

        curseur.execute(
            """
            INSERT OR IGNORE INTO commandement_etat (
                cle,
                valeur
            )
            VALUES (
                'gain_points_journalier_x10',
                10
            )
            """
        )

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS priorites_repartition_mensuelles (
                annee INTEGER NOT NULL,
                mois INTEGER NOT NULL,
                munition TEXT NOT NULL,
                priorite REAL NOT NULL DEFAULT 100.0,
                PRIMARY KEY (
                    annee,
                    mois,
                    munition
                )
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS niveaux_repartition (
                modele TEXT NOT NULL,
                niveau TEXT NOT NULL,
                quantite_reference REAL NOT NULL,
                PRIMARY KEY (
                    modele,
                    niveau
                )
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS niveaux_repartition_periodes (
                modele TEXT NOT NULL,
                annee INTEGER NOT NULL,
                mois INTEGER NOT NULL,
                niveau TEXT NOT NULL,
                quantite_reference REAL NOT NULL,
                PRIMARY KEY (
                    modele,
                    annee,
                    mois,
                    niveau
                )
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS affectations_repartition (
                modele TEXT NOT NULL,
                annee INTEGER NOT NULL,
                mois INTEGER NOT NULL,
                avion TEXT NOT NULL,
                munition TEXT NOT NULL,
                niveau TEXT NOT NULL,
                PRIMARY KEY (
                    modele,
                    annee,
                    mois,
                    avion,
                    munition
                )
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS profils_repartition (
                modele TEXT PRIMARY KEY,
                nom TEXT NOT NULL,
                date_creation TEXT NOT NULL
            )
        """)

        curseur.execute("""
            CREATE TABLE IF NOT EXISTS standard_repartition_mensuelle (
                annee INTEGER NOT NULL,
                mois INTEGER NOT NULL,
                avion TEXT NOT NULL,
                munition TEXT NOT NULL,
                niveau TEXT NOT NULL,
                quantite_reference REAL NOT NULL,
                statut_historique TEXT NOT NULL DEFAULT 'PROVISOIRE',
                source TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (
                    annee,
                    mois,
                    avion,
                    munition
                )
            )
        """)

        for cle_profil in PROFILS_SIMULATION:
            curseur.execute(
                """
                INSERT OR IGNORE INTO modeles_simulation (
                    profil,
                    donnees
                )
                VALUES (?, ?)
                """,
                (
                    cle_profil,
                    json.dumps(
                        construire_modele_avance_defaut(
                            cle_profil
                        ),
                        ensure_ascii=False
                    )
                )
            )

        for cle, valeur in PARAMETRES_RAVITAILLEMENT_DEFAUT.items():
            curseur.execute(
                """
                INSERT OR IGNORE INTO ravitaillement_parametres (
                    cle,
                    valeur
                )
                VALUES (?, ?)
                """,
                (
                    cle,
                    float(
                        valeur
                    )
                )
            )

        # Migration douce depuis les anciens noms de la v0.8.2.
        curseur.execute(
            "SELECT stock FROM munitions WHERE nom = ? ORDER BY id LIMIT 1",
            (
                "HVAR",
            )
        )
        ancien_hvar = curseur.fetchone()

        curseur.execute(
            "SELECT stock FROM munitions WHERE nom = ? ORDER BY id LIMIT 1",
            (
                "Réservoir 110 gal",
            )
        )
        ancien_reservoir = curseur.fetchone()

        # Ajoute les nouvelles munitions sans écraser ce qui existe déjà.
        for nom, stock_initial in STOCKS_INITIAUX.items():
            curseur.execute(
                "SELECT id FROM munitions WHERE nom = ? LIMIT 1",
                (
                    nom,
                )
            )

            if curseur.fetchone() is None:
                stock = stock_initial

                if (
                    nom == "Roquette aérienne à haute vitesse HVAR 5\""
                    and ancien_hvar is not None
                ):
                    stock = ancien_hvar[
                        0
                    ]

                if (
                    nom == "Réservoir largable 110 gal"
                    and ancien_reservoir is not None
                ):
                    stock = ancien_reservoir[
                        0
                    ]

                curseur.execute(
                    "INSERT INTO munitions (nom, stock) VALUES (?, ?)",
                    (
                        nom,
                        stock
                    )
                )


def appliquer_valeurs_usine_nouvelle_carriere(
    fichier_base: Path,
    version_application: str
) -> None:
    """Initialise l'état usine d'une carrière locale neuve."""
    connexion = sqlite3.connect(
        Path(
            fichier_base
        )
    )

    try:
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        curseur.execute(
            """
            INSERT INTO commandement_etat (
                cle,
                valeur
            )
            VALUES (
                'points_commandement',
                1
            )
            ON CONFLICT(cle)
            DO UPDATE SET
                valeur = excluded.valeur
            """
        )

        curseur.execute(
            """
            INSERT INTO commandement_etat (
                cle,
                valeur
            )
            VALUES (
                'mode_developpeur',
                0
            )
            ON CONFLICT(cle)
            DO UPDATE SET
                valeur = excluded.valeur
            """
        )

        curseur.execute(
            """
            INSERT INTO commandement_etat (
                cle,
                valeur
            )
            VALUES (
                'points_commandement_x10',
                10
            )
            ON CONFLICT(cle)
            DO UPDATE SET
                valeur = excluded.valeur
            """
        )

        curseur.execute(
            """
            INSERT INTO commandement_etat (
                cle,
                valeur
            )
            VALUES (
                'gain_points_journalier_x10',
                10
            )
            ON CONFLICT(cle)
            DO UPDATE SET
                valeur = excluded.valeur
            """
        )

        curseur.execute(
            """
            DELETE FROM commandement_etat
            WHERE cle = 'derniere_date_gain_points'
            """
        )

        curseur.execute(
            """
            INSERT INTO commandement_etat (
                cle,
                valeur
            )
            VALUES (
                'version_usine_points_commandement',
                ?
            )
            ON CONFLICT(cle)
            DO UPDATE SET
                valeur = excluded.valeur
            """,
            (
                VERSION_USINE_POINTS_COMMANDEMENT,
            )
        )

        curseur.execute(
            """
            INSERT INTO preferences_repartition (
                cle,
                valeur
            )
            VALUES (
                'modele_repartition_actif',
                'STANDARD'
            )
            ON CONFLICT(cle)
            DO UPDATE SET
                valeur = excluded.valeur
            """
        )

        for table in (
            "boosts_commandement",
            "livraisons_urgentes",
            "directives_standard_priorites",
            "directives_standard_commandement",
            "rapports_carriere",
            "missions",
            "ravitaillements"
        ):
            curseur.execute(
                f"DELETE FROM {table}"
            )

        curseur.execute(
            """
            UPDATE munitions
            SET stock = 0
            """
        )

        curseur.execute(
            """
            CREATE TABLE IF NOT EXISTS carriere_locale_meta (
                cle TEXT PRIMARY KEY,
                valeur TEXT NOT NULL
            )
            """
        )

        valeurs_meta = {
            "schema_version": "1",
            "defaults_version": "2",
            "initialisation_produit": "1",
            "version_application_initiale": version_application
        }

        for cle, valeur in valeurs_meta.items():
            curseur.execute(
                """
                INSERT INTO carriere_locale_meta (
                    cle,
                    valeur
                )
                VALUES (?, ?)
                ON CONFLICT(cle)
                DO UPDATE SET
                    valeur = excluded.valeur
                """,
                (
                    cle,
                    str(
                        valeur
                    )
                )
            )

        connexion.commit()

    except Exception:
        connexion.rollback()
        raise

    finally:
        connexion.close()


def lire_stock(
    fichier_base: Path,
    noms: Iterable[str] | None = None
) -> list[tuple[str, int]]:
    """Lit tout le stock ou un sous-ensemble ordonné."""
    with sqlite3.connect(
        Path(
            fichier_base
        )
    ) as connexion:
        curseur = connexion.cursor()

        if noms is None:
            curseur.execute("""
                SELECT nom, stock
                FROM munitions
                ORDER BY id
            """)

            return [
                (
                    str(
                        nom
                    ),
                    int(
                        stock
                    )
                )
                for nom, stock in curseur.fetchall()
            ]

        resultat = []

        for nom in noms:
            curseur.execute(
                "SELECT stock FROM munitions WHERE nom = ? ORDER BY id LIMIT 1",
                (
                    nom,
                )
            )

            ligne = curseur.fetchone()

            resultat.append(
                (
                    nom,
                    int(
                        ligne[
                            0
                        ]
                    )
                    if ligne
                    else 0
                )
            )

        return resultat


def lire_stock_unitaire(
    fichier_base: Path,
    nom: str
) -> int:
    """Lit une quantité de stock, 0 si la munition n'existe pas."""
    with sqlite3.connect(
        Path(
            fichier_base
        )
    ) as connexion:
        ligne = connexion.execute(
            "SELECT stock FROM munitions WHERE nom = ? ORDER BY id LIMIT 1",
            (
                nom,
            )
        ).fetchone()

    return (
        int(
            ligne[
                0
            ]
        )
        if ligne
        else 0
    )


def charger_missions(
    fichier_base: Path
) -> list[tuple]:
    """Retourne l'historique local des missions, plus récentes d'abord."""
    with sqlite3.connect(
        Path(
            fichier_base
        )
    ) as connexion:
        return connexion.execute("""
            SELECT
                id,
                date_heure,
                avion,
                nombre_avions,
                armement
            FROM missions
            ORDER BY id DESC
        """).fetchall()


def charger_noms_presets(
    fichier_base: Path,
    avion: str
) -> list[str]:
    """Liste les presets d'emport d'un appareil."""
    with sqlite3.connect(
        Path(
            fichier_base
        )
    ) as connexion:
        lignes = connexion.execute(
            """
            SELECT nom
            FROM presets
            WHERE avion = ?
            ORDER BY nom COLLATE NOCASE
            """,
            (
                avion,
            )
        ).fetchall()

    return [
        str(
            ligne[
                0
            ]
        )
        for ligne in lignes
    ]


def charger_preset(
    fichier_base: Path,
    avion: str,
    nom: str
) -> dict | None:
    """Charge le contenu JSON d'un preset d'emport."""
    with sqlite3.connect(
        Path(
            fichier_base
        )
    ) as connexion:
        ligne = connexion.execute(
            """
            SELECT contenu
            FROM presets
            WHERE avion = ? AND nom = ?
            LIMIT 1
            """,
            (
                avion,
                nom
            )
        ).fetchone()

    if ligne is None:
        return None

    try:
        contenu = json.loads(
            ligne[
                0
            ]
        )

        if not isinstance(
            contenu,
            dict
        ):
            return None

        return contenu

    except Exception:
        return None


def enregistrer_preset(
    fichier_base: Path,
    avion: str,
    nom: str,
    contenu: dict
) -> None:
    """Crée ou remplace un preset d'emport."""
    texte_json = json.dumps(
        contenu,
        ensure_ascii=False
    )

    with sqlite3.connect(
        Path(
            fichier_base
        )
    ) as connexion:
        connexion.execute(
            """
            INSERT INTO presets (
                nom,
                avion,
                contenu
            )
            VALUES (?, ?, ?)
            ON CONFLICT(nom, avion)
            DO UPDATE SET contenu = excluded.contenu
            """,
            (
                nom,
                avion,
                texte_json
            )
        )


def supprimer_preset_bdd(
    fichier_base: Path,
    avion: str,
    nom: str
) -> None:
    """Supprime un preset d'emport de la DB locale."""
    with sqlite3.connect(
        Path(
            fichier_base
        )
    ) as connexion:
        connexion.execute(
            """
            DELETE FROM presets
            WHERE avion = ? AND nom = ?
            """,
            (
                avion,
                nom
            )
        )


def lire_parametres_ravitaillement(
    fichier_base: Path
) -> dict[str, float]:
    """Lit les paramètres logistiques en complétant avec les defaults."""
    resultat = PARAMETRES_RAVITAILLEMENT_DEFAUT.copy()

    with sqlite3.connect(
        Path(
            fichier_base
        )
    ) as connexion:
        lignes = connexion.execute(
            """
            SELECT cle, valeur
            FROM ravitaillement_parametres
            """
        ).fetchall()

    for cle, valeur in lignes:
        if cle in resultat:
            resultat[
                cle
            ] = float(
                valeur
            )

    return resultat


def enregistrer_parametres_ravitaillement(
    fichier_base: Path,
    parametres: dict
) -> None:
    """Enregistre uniquement les clés logistiques reconnues."""
    with sqlite3.connect(
        Path(
            fichier_base
        )
    ) as connexion:
        curseur = connexion.cursor()

        for cle, valeur in parametres.items():
            if cle not in PARAMETRES_RAVITAILLEMENT_DEFAUT:
                continue

            curseur.execute(
                """
                INSERT INTO ravitaillement_parametres (
                    cle,
                    valeur
                )
                VALUES (?, ?)
                ON CONFLICT(cle)
                DO UPDATE SET valeur = excluded.valeur
                """,
                (
                    cle,
                    float(
                        valeur
                    )
                )
            )
