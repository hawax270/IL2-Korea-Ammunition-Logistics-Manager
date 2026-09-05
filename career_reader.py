"""Lecture strictement read-only des bases de carrière IL-2 Korea.

Aucune fonction de ce module n'écrit dans la base du jeu.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
import re

from app_data import MAPPING_CONFIG_AVIONS_IL2

def identifier_avion_depuis_config_il2(chemin_config):
    """
    Exemple :
    luascripts/worldobjects/planes/f51d.txt -> F-51D
    """
    texte = str(
        chemin_config or ""
    ).replace(
        "\\",
        "/"
    ).lower()

    nom = Path(
        texte
    ).stem

    identifiant = re.sub(
        r"[^a-z0-9]",
        "",
        nom
    )

    # Recherche exacte d'abord.
    if identifiant in MAPPING_CONFIG_AVIONS_IL2:
        return MAPPING_CONFIG_AVIONS_IL2[
            identifiant
        ]

    # Puis recherche tolérante.
    for cle, avion in MAPPING_CONFIG_AVIONS_IL2.items():
        if cle in identifiant:
            return avion

    return None

def extraire_nom_escadrille_depuis_fichier(chemin):
    """
    Extrait le nom de l'escadrille depuis le nom du fichier de carrière.

    Format généralement observé :
        Nom du pilote, 12e FBS USAF.db

    Les suffixes de duplication Windows du type ``(2)`` sont retirés :
        Nom du pilote, 12e FBS USAF(2).db -> 12e FBS USAF

    Si le nom du fichier ne contient pas de virgule exploitable, la fonction
    retourne une chaîne vide afin que l'interface utilise son fallback.
    """
    try:
        nom = Path(chemin).stem.strip()
    except Exception:
        return ""

    if "," not in nom:
        return ""

    # On prend ce qui suit la DERNIÈRE virgule : c'est plus tolérant si
    # le nom du pilote contient lui-même une virgule ou une annotation.
    escadrille = nom.rsplit(",", 1)[1].strip()

    # Nettoyage des suffixes de duplication Windows : (2), (3), etc.
    escadrille = re.sub(
        r"\s*\(\d+\)\s*$",
        "",
        escadrille
    ).strip()

    return escadrille


def connexion_sqlite_lecture_seule(chemin):
    """
    Ouvre la base SQLite via URI en mode read-only.
    Impossible d'écrire dans le fichier du jeu via cette connexion.
    """
    chemin_absolu = Path(
        chemin
    ).resolve()

    uri = (
        chemin_absolu.as_uri()
        + "?mode=ro"
    )

    connexion = sqlite3.connect(
        uri,
        uri=True,
        timeout=0.75
    )

    try:
        connexion.execute(
            "PRAGMA query_only = ON"
        )
        connexion.execute(
            "PRAGMA busy_timeout = 750"
        )
    except sqlite3.Error:
        pass

    return connexion

def lire_date_carriere_il2(
    chemin
):
    """
    Relit directement la DATE DE CAMPAGNE actuelle dans la base IL-2.

    Règle importante :
    - career.currentDate = source de vérité pour année / mois / jour ;
    - career.currentTime ne doit jamais remplacer currentDate lorsqu'elle
      existe. Il n'est utilisé qu'en secours.

    La base IL-2 reste strictement ouverte en lecture seule.
    """
    chemin = Path(
        chemin
    )

    if not chemin.exists():
        return ""

    connexion = None

    try:
        connexion = connexion_sqlite_lecture_seule(
            chemin
        )

        curseur = connexion.cursor()

        ligne = curseur.execute(
            """
            SELECT
                currentDate,
                currentTime
            FROM career
            WHERE isDeleted = 0
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

        if ligne is None:
            return ""

        current_date = str(
            ligne[0]
            or ""
        ).strip()

        current_time = str(
            ligne[1]
            or ""
        ).strip()

        # ----------------------------------------------------
        # 1. currentDate est TOUJOURS prioritaire.
        # ----------------------------------------------------
        formats_date = (
            "%Y.%m.%d %H:%M:%S",
            "%Y.%m.%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        )

        for format_source in formats_date:
            try:
                date = datetime.strptime(
                    current_date,
                    format_source
                )

                return date.strftime(
                    "%Y.%m.%d %H:%M:%S"
                )

            except ValueError:
                pass

        # ----------------------------------------------------
        # 2. Secours uniquement si currentDate est inutilisable.
        # ----------------------------------------------------
        for format_source in formats_date:
            try:
                date = datetime.strptime(
                    current_time,
                    format_source
                )

                return date.strftime(
                    "%Y.%m.%d %H:%M:%S"
                )

            except ValueError:
                pass

        return ""

    except Exception as erreur:
        print(
            "Lecture date carrière IL-2 impossible :",
            erreur
        )

        return ""

    finally:
        if connexion is not None:
            try:
                connexion.close()
            except Exception:
                pass

def analyser_carriere_il2(chemin):
    """
    Extraction v0.9.3 volontairement limitée à :
    - appareil de l'escadrille ;
    - quantité abstraite actuelle de munitions ;
    - supply de type 4 = ravitaillements munitions.
    """
    chemin = Path(
        chemin
    )

    if not chemin.exists():
        raise FileNotFoundError(
            "Le fichier sélectionné n'existe pas."
        )

    connexion = connexion_sqlite_lecture_seule(
        chemin
    )

    curseur = connexion.cursor()

    tables = {
        ligne[0]
        for ligne in curseur.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()
    }

    tables_requises = {
        "plane",
        "squadron",
        "supply"
    }

    manquantes = (
        tables_requises
        - tables
    )

    if manquantes:
        connexion.close()

        raise ValueError(
            "Base de carrière non reconnue. "
            "Tables manquantes : "
            + ", ".join(
                sorted(
                    manquantes
                )
            )
        )


    # --------------------------------------------------------
    # APPAREIL
    # --------------------------------------------------------
    #
    # On limite aux avions non supprimés et à l'escadrille active.
    # Si plusieurs configs existent, la plus représentée est utilisée.
    # --------------------------------------------------------

    ligne_avion = curseur.execute(
        """
        SELECT
            p.config,
            COUNT(*) AS nombre
        FROM plane AS p
        INNER JOIN squadron AS s
            ON s.id = p.squadronId
        WHERE
            p.isDeleted = 0
            AND s.isDeleted = 0
        GROUP BY p.config
        ORDER BY
            nombre DESC,
            MAX(p.id) DESC
        LIMIT 1
        """
    ).fetchone()


    config_avion = (
        ligne_avion[0]
        if ligne_avion
        else None
    )

    avion = identifier_avion_depuis_config_il2(
        config_avion
    )


    # --------------------------------------------------------
    # STOCK ABSTRAIT DE MUNITIONS ACTUEL DANS IL-2
    # --------------------------------------------------------

    ligne_squadron = curseur.execute(
        """
        SELECT
            id,
            ammoQty
        FROM squadron
        WHERE isDeleted = 0
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()


    squadron_id = (
        int(
            ligne_squadron[0]
        )
        if ligne_squadron
        else None
    )

    ammo_qty = (
        int(
            ligne_squadron[1]
        )
        if ligne_squadron
        else 0
    )


    # --------------------------------------------------------
    # RAVITAILLEMENTS MUNITIONS
    # --------------------------------------------------------
    #
    # Dans la structure de carrière fournie :
    # type 1 = appareil
    # type 3 = carburant
    # type 4 = munitions
    # type 5 = pièces
    #
    # On récupère TOUTES les entrées munitions, pas seulement la dernière.
    # --------------------------------------------------------

    if squadron_id is not None:
        lignes_supply = curseur.execute(
            """
            SELECT
                id,
                supplyNum,
                scheduled,
                status,
                statusDate,
                quantity
            FROM supply
            WHERE
                isDeleted = 0
                AND squadronId = ?
                AND type = 4
            ORDER BY
                scheduled ASC,
                id ASC
            """,
            (
                squadron_id,
            )
        ).fetchall()

    else:
        lignes_supply = curseur.execute(
            """
            SELECT
                id,
                supplyNum,
                scheduled,
                status,
                statusDate,
                quantity
            FROM supply
            WHERE
                isDeleted = 0
                AND type = 4
            ORDER BY
                scheduled ASC,
                id ASC
            """
        ).fetchall()


    ravitaillements = []

    for (
        identifiant,
        numero,
        scheduled,
        status,
        status_date,
        quantity
    ) in lignes_supply:
        ravitaillements.append(
            {
                "id": int(
                    identifiant
                ),
                "numero": int(
                    numero
                ),
                "date_prevue": (
                    scheduled
                    or ""
                ),
                "statut": int(
                    status
                ),
                "date_statut": (
                    status_date
                    or ""
                ),
                "quantite": int(
                    quantity
                )
            }
        )


    ligne_carriere = curseur.execute(
        """
        SELECT
            cuid,
            personageId,
            currentDate,
            currentTime
        FROM career
        WHERE isDeleted = 0
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()


    identifiant_cuid = ""
    identifiant_personage = ""
    date_jeu = ""

    if ligne_carriere:
        identifiant_cuid = str(
            ligne_carriere[0]
            or ""
        ).strip()

        identifiant_personage = str(
            ligne_carriere[1]
            or ""
        ).strip()

        # currentDate est la source de vérité pour la période de campagne.
        # currentTime ne sert que de secours si currentDate est absent.
        date_jeu = (
            ligne_carriere[2]
            or ligne_carriere[3]
            or ""
        )


    connexion.close()


    total_supply = sum(
        element[
            "quantite"
        ]
        for element in ravitaillements
    )


    derniere_supply = (
        ravitaillements[-1]
        if ravitaillements
        else None
    )


    return {
        "fichier": str(
            chemin.resolve()
        ),
        "nom_escadrille": extraire_nom_escadrille_depuis_fichier(
            chemin
        ),
        "avion": avion,
        "config_avion_il2": config_avion,
        "ammo_qty": ammo_qty,
        "date_jeu": date_jeu,
        "career_cuid": identifiant_cuid,
        "career_personage_id": identifiant_personage,
        "ravitaillements_munitions": ravitaillements,
        "total_ravitaillements_munitions": total_supply,
        "derniere_supply_munitions": derniere_supply
    }

def formater_date_supply_il2(texte):
    if not texte:
        return "DATE INCONNUE"

    try:
        date = datetime.strptime(
            texte,
            "%Y.%m.%d %H:%M:%S"
        )

        return date.strftime(
            "%d.%m.%Y - %H:%M"
        )

    except ValueError:
        return str(
            texte
        )

