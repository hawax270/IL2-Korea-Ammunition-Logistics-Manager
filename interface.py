import tkinter as tk
from tkinter import messagebox, filedialog
import tkinter.font as tkfont

import sqlite3
from datetime import datetime, timedelta
import json
from pathlib import Path
import time
import math
import random
import ctypes
import os
import threading
import queue
import re
import shutil
import traceback

from PIL import Image, ImageTk, ImageDraw

from app_data import (
    MUNITIONS,
    AVIONS_EMPORTS,
    PARAMETRES_RAVITAILLEMENT_DEFAUT,
    DISPONIBILITE_SPECIFIQUE,
    COUT_LOGISTIQUE_SPECIFIQUE,
    categorie_logistique,
    cout_logistique,
    disponibilite_logistique,
    stock_cible_logistique,
    cle_coefficient_categorie,
    trier_munitions_logiquement,
    NOMS_MOIS,
    PROFILS_SIMULATION,
    COEFFICIENT_GLOBAL_MOIS_DEFAUT,
    COEFFICIENT_CATEGORIE_MOIS_DEFAUT,
    construire_modele_avance_defaut,
    CLE_MODELE_LOGISTIQUE,
    PALETTES_STOCK,
    categorie_affichage_munition,
    couleur_munition_stock,
    THEME_CLAIR,
    THEME_SOMBRE,
    THEMES,
    CONFIG_DEFAUT,
)
from career_reader import (
    identifier_avion_depuis_config_il2,
    connexion_sqlite_lecture_seule,
    lire_date_carriere_il2,
    extraire_nom_escadrille_depuis_fichier,
    analyser_carriere_il2,
    formater_date_supply_il2,
)

import local_database as local_db
import stock_engine
import updater

from i18n import (
    LANGUES_SUPPORTEES,
    definir_langue,
    langue_active,
    t,
    t_munition,
    t_categorie,
    t_mois,
    t_priorite,
    t_taille_livraison,
    t_statut_livraison,
)


# ============================================================
# VERSION
# ============================================================

VERSION_APPLICATION = "v1.1.1"

# Refactor pré-1.0 : données, lecture carrière et base locale séparées de l’UI.


# ============================================================
# DIMENSIONS
# ============================================================

LARGEUR_FENETRE = 1600
HAUTEUR_FENETRE = 900

HAUTEUR_BARRE_HAUT = 62
HAUTEUR_BARRE_BAS = 64


# ============================================================
# SPLASH SCREEN
# ============================================================

LARGEUR_SPLASH = int(LARGEUR_FENETRE * 0.90)
HAUTEUR_SPLASH = int(HAUTEUR_FENETRE * 0.90)

DUREE_SPLASH = 3.0
DUREE_PULSE = 2.9
NOMBRE_PULSES = 3

TAILLE_LOGO_SPLASH = 100
AGRANDISSEMENT_PULSE = 0.10


# ============================================================
# DOSSIERS / FICHIERS
# ============================================================

DOSSIER = Path(__file__).parent

DOSSIER_IMAGES = DOSSIER / "images"
DOSSIER_AVIONS = DOSSIER_IMAGES / "planes"
DOSSIER_MUNITIONS = DOSSIER_IMAGES / "ordnance"
DOSSIER_BANNIERES_CHARGEMENT = DOSSIER_IMAGES / "loading_banners"

DOSSIER_IMAGES.mkdir(exist_ok=True)
DOSSIER_AVIONS.mkdir(exist_ok=True)
DOSSIER_MUNITIONS.mkdir(exist_ok=True)
DOSSIER_BANNIERES_CHARGEMENT.mkdir(exist_ok=True)

# ============================================================
# DONNÉES UTILISATEUR
# ============================================================
#
# Les fichiers modifiables ne doivent jamais vivre dans Program Files.
# Ils sont stockés dans %LOCALAPPDATA% sous Windows.
#
# Exemple :
# C:\Users\<user>\AppData\Local\hawax270\
#     IL2 Korea Ammunition Logistics Manager\
# ============================================================

def obtenir_dossier_donnees_utilisateur():
    local_appdata = os.environ.get(
        "LOCALAPPDATA",
        ""
    )

    if local_appdata:
        base = Path(
            local_appdata
        )
    else:
        # Fallback surtout utile pour les tests / lancement source
        # hors Windows.
        base = (
            Path.home()
            / ".local"
            / "share"
        )

    return (
        base
        / "hawax270"
        / "IL2 Korea Ammunition Logistics Manager"
    )


DOSSIER_DONNEES = obtenir_dossier_donnees_utilisateur()
DOSSIER_DONNEES.mkdir(
    parents=True,
    exist_ok=True
)

# A partir de la v0.9.13, chaque carrière possède sa propre base locale.
DOSSIER_CARRIERES = DOSSIER_DONNEES / "careers"
DOSSIER_CARRIERES.mkdir(
    parents=True,
    exist_ok=True
)

# Ancienne base globale, conservée uniquement pour une migration éventuelle.
FICHIER_BASE_HERITAGE = DOSSIER_DONNEES / "stock.db"

# Valeur provisoire jusqu'à ce qu'une carrière soit sélectionnée.
FICHIER_BASE = FICHIER_BASE_HERITAGE

FICHIER_CONFIG = DOSSIER_DONNEES / "config.json"

DOSSIER_LOGS = DOSSIER_DONNEES / "logs"
DOSSIER_LOGS.mkdir(
    parents=True,
    exist_ok=True
)

FICHIER_LOG_RUNTIME = DOSSIER_LOGS / "runtime_errors.log"


def migrer_donnees_utilisateur_legacy():
    """
    Copie une seule fois les données runtime d'une ancienne installation
    située à côté du programme vers %LOCALAPPDATA%.

    La migration ne remplace jamais une donnée déjà présente dans le
    nouveau dossier utilisateur.
    """
    try:
        ancien_config = DOSSIER / "config.json"

        if (
            ancien_config.exists()
            and not FICHIER_CONFIG.exists()
        ):
            shutil.copy2(
                ancien_config,
                FICHIER_CONFIG
            )

        ancien_stock = DOSSIER / "stock.db"

        if (
            ancien_stock.exists()
            and not FICHIER_BASE_HERITAGE.exists()
        ):
            shutil.copy2(
                ancien_stock,
                FICHIER_BASE_HERITAGE
            )

        ancien_dossier_carrieres = DOSSIER / "careers"

        if ancien_dossier_carrieres.exists():
            for source in ancien_dossier_carrieres.rglob("*"):
                relatif = source.relative_to(
                    ancien_dossier_carrieres
                )

                destination = (
                    DOSSIER_CARRIERES
                    / relatif
                )

                if source.is_dir():
                    destination.mkdir(
                        parents=True,
                        exist_ok=True
                    )
                    continue

                if not destination.exists():
                    destination.parent.mkdir(
                        parents=True,
                        exist_ok=True
                    )

                    shutil.copy2(
                        source,
                        destination
                    )

        ancien_dossier_logs = DOSSIER / "logs"

        if ancien_dossier_logs.exists():
            for source in ancien_dossier_logs.rglob("*"):
                relatif = source.relative_to(
                    ancien_dossier_logs
                )

                destination = (
                    DOSSIER_LOGS
                    / relatif
                )

                if source.is_dir():
                    destination.mkdir(
                        parents=True,
                        exist_ok=True
                    )
                    continue

                if not destination.exists():
                    destination.parent.mkdir(
                        parents=True,
                        exist_ok=True
                    )

                    shutil.copy2(
                        source,
                        destination
                    )

    except Exception:
        # La migration ne doit jamais empêcher le démarrage.
        pass


migrer_donnees_utilisateur_legacy()

FICHIER_LOGO_SPLASH = DOSSIER_IMAGES / "Loading_screen_image.png"
FICHIER_FOND_SPLASH = DOSSIER_IMAGES / "splash_background.png"


# ============================================================
# APPAREILS
# ============================================================

AVIONS = {
    "F-51D": {
        "image": DOSSIER_AVIONS / "F51D.png"
    },
    "F-80C-10": {
        "image": DOSSIER_AVIONS / "F80.png"
    },
    "F-84E": {
        "image": DOSSIER_AVIONS / "F84E.png"
    },
    "F-86A-5": {
        "image": DOSSIER_AVIONS / "F86.png"
    },
    "MiG-15bis": {
        "image": DOSSIER_AVIONS / "Mig15.png"
    },
    "La-11": {
        "image": DOSSIER_AVIONS / "La11.png"
    },
    "Yak-9P": {
        "image": DOSSIER_AVIONS / "Yak9P.png"
    },
    "IL-10": {
        "image": DOSSIER_AVIONS / "IL10.png"
    }
}


# Bannières facultatives de la fenêtre d'initialisation d'une nouvelle carrière.
# Il suffit d'ajouter/remplacer le PNG correspondant dans images/loading_banners/.
BANNIERES_CHARGEMENT_PAR_AVION = {
    "F-51D": "F51D.png",
    "F-80C-10": "F80.png",
    "F-84E": "F84E.png",
    "F-86A-5": "F86.png",
    "MiG-15bis": "Mig15.png",
    "La-11": "La11.png",
    "Yak-9P": "Yak9P.png",
    "IL-10": "IL10.png",
}


def chemin_banniere_chargement_avion(avion):
    nom_fichier = BANNIERES_CHARGEMENT_PAR_AVION.get(str(avion or ""))
    if not nom_fichier:
        return None
    chemin = DOSSIER_BANNIERES_CHARGEMENT / nom_fichier
    if not chemin.exists():
        return None
    return chemin


# ============================================================
# CATALOGUE DES MUNITIONS / EMPORTS
# Noms repris des écrans IL-2 Korea fournis.
# ============================================================





# ============================================================
# MODELE LOGISTIQUE v0.9.0
# ============================================================
#
# IMPORTANT :
# Ces coefficients sont volontairement des valeurs de SIMULATION
# provisoires. Ils servent à faire fonctionner le moteur dès la v0.9.0.
# Ils pourront être remplacés / recalibrés plus tard avec des données
# historiques documentées, sans changer l'architecture du logiciel.
# ============================================================





















# ============================================================
# PROFILS DE SIMULATION AVANCÉS v0.9.1
# ============================================================
# Les valeurs ci-dessous sont des paramètres de simulation provisoires.
# Elles servent de base technique et NE sont pas présentées comme des
# données historiques définitives. Le système est conçu pour être
# recalibré plus tard avec des sources historiques.
# ============================================================











def cle_preparation_mission_carriere():
    """
    Clé de sauvegarde de la préparation de mission.

    Les valeurs manuelles restent propres à chaque carrière.
    """
    identifiant = str(
        config.get(
            "carriere_id",
            ""
        )
        or ""
    ).strip()

    if identifiant:
        return identifiant

    chemin = str(
        config.get(
            "carriere_fichier",
            ""
        )
        or ""
    ).strip()

    if chemin:
        return chemin

    return "GLOBAL"


def date_preparation_defaut():
    """
    Date affichée dans la préparation de mission.

    Depuis v0.9.51.7, cette valeur vient exclusivement de la carrière IL-2.
    Le joueur ne peut plus la modifier manuellement.
    """
    try:
        date_carriere = extraire_date_complete_carriere(
            DONNEES_CARRIERE_IL2
        )

        if date_carriere is not None:
            return date_carriere.strftime(
                "%d.%m.%Y"
            )

    except Exception:
        pass

    return "09.04.1951"


def rafraichir_date_interface_depuis_carriere(
    donnees_carriere=None
):
    """
    Synchronise le champ DATE de l'interface principale avec la carrière IL-2.

    Cette fonction est appelée uniquement depuis le thread Tkinter.
    Elle ne lit pas SQLite : elle utilise les données déjà lues par le watcher.
    """
    if donnees_carriere is None:
        donnees_carriere = DONNEES_CARRIERE_IL2

    if not isinstance(
        donnees_carriere,
        dict
    ):
        return False

    try:
        date_carriere = extraire_date_complete_carriere(
            donnees_carriere
        )

        if date_carriere is None:
            return False

        texte = date_carriere.strftime(
            "%d.%m.%Y"
        )

        variable = globals().get(
            "variable_date_carriere"
        )

        if variable is None:
            return False

        if str(
            variable.get()
            or ""
        ) != texte:
            variable.set(
                texte
            )

        return True

    except Exception:
        return False


def charger_preparation_mission():
    """
    Charge la préparation de mission.

    La DATE est toujours la date réelle de la carrière IL-2.
    Seule l'HEURE reste personnalisable et persistante par carrière.
    """
    cle = cle_preparation_mission_carriere()

    stockage = config.get(
        "preparation_mission",
        {}
    )

    donnees = stockage.get(
        cle,
        {}
    )

    date_texte = date_preparation_defaut()

    heure_texte = str(
        donnees.get(
            "heure",
            ""
        )
        or ""
    ).strip()

    try:
        datetime.strptime(
            heure_texte,
            "%H:%M"
        )

    except ValueError:
        heure_texte = "10:00"

    return (
        date_texte,
        heure_texte
    )


def sauvegarder_preparation_mission(
    date_texte=None,
    heure_texte=None
):
    """
    Sauvegarde uniquement l'heure de préparation.

    Le paramètre date_texte est conservé dans la signature pour compatibilité
    avec d'anciens appels, mais il est volontairement ignoré.

    Une ancienne clé "date" sauvegardée avant v0.9.51.7 est supprimée dès
    la prochaine sauvegarde de cette carrière.
    """
    cle = cle_preparation_mission_carriere()

    stockage = config.setdefault(
        "preparation_mission",
        {}
    )

    donnees = stockage.setdefault(
        cle,
        {}
    )

    donnees.pop(
        "date",
        None
    )

    if heure_texte is not None:
        heure_texte = str(
            heure_texte
        ).strip()

        try:
            datetime.strptime(
                heure_texte,
                "%H:%M"
            )

            donnees[
                "heure"
            ] = heure_texte

        except ValueError:
            pass

    sauvegarder_config()


def date_mission_vers_mois():
    """
    Utilise le mois de la date de mission si possible.
    Sinon, avril est utilisé comme valeur de secours.
    """
    try:
        date = datetime.strptime(
            champ_date.get(),
            "%d.%m.%Y"
        )
        return date.month
    except Exception:
        return 4



# ============================================================
# MODELE UNIQUE DE CONVERSION LOGISTIQUE
# ============================================================
#
# IL-2 Korea doit rester la source de vérité pour la QUANTITE
# globale de ravitaillement. Ce logiciel ne modifie jamais le jeu.
#
# Son rôle est uniquement de convertir les "unités" abstraites
# du jeu en types et quantités de munitions concrètes.
#
# Pour conserver la compatibilité avec la base v0.9.1 existante,
# le modèle unique utilise encore la clé SQLite "STANDARD" en interne.
# Cette clé n'est plus présentée à l'utilisateur.
# ============================================================




# ============================================================
# PALETTES DE COULEURS DU STOCK
# ============================================================
#
# Chaque famille possède une gamme cohérente :
# - Bombes       : rouges / bruns
# - Roquettes    : bleus
# - Réservoirs   : verts
# - Spécial      : ocres / violets / gris chauds
#
# Les nuances sont attribuées automatiquement aux différentes
# munitions d'une même famille.
# ============================================================








# ============================================================
# THEMES
# ============================================================







# ============================================================
# CONFIGURATION
# ============================================================



def charger_config():
    if not FICHIER_CONFIG.exists():
        with open(FICHIER_CONFIG, "w", encoding="utf-8") as fichier:
            json.dump(CONFIG_DEFAUT, fichier, indent=4)

        return CONFIG_DEFAUT.copy()

    try:
        with open(FICHIER_CONFIG, "r", encoding="utf-8") as fichier:
            resultat = json.load(fichier)

        if resultat.get("theme") not in THEMES:
            resultat["theme"] = "clair"

        if resultat.get("avion") not in AVIONS:
            resultat["avion"] = "F-51D"

        if not isinstance(
            resultat.get("carriere_fichier", ""),
            str
        ):
            resultat["carriere_fichier"] = ""

        if not isinstance(
            resultat.get(
                "preparation_mission",
                {}
            ),
            dict
        ):
            resultat[
                "preparation_mission"
            ] = {}

        if not isinstance(
            resultat.get(
                "mode_admin",
                False
            ),
            bool
        ):
            resultat[
                "mode_admin"
            ] = False

        if resultat.get(
            "taille_police"
        ) not in (
            "compact",
            "standard",
            "grand"
        ):
            resultat[
                "taille_police"
            ] = "standard"

        if resultat.get(
            "taille_fenetres"
        ) not in (
            "compact",
            "standard",
            "grand"
        ):
            resultat[
                "taille_fenetres"
            ] = "standard"

        if resultat.get(
            "langue"
        ) not in LANGUES_SUPPORTEES:
            resultat[
                "langue"
            ] = "en"

        return resultat

    except Exception:
        return CONFIG_DEFAUT.copy()


def sauvegarder_config():
    with open(FICHIER_CONFIG, "w", encoding="utf-8") as fichier:
        json.dump(config, fichier, indent=4)


config = charger_config()

# La langue de la session est fixée au démarrage.
# Un changement depuis Options s'applique au lancement suivant.
definir_langue(
    config.get(
        "langue",
        "en"
    )
)

theme = THEMES[config["theme"]]
avion_selectionne = config["avion"]



# ============================================================
# JOURNAL RUNTIME
# ============================================================

def journaliser_erreur_runtime(
    contexte,
    erreur
):
    """
    Journalise une exception sans faire tomber la boucle Tkinter.

    Le fichier reste purement local à l'application :
    %LOCALAPPDATA%/hawax270/IL2 Korea Ammunition Logistics Manager/logs/runtime_errors.log
    """
    try:
        detail = "".join(
            traceback.format_exception(
                type(
                    erreur
                ),
                erreur,
                erreur.__traceback__
            )
        )

        message = (
            "\n"
            + "=" * 72
            + "\n"
            + datetime.now().strftime(
                "%d.%m.%Y - %H:%M:%S"
            )
            + " | "
            + str(
                contexte
            )
            + "\n"
            + detail
        )

        print(
            message
        )

        with open(
            FICHIER_LOG_RUNTIME,
            "a",
            encoding="utf-8"
        ) as fichier:
            fichier.write(
                message
            )

    except Exception:
        try:
            print(
                "Erreur runtime non journalisable :",
                contexte,
                erreur
            )
        except Exception:
            pass


# ============================================================
# LECTURE DE LA CARRIERE IL-2 KOREA
# ============================================================
# Intervalle de relecture de la carrière pendant que l'interface est ouverte.
# 4000 ms = quasi temps réel sans marteler inutilement le fichier SQLite.
INTERVALLE_SURVEILLANCE_CARRIERE_MS = 4000


#
# IMPORTANT :
# Le fichier de carrière du jeu est ouvert STRICTEMENT EN LECTURE SEULE.
# Ce logiciel ne modifie jamais la base de données IL-2.
# ============================================================

DONNEES_CARRIERE_IL2 = None











def rafraichir_date_carriere_en_memoire():
    """
    Met à jour uniquement DONNEES_CARRIERE_IL2['date_jeu']
    depuis le fichier réel de carrière.

    Retourne True lorsqu'une date a pu être relue.
    """
    global DONNEES_CARRIERE_IL2

    if not isinstance(
        DONNEES_CARRIERE_IL2,
        dict
    ):
        return False

    chemin = str(
        DONNEES_CARRIERE_IL2.get(
            "fichier",
            ""
        )
        or ""
    ).strip()

    if not chemin:
        return False

    date_fraiche = lire_date_carriere_il2(
        chemin
    )

    if not date_fraiche:
        return False

    DONNEES_CARRIERE_IL2[
        "date_jeu"
    ] = date_fraiche

    return True


def obtenir_annee_mois_carriere_frais():
    """
    Source unique pour toute fenêtre / logique affichant une période
    de carrière.

    À CHAQUE appel :
    1. relit career.currentDate/currentTime dans la base IL-2 ;
    2. met à jour DONNEES_CARRIERE_IL2['date_jeu'] ;
    3. retourne l'année et le mois réellement joués.

    Aucun cache de date n'est utilisé pour initialiser une fenêtre.
    """
    rafraichir_date_carriere_en_memoire()

    return extraire_annee_mois_carriere(
        DONNEES_CARRIERE_IL2
    )






def selectionner_carriere_avant_demarrage():
    """
    Fenêtre de liaison affichée AVANT le splash et avant l'interface.
    """
    resultat = {
        "donnees": None
    }


    liaison = tk.Toplevel(fenetre)

    largeur = 820
    hauteur = 560

    liaison.overrideredirect(
        True
    )

    liaison.resizable(
        False,
        False
    )

    adapter_fenetre_simple_ecran(
        liaison,
        largeur,
        hauteur,
        parent=fenetre,
        adapter_contenu=False,
        respecter_profils=True
    )

    liaison.configure(
        bg=theme["fond"]
    )

    try:
        liaison.lift()
        liaison.focus_force()
    except Exception:
        pass


    # Contour.
    contour = tk.Frame(
        liaison,
        bg=theme[
            "contour_fenetre"
        ]
    )

    contour.place(
        x=0,
        y=0,
        relwidth=1.0,
        relheight=1.0
    )


    contenu = tk.Frame(
        liaison,
        bg=theme["fond"]
    )

    contenu.place(
        x=1,
        y=1,
        relwidth=1.0,
        relheight=1.0,
        width=-2,
        height=-2
    )


    # --------------------------------------------------------
    # BARRE DE TITRE
    # --------------------------------------------------------

    barre = tk.Frame(
        contenu,
        height=42,
        bg=theme["barre"]
    )

    barre.pack(
        fill="x"
    )

    barre.pack_propagate(
        False
    )


    label_barre = tk.Label(
        barre,
        text=t("career.banner"),
        font=("Bahnschrift", 10, "bold"),
        anchor="w",
        bg=theme["barre"],
        fg=theme["blanc"]
    )

    label_barre.pack(
        side="left",
        fill="both",
        expand=True
    )


    def annuler():
        resultat[
            "donnees"
        ] = None

        liaison.destroy()


    bouton_fermer = tk.Button(
        barre,
        text="✕",
        command=annuler,
        font=("Bahnschrift", 11, "bold"),
        relief="flat",
        borderwidth=0,
        bg=theme["barre"],
        fg=theme["blanc"],
        activebackground=theme["rouge"],
        activeforeground=theme["blanc"]
    )

    bouton_fermer.pack(
        side="right",
        fill="y",
        ipadx=13
    )


    deplacement = {
        "x": 0,
        "y": 0
    }


    def debut_deplacement_liaison(event):
        deplacement["x"] = (
            event.x_root
            - liaison.winfo_x()
        )

        deplacement["y"] = (
            event.y_root
            - liaison.winfo_y()
        )


    def deplacer_liaison(event):
        px = (
            event.x_root
            - deplacement["x"]
        )

        py = (
            event.y_root
            - deplacement["y"]
        )

        liaison.geometry(
            f"+{px}+{py}"
        )


    for widget in (
        barre,
        label_barre
    ):
        widget.bind(
            "<Button-1>",
            debut_deplacement_liaison
        )

        widget.bind(
            "<B1-Motion>",
            deplacer_liaison
        )


    # --------------------------------------------------------
    # TITRE
    # --------------------------------------------------------

    tk.Label(
        contenu,
        text=t("career.select.title"),
        font=("Bahnschrift", 20, "bold"),
        bg=theme["fond"],
        fg=theme["texte"]
    ).pack(
        pady=(30, 5)
    )


    tk.Label(
        contenu,
        text=t("career.select.description"),
        font=("Bahnschrift", 9),
        justify="center",
        bg=theme["fond"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 18)
    )


    # --------------------------------------------------------
    # FICHIER
    # --------------------------------------------------------

    cadre_fichier = tk.Frame(
        contenu,
        height=68,
        bg=theme["panneau"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    cadre_fichier.pack(
        fill="x",
        padx=38
    )

    cadre_fichier.pack_propagate(
        False
    )


    # La zone d'actions est réservée AVANT le panneau de résultats.
    # Ainsi, même avec le profil GRAND ou sur un écran plus petit,
    # le bouton de sélection de carrière reste toujours accessible.
    zone_boutons = tk.Frame(
        contenu,
        bg=theme["fond"]
    )

    zone_boutons.pack(
        side="bottom",
        fill="x",
        padx=38,
        pady=(0, 24)
    )


    label_fichier = tk.Label(
        cadre_fichier,
        text=t("career.none"),
        font=("Bahnschrift", 9, "bold"),
        anchor="w",
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    )

    label_fichier.pack(
        side="left",
        fill="both",
        expand=True,
        padx=16
    )


    # --------------------------------------------------------
    # RESULTATS
    # --------------------------------------------------------

    cadre_resultats = tk.Frame(
        contenu,
        bg=theme["panneau"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    cadre_resultats.pack(
        fill="both",
        expand=True,
        padx=38,
        pady=16
    )


    titre_resultats = tk.Label(
        cadre_resultats,
        text=t("career.analysis.title"),
        font=("Bahnschrift", 11, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"]
    )

    titre_resultats.pack(
        pady=(16, 12)
    )


    label_avion = tk.Label(
        cadre_resultats,
        text=t("career.aircraft.empty"),
        font=("Bahnschrift", 11, "bold"),
        anchor="w",
        bg=theme["panneau"],
        fg=theme["texte"]
    )

    label_avion.pack(
        fill="x",
        padx=26,
        pady=4
    )


    label_ammo = tk.Label(
        cadre_resultats,
        text=t("career.ammo.empty"),
        font=("Bahnschrift", 10),
        anchor="w",
        bg=theme["panneau"],
        fg=theme["texte"]
    )

    label_ammo.pack(
        fill="x",
        padx=26,
        pady=4
    )


    label_supply = tk.Label(
        cadre_resultats,
        text=t("career.supplies.empty"),
        font=("Bahnschrift", 10),
        anchor="w",
        bg=theme["panneau"],
        fg=theme["texte"]
    )

    label_supply.pack(
        fill="x",
        padx=26,
        pady=4
    )


    label_derniere = tk.Label(
        cadre_resultats,
        text=t("career.last.empty"),
        font=("Bahnschrift", 10),
        anchor="w",
        bg=theme["panneau"],
        fg=theme["texte"]
    )

    label_derniere.pack(
        fill="x",
        padx=26,
        pady=4
    )


    label_etat = tk.Label(
        cadre_resultats,
        text=t("career.waiting"),
        font=("Bahnschrift", 8, "bold"),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    )

    label_etat.pack(
        pady=(14, 8)
    )


    # --------------------------------------------------------
    # ACTIONS
    # --------------------------------------------------------

    bouton_continuer = tk.Button(
        zone_boutons,
        text=t("common.continue"),
        state="disabled",
        font=("Bahnschrift", 10, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte"],
        disabledforeground=theme["texte_faible"],
        activebackground=theme["champ"],
        activeforeground=theme["texte"],
        relief="solid",
        borderwidth=1
    )

    bouton_continuer.pack(
        side="right",
        ipadx=22,
        ipady=7
    )


    def choisir_fichier(chemin_force=None):
        if chemin_force:
            chemin = str(
                chemin_force
            )
        else:
            chemin = filedialog.askopenfilename(
                parent=liaison,
                title=t("career.file_dialog"),
                filetypes=[
                    (
                        t("career.filetype.db"),
                        "*.db"
                    ),
                    (
                        t("career.filetype.all"),
                        "*.*"
                    )
                ]
            )

        if not chemin:
            return


        label_fichier.configure(
            text=Path(
                chemin
            ).name,
            fg=theme["texte"]
        )


        label_etat.configure(
            text=t("career.analyzing"),
            fg=theme["texte_faible"]
        )

        liaison.update_idletasks()


        try:
            donnees = analyser_carriere_il2(
                chemin
            )

        except Exception as erreur:
            resultat[
                "donnees"
            ] = None

            bouton_continuer.configure(
                state="disabled"
            )

            label_avion.configure(
                text=t("career.aircraft.empty")
            )

            label_ammo.configure(
                text=t("career.ammo.empty")
            )

            label_supply.configure(
                text=t("career.supplies.empty")
            )

            label_derniere.configure(
                text=t("career.last.empty")
            )

            label_etat.configure(
                text=(
                    t("common.error").upper() + " : " + str(erreur)
                ),
                fg=theme["rouge"]
            )

            return


        resultat[
            "donnees"
        ] = donnees


        ancien_fichier_carriere = str(
            config.get(
                "carriere_fichier",
                ""
            )
            or ""
        )

        nouveau_fichier_carriere = str(
            Path(
                chemin
            ).resolve()
        )


        config["carriere_fichier"] = (
            nouveau_fichier_carriere
        )

        sauvegarder_config()


        avion = donnees[
            "avion"
        ]


        if avion is None:
            texte_avion = t(
                "career.aircraft_unknown",
                config=str(donnees["config_avion_il2"])
            )

            couleur_avion = theme[
                "rouge"
            ]

        else:
            texte_avion = t("career.aircraft_value", aircraft=avion)

            couleur_avion = theme[
                "vert"
            ]


        label_avion.configure(
            text=texte_avion,
            fg=couleur_avion
        )


        label_ammo.configure(
            text=t(
                "career.current_ammo",
                qty=donnees["ammo_qty"]
            )
        )


        liste_supply = donnees[
            "ravitaillements_munitions"
        ]


        label_supply.configure(
            text=t(
                "career.supply_summary",
                count=len(liste_supply),
                total=donnees["total_ravitaillements_munitions"]
            )
        )


        derniere = donnees[
            "derniere_supply_munitions"
        ]


        if derniere:
            label_derniere.configure(
                text=t(
                    "career.last_delivery",
                    qty=derniere["quantite"],
                    date=formater_date_supply_il2(derniere["date_prevue"])
                )
            )

        else:
            label_derniere.configure(
                text=t("career.last_none")
            )


        label_etat.configure(
            text=t("career.read_only"),
            fg=theme["vert"]
        )


        bouton_continuer.configure(
            state="normal"
        )


    def continuer():
        if resultat[
            "donnees"
        ] is None:
            return

        liaison.destroy()


    bouton_continuer.configure(
        command=continuer
    )


    bouton_selectionner = tk.Button(
        zone_boutons,
        text=t("career.choose"),
        command=choisir_fichier,
        font=("Bahnschrift", 10, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"],
        activebackground=theme["panneau_alt"],
        activeforeground=theme["texte"],
        relief="solid",
        borderwidth=1
    )

    bouton_selectionner.pack(
        side="left",
        ipadx=18,
        ipady=7
    )


    liaison.protocol(
        "WM_DELETE_WINDOW",
        annuler
    )


    chemin_memorise = config.get(
        "carriere_fichier",
        ""
    )

    if (
        chemin_memorise
        and Path(
            chemin_memorise
        ).exists()
    ):
        liaison.after(
            120,
            lambda:
            choisir_fichier(
                chemin_memorise
            )
        )


    # Toute la liaison est désormais construite : applique le même facteur
    # aux contrôles si le moniteur courant est plus petit que 820x560.
    liaison.after_idle(
        lambda:
        adapter_fenetre_simple_ecran(
            liaison,
            largeur,
            hauteur,
            parent=fenetre,
            adapter_contenu=True,
            respecter_profils=True
        )
    )

    fenetre.wait_window(liaison)

    return resultat[
        "donnees"
    ]


# ============================================================
# PROFILS D'AFFICHAGE
# ============================================================

PROFILS_TAILLE_INTERFACE = {
    # COMPACT correspond désormais exactement à l'échelle historique
    # de l'application avant l'ajout des profils d'affichage.
    "compact": {
        "nom": "COMPACT",
        "police": 1.00,
        "fenetre": 1.00
    },

    # STANDARD est volontairement plus confortable.
    "standard": {
        "nom": "STANDARD",
        "police": 1.18,
        "fenetre": 1.10
    },

    # GRAND doit produire une différence nettement perceptible.
    "grand": {
        "nom": "GRAND",
        "police": 1.35,
        "fenetre": 1.20
    }
}


def facteur_taille_police():
    return PROFILS_TAILLE_INTERFACE.get(
        config.get(
            "taille_police",
            "standard"
        ),
        PROFILS_TAILLE_INTERFACE[
            "standard"
        ]
    )[
        "police"
    ]


def facteur_taille_fenetres():
    return PROFILS_TAILLE_INTERFACE.get(
        config.get(
            "taille_fenetres",
            "standard"
        ),
        PROFILS_TAILLE_INTERFACE[
            "standard"
        ]
    )[
        "fenetre"
    ]


# ============================================================
# ADAPTATION AUTOMATIQUE AUX ECRANS / MULTI-MONITEURS
# ============================================================
#
# Chaque fenêtre conserve UNE taille de référence stable. Le dimensionnement
# suit ensuite une règle unique et déterministe : profil demandé -> facteur de
# sécurité écran -> même facteur appliqué au layout. On ne mesure jamais le
# contenu pour agrandir une fenêtre, ce qui évite les dérives entre machines.
# La zone de travail réelle du moniteur (barre des tâches exclue sous Windows)
# reste prise en compte, y compris lorsqu'une fenêtre change de moniteur.

MARGE_ECRAN_ADAPTATIVE = 14
FACTEUR_ECRAN_MINIMUM = 0.40

# Une police peut être légèrement plus grande que le layout, mais jamais au
# point de pousser des contrôles hors écran. Cela garde le réglage de police
# visible sans réintroduire les fenêtres coupées.
RATIO_POLICE_MAX_PAR_LAYOUT = 1.25


def _zone_travail_moniteur(fenetre_cible=None, parent=None, point_ecran=None):
    """Retourne (gauche, haut, largeur, hauteur) du moniteur pertinent.

    ``point_ecran`` permet de choisir explicitement le moniteur contenant un
    point du bureau virtuel. C'est utile au démarrage, lorsque la fenêtre
    principale est volontairement cachée hors écran.
    """
    reference = fenetre_cible

    try:
        if (
            reference is None
            or not reference.winfo_exists()
            or reference.winfo_width() <= 5
            or reference.winfo_height() <= 5
        ):
            reference = parent
    except Exception:
        reference = parent

    try:
        if reference is None:
            reference = fenetre
    except Exception:
        pass

    # Windows : MonitorFromPoint + rcWork permet de tenir compte de la barre
    # des tâches et du moniteur réellement utilisé dans une configuration
    # multi-écrans.
    if os.name == "nt":
        try:
            class POINT(ctypes.Structure):
                _fields_ = [
                    ("x", ctypes.c_long),
                    ("y", ctypes.c_long),
                ]

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            class MONITORINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.c_ulong),
                    ("rcMonitor", RECT),
                    ("rcWork", RECT),
                    ("dwFlags", ctypes.c_ulong),
                ]

            if point_ecran is not None:
                cx = int(point_ecran[0])
                cy = int(point_ecran[1])
            elif reference is not None:
                reference.update_idletasks()
                cx = int(reference.winfo_rootx() + max(1, reference.winfo_width()) / 2)
                cy = int(reference.winfo_rooty() + max(1, reference.winfo_height()) / 2)
            else:
                point_curseur = POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(point_curseur))
                cx = int(point_curseur.x)
                cy = int(point_curseur.y)

            point = POINT(cx, cy)
            MONITOR_DEFAULTTONEAREST = 2

            monitor_from_point = ctypes.windll.user32.MonitorFromPoint
            monitor_from_point.restype = ctypes.c_void_p

            moniteur = monitor_from_point(
                point,
                MONITOR_DEFAULTTONEAREST
            )

            infos = MONITORINFO()
            infos.cbSize = ctypes.sizeof(MONITORINFO)

            if moniteur and ctypes.windll.user32.GetMonitorInfoW(
                moniteur,
                ctypes.byref(infos)
            ):
                rect = infos.rcWork
                largeur = max(1, int(rect.right - rect.left))
                hauteur = max(1, int(rect.bottom - rect.top))
                return (
                    int(rect.left),
                    int(rect.top),
                    largeur,
                    hauteur,
                )
        except Exception:
            pass

    # Fallback portable : écran Tk principal.
    try:
        largeur = max(1, int(reference.winfo_screenwidth()))
        hauteur = max(1, int(reference.winfo_screenheight()))
    except Exception:
        largeur = 1600
        hauteur = 900

    return (0, 0, largeur, hauteur)


def _facteur_pour_zone_travail(
    largeur_reference,
    hauteur_reference,
    zone_travail,
    marge=MARGE_ECRAN_ADAPTATIVE,
):
    """Facteur <= 1 permettant de faire tenir la fenêtre dans la zone utile."""
    _, _, largeur_zone, hauteur_zone = zone_travail

    largeur_disponible = max(240, largeur_zone - 2 * int(marge))
    hauteur_disponible = max(180, hauteur_zone - 2 * int(marge))

    largeur_reference = max(1, float(largeur_reference))
    hauteur_reference = max(1, float(hauteur_reference))

    facteur = min(
        1.0,
        largeur_disponible / largeur_reference,
        hauteur_disponible / hauteur_reference,
    )

    return max(
        FACTEUR_ECRAN_MINIMUM,
        min(1.0, float(facteur))
    )


def _centrer_dans_zone_travail(
    fenetre_cible,
    largeur,
    hauteur,
    parent=None,
    zone_travail=None,
):
    """Centre une fenêtre dans son moniteur et garantit qu'elle reste visible."""
    if zone_travail is None:
        zone_travail = _zone_travail_moniteur(
            fenetre_cible,
            parent=parent,
        )

    gauche, haut, largeur_zone, hauteur_zone = zone_travail

    largeur = max(1, min(int(largeur), largeur_zone))
    hauteur = max(1, min(int(hauteur), hauteur_zone))

    x = gauche + max(0, (largeur_zone - largeur) // 2)
    y = haut + max(0, (hauteur_zone - hauteur) // 2)

    fenetre_cible.geometry(
        f"{largeur}x{hauteur}+{x}+{y}"
    )

    return largeur, hauteur


def _valeur_pixel_tk(valeur):
    try:
        texte = str(valeur).strip()
        if not texte:
            return None
        return int(round(float(texte)))
    except Exception:
        return None


def _adapter_canvas_items_ecran(canvas, facteur):
    """Réduit les coordonnées des éléments Canvas statiques sans cumul."""
    try:
        bases = getattr(canvas, "_coordonnees_canvas_base_ecran", None)
        if bases is None:
            bases = {}
            canvas._coordonnees_canvas_base_ecran = bases

        for item in canvas.find_all():
            if item not in bases:
                try:
                    bases[item] = tuple(canvas.coords(item))
                except Exception:
                    continue

            coords_base = bases.get(item, ())
            if coords_base:
                try:
                    canvas.coords(
                        item,
                        *[
                            float(coord) * facteur
                            for coord in coords_base
                        ]
                    )
                except Exception:
                    pass
    except Exception:
        pass


def _adapter_mise_en_page_widget_ecran(widget, facteur):
    """
    Applique un facteur écran depuis des valeurs de base mémorisées.

    Cette fonction est déterministe : repasser de 0.75 à 1.0 restaure les
    dimensions initiales au lieu de multiplier les redimensionnements.
    """
    facteur = max(
        FACTEUR_ECRAN_MINIMUM,
        min(1.0, float(facteur))
    )

    def parcourir(cible):
        # Widgets gérés par place : x/y/width/height sont des pixels et peuvent
        # donc être mis à l'échelle sans modifier la logique de l'interface.
        try:
            infos_place = cible.place_info()
        except Exception:
            infos_place = {}

        if infos_place:
            base_place = getattr(
                cible,
                "_place_base_ecran",
                None
            )

            if base_place is None:
                base_place = {}
                for cle in ("x", "y", "width", "height"):
                    valeur = _valeur_pixel_tk(infos_place.get(cle, ""))
                    if valeur is not None:
                        base_place[cle] = valeur
                cible._place_base_ecran = base_place

            nouvelles_valeurs = {
                cle: int(round(valeur * facteur))
                for cle, valeur in base_place.items()
            }

            if nouvelles_valeurs:
                try:
                    cible.place_configure(**nouvelles_valeurs)
                except Exception:
                    pass

        # Frames/Canvas packés avec une taille pixel fixe (headers, panneaux,
        # etc.). Les widgets texte utilisent généralement des unités de
        # caractères : on ne touche donc pas à leur width/height ici.
        if isinstance(cible, (tk.Frame, tk.Canvas)) and not infos_place:
            base_dimension = getattr(
                cible,
                "_dimension_base_ecran",
                None
            )

            if base_dimension is None:
                try:
                    largeur_base = _valeur_pixel_tk(cible.cget("width"))
                    hauteur_base = _valeur_pixel_tk(cible.cget("height"))
                    base_dimension = (
                        largeur_base,
                        hauteur_base,
                    )
                    cible._dimension_base_ecran = base_dimension
                except Exception:
                    base_dimension = None

            if base_dimension:
                largeur_base, hauteur_base = base_dimension
                options = {}
                if largeur_base and largeur_base > 1:
                    options["width"] = max(1, int(round(largeur_base * facteur)))
                if hauteur_base and hauteur_base > 1:
                    options["height"] = max(1, int(round(hauteur_base * facteur)))
                if options:
                    try:
                        cible.configure(**options)
                    except Exception:
                        pass

        # Les labels/boutons avec wraplength fixe doivent suivre la même
        # réduction. Sinon le texte peut continuer à réclamer une largeur
        # supérieure à celle de la fenêtre adaptée.
        try:
            wrap_base = getattr(cible, "_wraplength_base_ecran", None)
            if wrap_base is None:
                wrap_actuel = _valeur_pixel_tk(cible.cget("wraplength"))
                if wrap_actuel is not None and wrap_actuel > 0:
                    wrap_base = wrap_actuel
                    cible._wraplength_base_ecran = wrap_base
            if wrap_base:
                cible.configure(
                    wraplength=max(1, int(round(wrap_base * facteur)))
                )
        except Exception:
            pass

        if isinstance(cible, tk.Canvas):
            _adapter_canvas_items_ecran(
                cible,
                facteur
            )

        try:
            enfants = cible.winfo_children()
        except Exception:
            enfants = ()

        for enfant in enfants:
            parcourir(enfant)

    try:
        for enfant in widget.winfo_children():
            parcourir(enfant)
    except Exception:
        pass


def _reinitialiser_references_layout_ecran(widget):
    """Force une nouvelle capture des dimensions de base au prochain passage."""
    attributs = (
        "_place_base_ecran",
        "_dimension_base_ecran",
        "_coordonnees_canvas_base_ecran",
        "_wraplength_base_ecran",
    )

    def parcourir(cible):
        for attribut in attributs:
            try:
                delattr(cible, attribut)
            except Exception:
                pass

        try:
            enfants = cible.winfo_children()
        except Exception:
            enfants = ()

        for enfant in enfants:
            parcourir(enfant)

    parcourir(widget)


def _installer_suivi_moniteur(fenetre_cible, callback):
    """Réajuste une fenêtre lorsqu'elle change de moniteur.

    Le callback courant est remplaçable. C'est important pour les fenêtres
    construites en deux temps : une première passe peut ne positionner que la
    géométrie, puis la passe finale active l'adaptation du contenu.
    """
    fenetre_cible._callback_adaptation_moniteur = callback

    if getattr(
        fenetre_cible,
        "_suivi_moniteur_adaptatif",
        False
    ):
        return

    fenetre_cible._suivi_moniteur_adaptatif = True
    fenetre_cible._zone_moniteur_adaptative = _zone_travail_moniteur(
        fenetre_cible,
        parent=getattr(fenetre_cible, "master", None)
    )
    fenetre_cible._after_adaptation_moniteur = None

    def executer_callback_courant():
        try:
            callback_courant = getattr(
                fenetre_cible,
                "_callback_adaptation_moniteur",
                None
            )
            if callback_courant is not None:
                callback_courant()
        except Exception:
            pass

    def verifier_changement(event=None):
        if event is not None and event.widget is not fenetre_cible:
            return

        if getattr(
            fenetre_cible,
            "_adaptation_ecran_en_cours",
            False
        ):
            return

        try:
            if not fenetre_cible.winfo_exists():
                return
        except Exception:
            return

        nouvelle_zone = _zone_travail_moniteur(
            fenetre_cible,
            parent=getattr(fenetre_cible, "master", None)
        )

        if nouvelle_zone == getattr(
            fenetre_cible,
            "_zone_moniteur_adaptative",
            None
        ):
            return

        fenetre_cible._zone_moniteur_adaptative = nouvelle_zone

        try:
            ancien_after = fenetre_cible._after_adaptation_moniteur
            if ancien_after:
                fenetre_cible.after_cancel(ancien_after)
        except Exception:
            pass

        try:
            fenetre_cible._after_adaptation_moniteur = fenetre_cible.after(
                90,
                executer_callback_courant
            )
        except Exception:
            pass

    fenetre_cible.bind(
        "<Configure>",
        verifier_changement,
        add="+"
    )

def adapter_fenetre_simple_ecran(
    fenetre_cible,
    largeur_base,
    hauteur_base,
    parent=None,
    adapter_contenu=True,
    respecter_profils=False,
):
    """Dimensionnement déterministe des fenêtres simples.

    Principe volontairement simple :
      1. la taille de référence est multipliée par le profil de fenêtre ;
      2. si cela dépasse le moniteur, UN SEUL facteur la fait tenir ;
      3. le contenu reçoit exactement le même facteur de layout ;
      4. la police garde son profil, avec une limite de sécurité par rapport
         au layout pour éviter tout texte ou bouton inaccessible.

    Aucun auto-mesurage du contenu n'est effectué : la géométrie ne peut donc
    plus grossir ou dériver en fonction du rendu de police d'une machine.
    """
    try:
        if not fenetre_cible.winfo_exists():
            return 1.0

        fenetre_cible._adaptation_ecran_en_cours = True
        zone = _zone_travail_moniteur(
            fenetre_cible,
            parent=parent
        )

        facteur_fenetre = (
            facteur_taille_fenetres()
            if respecter_profils
            else 1.0
        )
        facteur_police = (
            facteur_taille_police()
            if respecter_profils
            else 1.0
        )

        largeur_reference = max(
            1,
            int(round(float(largeur_base) * float(facteur_fenetre)))
        )
        hauteur_reference = max(
            1,
            int(round(float(hauteur_base) * float(facteur_fenetre)))
        )

        facteur_ecran = _facteur_pour_zone_travail(
            largeur_reference,
            hauteur_reference,
            zone
        )

        facteur_layout = float(facteur_fenetre) * float(facteur_ecran)
        facteur_police_effectif = min(
            float(facteur_police),
            max(
                FACTEUR_ECRAN_MINIMUM,
                facteur_layout * RATIO_POLICE_MAX_PAR_LAYOUT
            )
        )

        largeur = max(1, int(round(float(largeur_base) * facteur_layout)))
        hauteur = max(1, int(round(float(hauteur_base) * facteur_layout)))

        fenetre_cible._facteur_auto_ecran = facteur_ecran
        fenetre_cible._facteur_layout_effectif = facteur_layout
        fenetre_cible._taille_base_ecran = (
            int(largeur_base),
            int(hauteur_base),
        )
        fenetre_cible._adapter_simple_respecter_profils = bool(
            respecter_profils
        )
        fenetre_cible._adapter_simple_parent = parent

        if adapter_contenu:
            _adapter_mise_en_page_widget_ecran(
                fenetre_cible,
                facteur_layout
            )
            try:
                _appliquer_taille_police_widget(
                    fenetre_cible,
                    facteur_police_effectif
                )
            except Exception:
                pass

        _centrer_dans_zone_travail(
            fenetre_cible,
            largeur,
            hauteur,
            parent=parent,
            zone_travail=zone,
        )

        fenetre_cible._zone_moniteur_adaptative = zone

    except Exception:
        facteur_ecran = 1.0
    finally:
        try:
            fenetre_cible._adaptation_ecran_en_cours = False
        except Exception:
            pass

    _installer_suivi_moniteur(
        fenetre_cible,
        lambda f=fenetre_cible, w=largeur_base, h=hauteur_base, p=parent, rp=respecter_profils:
        adapter_fenetre_simple_ecran(
            f,
            w,
            h,
            parent=p,
            adapter_contenu=adapter_contenu,
            respecter_profils=rp,
        )
    )

    return facteur_ecran

def adapter_fenetre_principale_ecran(adapter_contenu=True):
    """Fait tenir l'interface 1600x900 sur le moniteur où elle se trouve."""
    try:
        if not fenetre.winfo_exists():
            return 1.0

        fenetre._adaptation_ecran_en_cours = True
        zone = _zone_travail_moniteur(
            fenetre,
            parent=None
        )
        facteur = _facteur_pour_zone_travail(
            LARGEUR_FENETRE,
            HAUTEUR_FENETRE,
            zone
        )

        largeur = max(
            320,
            int(round(LARGEUR_FENETRE * facteur))
        )
        hauteur = max(
            240,
            int(round(HAUTEUR_FENETRE * facteur))
        )

        fenetre._facteur_auto_ecran = facteur
        fenetre._taille_base_ecran = (
            LARGEUR_FENETRE,
            HAUTEUR_FENETRE,
        )

        if adapter_contenu:
            _adapter_mise_en_page_widget_ecran(
                fenetre,
                facteur
            )
            facteur_police_effectif = min(
                float(facteur_taille_police()),
                max(
                    FACTEUR_ECRAN_MINIMUM,
                    float(facteur) * RATIO_POLICE_MAX_PAR_LAYOUT
                )
            )
            _appliquer_taille_police_widget(
                fenetre,
                facteur_police_effectif
            )

        _centrer_dans_zone_travail(
            fenetre,
            largeur,
            hauteur,
            parent=None,
            zone_travail=zone,
        )
        fenetre._zone_moniteur_adaptative = zone

    except Exception:
        facteur = 1.0
    finally:
        try:
            fenetre._adaptation_ecran_en_cours = False
        except Exception:
            pass

    _installer_suivi_moniteur(
        fenetre,
        lambda:
        adapter_fenetre_principale_ecran(
            adapter_contenu=True
        )
    )

    return facteur


def _extraire_font_base_widget(
    widget
):
    """
    Capture la police originale d'un widget une seule fois.

    Cela évite les agrandissements cumulatifs lorsque le joueur passe
    plusieurs fois de COMPACT à GRAND puis STANDARD.
    """
    if hasattr(
        widget,
        "_font_base_interface"
    ):
        return widget._font_base_interface

    try:
        valeur_font = widget.cget(
            "font"
        )
    except Exception:
        return None

    if not valeur_font:
        return None

    try:
        font_temp = tkfont.Font(
            font=valeur_font
        )

        infos = font_temp.actual()

        base = {
            "family": infos.get(
                "family",
                POLICE
            ),
            "size": int(
                infos.get(
                    "size",
                    10
                )
            ),
            "weight": infos.get(
                "weight",
                "normal"
            ),
            "slant": infos.get(
                "slant",
                "roman"
            ),
            "underline": int(
                infos.get(
                    "underline",
                    0
                )
            ),
            "overstrike": int(
                infos.get(
                    "overstrike",
                    0
                )
            )
        }

        widget._font_base_interface = base

        return base

    except Exception:
        return None


def _appliquer_taille_police_canvas(canvas, facteur):
    """Applique le profil de police aux textes dessinés dans un Canvas.

    Les Canvas n'exposent pas leurs ``create_text`` comme des widgets Tk.
    Ils échappaient donc jusque-là aux profils COMPACT / STANDARD / GRAND.
    """
    try:
        bases = getattr(canvas, "_polices_canvas_base_interface", None)
        if bases is None:
            bases = {}
            canvas._polices_canvas_base_interface = bases

        for item in canvas.find_all():
            try:
                if canvas.type(item) != "text":
                    continue
            except Exception:
                continue

            base = bases.get(item)
            if base is None:
                try:
                    valeur_font = canvas.itemcget(item, "font")
                    if not valeur_font:
                        continue
                    font_temp = tkfont.Font(font=valeur_font)
                    infos = font_temp.actual()
                    base = {
                        "family": infos.get("family", POLICE),
                        "size": int(infos.get("size", 10)),
                        "weight": infos.get("weight", "normal"),
                        "slant": infos.get("slant", "roman"),
                        "underline": int(infos.get("underline", 0)),
                        "overstrike": int(infos.get("overstrike", 0)),
                    }
                    bases[item] = base
                except Exception:
                    continue

            taille_base = int(base["size"])
            signe = -1 if taille_base < 0 else 1
            nouvelle_taille = signe * max(
                6,
                int(round(abs(taille_base) * float(facteur)))
            )

            styles = []
            if base["weight"] == "bold":
                styles.append("bold")
            if base["slant"] == "italic":
                styles.append("italic")
            if base["underline"]:
                styles.append("underline")
            if base["overstrike"]:
                styles.append("overstrike")

            police = (
                base["family"],
                nouvelle_taille,
                " ".join(styles) if styles else "normal"
            )

            try:
                canvas.itemconfigure(item, font=police)
            except Exception:
                pass
    except Exception:
        pass


def _appliquer_taille_police_widget(
    widget,
    facteur
):
    try:
        if not widget.winfo_exists():
            return
    except Exception:
        return

    # Les cartes de prévisualisation thème restent visuellement stables.
    if getattr(
        widget,
        "_theme_preview_fixe",
        False
    ):
        return

    if isinstance(widget, tk.Canvas):
        _appliquer_taille_police_canvas(
            widget,
            facteur
        )

    base = _extraire_font_base_widget(
        widget
    )

    if base is not None:
        taille_base = int(
            base[
                "size"
            ]
        )

        signe = (
            -1
            if taille_base < 0
            else 1
        )

        nouvelle_taille = signe * max(
            6,
            int(
                round(
                    abs(
                        taille_base
                    )
                    * float(
                        facteur
                    )
                )
            )
        )

        styles = []

        if base[
            "weight"
        ] == "bold":
            styles.append(
                "bold"
            )

        if base[
            "slant"
        ] == "italic":
            styles.append(
                "italic"
            )

        if base[
            "underline"
        ]:
            styles.append(
                "underline"
            )

        if base[
            "overstrike"
        ]:
            styles.append(
                "overstrike"
            )

        police = (
            base[
                "family"
            ],
            nouvelle_taille,
            " ".join(
                styles
            )
            if styles
            else "normal"
        )

        try:
            widget.configure(
                font=police
            )
        except Exception:
            pass

    try:
        enfants = widget.winfo_children()
    except Exception:
        enfants = []

    for enfant in enfants:
        _appliquer_taille_police_widget(
            enfant,
            facteur
        )


def _largeur_texte_widget(
    widget,
    texte=None,
    marge=20
):
    """
    Retourne la largeur réellement nécessaire au texte d'un widget
    avec sa police ACTUELLE.
    """
    try:
        if texte is None:
            try:
                texte = widget.cget(
                    "text"
                )
            except Exception:
                texte = ""

            if not texte:
                try:
                    variable = widget.cget(
                        "textvariable"
                    )

                    if variable:
                        texte = widget.getvar(
                            variable
                        )
                except Exception:
                    pass

        police_widget = tkfont.Font(
            font=widget.cget(
                "font"
            )
        )

        lignes = str(
            texte
            or ""
        ).split(
            "\n"
        )

        largeur = max(
            [
                police_widget.measure(
                    ligne
                )
                for ligne in lignes
            ]
            or [
                1
            ]
        )

        return max(
            1,
            int(
                largeur
                + marge
            )
        )

    except Exception:
        return max(
            1,
            int(
                marge
            )
        )


def _hauteur_controle_widget(
    widget,
    minimum,
    maximum
):
    try:
        police_widget = tkfont.Font(
            font=widget.cget(
                "font"
            )
        )

        hauteur = (
            int(
                police_widget.metrics(
                    "linespace"
                )
            )
            + 14
        )

        return max(
            int(
                minimum
            ),
            min(
                int(
                    maximum
                ),
                hauteur
            )
        )

    except Exception:
        return int(
            minimum
        )


def adapter_boxes_fenetre_principale():
    """
    Ajuste les zones dont la géométrie fixe devient trop petite lorsque
    la police STANDARD ou GRAND est utilisée.

    Le calcul repart TOUJOURS de coordonnées fixes de référence.
    Il n'utilise jamais la géométrie affichée précédemment : aucun effet
    cumulatif n'est donc possible.
    """
    try:
        if not fenetre.winfo_exists():
            return

        fenetre.update_idletasks()

        # ----------------------------------------------------
        # DATE / HEURE / APPAREILS
        # ----------------------------------------------------
        hauteur_champ = max(
            _hauteur_controle_widget(
                champ_date,
                36,
                42
            ),
            _hauteur_controle_widget(
                champ_heure,
                36,
                42
            ),
            _hauteur_controle_widget(
                champ_nombre_avions,
                36,
                42
            )
        )

        champ_date.place_configure(
            x=30,
            y=100,
            width=150,
            height=hauteur_champ
        )

        champ_heure.place_configure(
            x=215,
            y=100,
            width=88,
            height=hauteur_champ
        )

        champ_nombre_avions.place_configure(
            x=400,
            y=100,
            width=100,
            height=hauteur_champ
        )

        # Seule l'heure reste modifiable : les flèches de date ont été retirées.
        demi_heure = max(
            18,
            hauteur_champ // 2
        )

        bouton_heure_plus.place_configure(
            x=303,
            y=100,
            width=22,
            height=demi_heure
        )

        bouton_heure_moins.place_configure(
            x=303,
            y=100 + demi_heure,
            width=22,
            height=max(
                18,
                hauteur_champ - demi_heure
            )
        )

        # ----------------------------------------------------
        # LIGNE PREREGLAGE
        # ----------------------------------------------------
        largeur_label_preset = _largeur_texte_widget(
            label_preset,
            t("main.mission.preset"),
            marge=6
        )

        label_preset.place_configure(
            x=30,
            y=178,
            width=largeur_label_preset
        )

        # Les trois boutons d'action sont ancrés depuis la DROITE.
        # Ainsi ils ne débordent jamais du cadre central.
        largeur_supprimer = min(
            112,
            max(
                82,
                _largeur_texte_widget(
                    bouton_supprimer_preset,
                    marge=20
                )
            )
        )

        largeur_sauver = min(
            108,
            max(
                82,
                _largeur_texte_widget(
                    bouton_sauver_preset,
                    marge=20
                )
            )
        )

        largeur_charger = min(
            112,
            max(
                82,
                _largeur_texte_widget(
                    bouton_charger_preset,
                    marge=20
                )
            )
        )

        droite = 687
        espace = 8

        x_supprimer = (
            droite
            - largeur_supprimer
        )

        x_sauver = (
            x_supprimer
            - espace
            - largeur_sauver
        )

        x_charger = (
            x_sauver
            - espace
            - largeur_charger
        )

        x_preset = max(
            145,
            30
            + largeur_label_preset
            + 12
        )

        largeur_preset = max(
            120,
            x_charger
            - espace
            - x_preset
        )

        hauteur_preset = max(
            _hauteur_controle_widget(
                bouton_preset,
                38,
                44
            ),
            _hauteur_controle_widget(
                bouton_charger_preset,
                38,
                44
            ),
            _hauteur_controle_widget(
                bouton_sauver_preset,
                38,
                44
            ),
            _hauteur_controle_widget(
                bouton_supprimer_preset,
                38,
                44
            )
        )

        bouton_preset.place_configure(
            x=x_preset,
            y=169,
            width=largeur_preset,
            height=hauteur_preset
        )

        bouton_charger_preset.place_configure(
            x=x_charger,
            y=169,
            width=largeur_charger,
            height=hauteur_preset
        )

        bouton_sauver_preset.place_configure(
            x=x_sauver,
            y=169,
            width=largeur_sauver,
            height=hauteur_preset
        )

        bouton_supprimer_preset.place_configure(
            x=x_supprimer,
            y=169,
            width=largeur_supprimer,
            height=hauteur_preset
        )

        # ----------------------------------------------------
        # EN-TETE EMPORT SELECTIONNE
        # ----------------------------------------------------
        largeur_armement = _largeur_texte_widget(
            label_armement,
            t("main.mission.selected_loadout"),
            marge=6
        )

        label_armement.place_configure(
            x=30,
            y=242,
            width=largeur_armement
        )

        largeur_plus = max(
            42,
            _largeur_texte_widget(
                bouton_ajouter_emport,
                "+",
                marge=18
            )
        )

        x_plus = min(
            405,
            30
            + largeur_armement
            + 12
        )

        bouton_ajouter_emport.place_configure(
            x=x_plus,
            y=235,
            width=largeur_plus,
            height=max(
                36,
                _hauteur_controle_widget(
                    bouton_ajouter_emport,
                    36,
                    42
                )
            )
        )

        largeur_total = max(
            65,
            _largeur_texte_widget(
                label_total_titre,
                "TOTAL",
                marge=8
            )
        )

        largeur_par_avion = max(
            85,
            _largeur_texte_widget(
                label_par_avion,
                "PAR AVION",
                marge=8
            )
        )

        x_total = 655 - largeur_total
        x_par_avion = (
            x_total
            - 18
            - largeur_par_avion
        )

        label_par_avion.place_configure(
            x=x_par_avion,
            y=245,
            width=largeur_par_avion
        )

        label_total_titre.place_configure(
            x=x_total,
            y=245,
            width=largeur_total
        )

        # ----------------------------------------------------
        # BOUTON VALIDATION
        # ----------------------------------------------------
        largeur_valider = max(
            240,
            min(
                330,
                _largeur_texte_widget(
                    bouton_valider,
                    marge=38
                )
            )
        )

        bouton_valider.place_configure(
            x=int(
                (
                    740
                    - largeur_valider
                )
                / 2
            ),
            y=610,
            width=largeur_valider,
            height=max(
                44,
                _hauteur_controle_widget(
                    bouton_valider,
                    44,
                    50
                )
            )
        )

        # ----------------------------------------------------
        # HISTORIQUE : BOUTON LONG
        # ----------------------------------------------------
        largeur_effacer = max(
            160,
            min(
                330,
                _largeur_texte_widget(
                    bouton_effacer,
                    t("main.history.clear"),
                    marge=34
                )
            )
        )

        bouton_effacer.place_configure(
            x=int(
                (
                    390
                    - largeur_effacer
                )
                / 2
            ),
            y=620,
            width=largeur_effacer,
            height=max(
                34,
                _hauteur_controle_widget(
                    bouton_effacer,
                    34,
                    42
                )
            )
        )

        # ----------------------------------------------------
        # BOUTONS DU PANNEAU STOCK
        # ----------------------------------------------------
        for bouton, largeur_min, largeur_max, centre in (
            (
                bouton_consulter_stock,
                230,
                340,
                195
            ),
            (
                bouton_rapports,
                178,
                265,
                178
            )
        ):
            largeur = max(
                largeur_min,
                min(
                    largeur_max,
                    _largeur_texte_widget(
                        bouton,
                        marge=34
                    )
                )
            )

            if bouton is bouton_consulter_stock:
                bouton.place_configure(
                    x=int(
                        centre
                        - largeur / 2
                    ),
                    width=largeur
                )
            else:
                # Le badge rapport reste à droite, donc le bouton peut
                # s'étendre uniquement vers la gauche.
                droite_bouton = 258
                bouton.place_configure(
                    x=(
                        droite_bouton
                        - largeur
                    ),
                    width=largeur
                )

        fenetre.update_idletasks()

    except Exception:
        # L'adaptation visuelle ne doit jamais empêcher le lancement.
        pass


def appliquer_taille_police_globale():
    facteur = facteur_taille_police()

    # Restaure d'abord le layout logique 1600x900. Ainsi un changement de
    # langue ou de profil ne recalcule jamais les boîtes depuis une géométrie
    # déjà réduite par un petit écran.
    try:
        _adapter_mise_en_page_widget_ecran(
            fenetre,
            1.0
        )
    except Exception:
        pass

    _appliquer_taille_police_widget(
        fenetre,
        facteur
    )

    try:
        fenetre.update_idletasks()
    except Exception:
        pass

    # Les boîtes et groupes de contrôles de la fenêtre principale
    # suivent maintenant la taille réelle de leur texte.
    adapter_boxes_fenetre_principale()

    # Les éventuelles dimensions recalculées par adapter_boxes deviennent la
    # nouvelle référence logique, puis le facteur écran est réappliqué.
    _reinitialiser_references_layout_ecran(
        fenetre
    )

    try:
        fenetre.after_idle(
            adapter_fenetre_principale_ecran
        )
    except Exception:
        pass

    # Une police plus grande change réellement la place nécessaire au texte.
    # Les fenêtres ouvertes sont donc recalculées depuis leurs dimensions de
    # base, puis réadaptées au moniteur. Le calcul est déterministe et n'est
    # pas cumulatif.
    try:
        fenetre.after_idle(
            appliquer_taille_fenetres_ouvertes
        )
    except Exception:
        pass


def appliquer_taille_fenetres_ouvertes():
    """Réapplique le profil d'affichage ET l'adaptation au moniteur courant."""
    try:
        for enfant in fenetre.winfo_children():
            if not isinstance(
                enfant,
                tk.Toplevel
            ):
                continue

            if getattr(
                enfant,
                "_taille_base_custom",
                None
            ):
                ajuster_fenetre_custom_au_contenu(
                    enfant
                )
                continue

            # Fenêtres simples qui ont explicitement demandé le respect des
            # profils (notamment la sélection de carrière).
            base_simple = getattr(
                enfant,
                "_taille_base_ecran",
                None
            )
            if (
                base_simple
                and getattr(
                    enfant,
                    "_adapter_simple_respecter_profils",
                    False
                )
            ):
                adapter_fenetre_simple_ecran(
                    enfant,
                    base_simple[0],
                    base_simple[1],
                    parent=getattr(
                        enfant,
                        "_adapter_simple_parent",
                        fenetre
                    ),
                    adapter_contenu=True,
                    respecter_profils=True,
                )

    except Exception:
        pass

    # La fenêtre principale utilise elle aussi le même mécanisme automatique.
    try:
        adapter_fenetre_principale_ecran()
    except Exception:
        pass


# ============================================================
# POLICES
# ============================================================

POLICE = "Bahnschrift"

POLICE_TITRE = (POLICE, 21, "bold")
POLICE_SECTION = (POLICE, 12, "bold")
POLICE_TEXTE = (POLICE, 11)
POLICE_PETIT = (POLICE, 10)
POLICE_VALEUR = (POLICE, 19, "bold")



# ============================================================
# IDENTITE LOCALE DE LA CARRIERE
# ============================================================
#
# Refactor v0.9.51 :
# la logique pure de nommage/migration se trouve dans local_database.py.
# Ces wrappers gardent les signatures historiques de l'interface.
# ============================================================

obtenir_identifiant_carriere = (
    local_db.obtenir_identifiant_carriere
)

nom_fichier_carriere_locale = (
    local_db.nom_fichier_carriere_locale
)

cle_sync_carriere = (
    local_db.cle_sync_carriere
)


def base_locale_carriere_existe(
    donnees_carriere
):
    return local_db.base_locale_carriere_existe(
        donnees_carriere,
        DOSSIER_CARRIERES
    )


def configurer_base_locale_carriere(
    donnees_carriere,
    ancien_chemin_config=""
):
    """
    Sélectionne la base locale propre à la carrière.

    Le choix du chemin et la migration legacy sont délégués au backend
    local_database.py ; ce wrapper conserve uniquement l'intégration avec
    config.json et la variable FICHIER_BASE de l'interface historique.
    """
    global FICHIER_BASE

    (
        destination,
        migration_effectuee
    ) = local_db.configurer_base_locale_carriere(
        donnees_carriere,
        DOSSIER_CARRIERES,
        FICHIER_BASE_HERITAGE,
        ancien_chemin_config
    )

    FICHIER_BASE = destination

    config[
        "carriere_id"
    ] = obtenir_identifiant_carriere(
        donnees_carriere
    )

    config[
        "base_carriere_locale"
    ] = str(
        destination
    )

    sauvegarder_config()

    return migration_effectuee


def normaliser_cles_base_migree(
    donnees_carriere
):
    return local_db.normaliser_cles_base_migree(
        FICHIER_BASE,
        donnees_carriere
    )


def enregistrer_meta_carriere_locale(
    donnees_carriere
):
    return local_db.enregistrer_meta_carriere_locale(
        FICHIER_BASE,
        donnees_carriere
    )


# ============================================================
# BASE DE DONNEES
# ============================================================

# Le schéma SQLite et les anciennes migrations de stock sont désormais
# centralisés dans local_database.py.


# ============================================================
# STOCK INITIAL STANDARD PAR APPAREIL
# ============================================================
#
# Ces nombres sont des valeurs de gameplay historiquement plausibles,
# et NON des inventaires d'archives attribués à une base précise.
#
# Philosophie :
# - munitions usuelles : réserves importantes ;
# - bombes lourdes / armes spéciales : volumes plus faibles ;
# - réservoirs : stocks intermédiaires ;
# - appareils principalement air-air : stocks air-sol limités.
#
# Le niveau STANDARD du mois de carrière module ensuite ces quantités :
# CRITIQUE / FORTE / NORMALE / FAIBLE / RARE / INDISPONIBLE.
#
# ============================================================
# STOCK INITIAL STANDARD — moteur extrait en Phase 2B
# ============================================================

def calculer_stock_initial_standard_carriere(
    avion,
    donnees_carriere
):
    return stock_engine.calculer_stock_initial_standard_carriere(
        avion,
        donnees_carriere,
        extraire_annee_mois_carriere=extraire_annee_mois_carriere,
        lire_standard_mensuel_munition=lire_standard_mensuel_munition,
        niveau_standard_munition=niveau_standard_munition
    )




def appliquer_valeurs_usine_nouvelle_carriere(
    donnees_carriere
):
    """
    Initialise l'état usine d'une nouvelle carrière locale.

    Les écritures SQLite sont déléguées à local_database.py.
    """
    return local_db.appliquer_valeurs_usine_nouvelle_carriere(
        FICHIER_BASE,
        VERSION_APPLICATION
    )

def initialiser_base():
    return local_db.initialiser_base(
        FICHIER_BASE
    )


def lire_stock(
    noms=None
):
    return local_db.lire_stock(
        FICHIER_BASE,
        noms
    )


def lire_stock_unitaire(
    nom
):
    return local_db.lire_stock_unitaire(
        FICHIER_BASE,
        nom
    )


def charger_missions():
    return local_db.charger_missions(
        FICHIER_BASE
    )


# ============================================================
# PRESETS D'EMPORT
# ============================================================

def charger_noms_presets(
    avion
):
    return local_db.charger_noms_presets(
        FICHIER_BASE,
        avion
    )


def charger_preset(
    avion,
    nom
):
    return local_db.charger_preset(
        FICHIER_BASE,
        avion,
        nom
    )


def enregistrer_preset(
    avion,
    nom,
    contenu
):
    return local_db.enregistrer_preset(
        FICHIER_BASE,
        avion,
        nom,
        contenu
    )


def supprimer_preset_bdd(
    avion,
    nom
):
    return local_db.supprimer_preset_bdd(
        FICHIER_BASE,
        avion,
        nom
    )


# ============================================================
# MOTEUR DE RAVITAILLEMENT
# ============================================================

def lire_parametres_ravitaillement():
    return local_db.lire_parametres_ravitaillement(
        FICHIER_BASE
    )


def enregistrer_parametres_ravitaillement(
    parametres
):
    return local_db.enregistrer_parametres_ravitaillement(
        FICHIER_BASE,
        parametres
    )


def consommation_recente(nom_munition, nombre_missions=10):
    """
    Lit les dernières missions enregistrées dans notre propre base.
    Le format historique actuel est par exemple :
    '12x AN-M64A1 500 lb | 24x HVAR ...'
    """
    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    curseur.execute(
        """
        SELECT armement
        FROM missions
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            int(nombre_missions),
        )
    )

    total = 0

    motif = re.compile(
        r"(\d+)x\s+"
        + re.escape(nom_munition)
        + r"(?=\s*\||$)"
    )

    for (armement,) in curseur.fetchall():
        correspondance = motif.search(
            armement or ""
        )

        if correspondance:
            total += int(
                correspondance.group(1)
            )

    connexion.close()

    return total


def calculer_capacite_stock():
    """
    Capacité globale de la base, toutes munitions confondues.
    La liste visible peut être filtrée par avion, mais le dépôt est global.
    """
    par_categorie = {
        "Bombes": 0.0,
        "Roquettes": 0.0,
        "Réservoirs": 0.0,
        "Spécial": 0.0
    }

    total = 0.0

    for nom, stock in lire_stock(
        list(MUNITIONS.keys())
    ):
        cout = cout_logistique(
            nom
        )

        valeur = (
            float(stock)
            * cout
        )

        categorie = categorie_logistique(
            nom
        )

        par_categorie[categorie] += valeur
        total += valeur

    return total, par_categorie


def simuler_ravitaillement(
    noms_munitions,
    parametres
):
    """
    Génère une livraison cohérente, sans toucher au stock.

    Facteurs utilisés :
    - disponibilité provisoire de la munition ;
    - déficit par rapport au stock-cible ;
    - consommation récente ;
    - coefficient de catégorie ;
    - variation aléatoire ;
    - capacité libre du dépôt.
    """
    capacite = max(
        1.0,
        float(
            parametres["capacite_depot"]
        )
    )

    stock_utilise, _ = calculer_capacite_stock()

    capacite_libre = max(
        0.0,
        capacite - stock_utilise
    )

    budget_prevu = max(
        0.0,
        float(
            parametres["budget_hebdo"]
        )
    )

    modificateur = max(
        0.0,
        float(
            parametres["modificateur_global"]
        )
    )

    variation = max(
        0.0,
        min(
            0.50,
            float(
                parametres["variation"]
            )
        )
    )

    facteur_aleatoire = random.uniform(
        1.0 - variation,
        1.0 + variation
    )

    budget_reel = (
        budget_prevu
        * modificateur
        * facteur_aleatoire
    )

    # Un dépôt plein coupe physiquement la livraison.
    budget_reel = min(
        budget_reel,
        capacite_libre
    )

    candidats = []

    for nom in noms_munitions:
        stock = lire_stock_unitaire(
            nom
        )

        cible = stock_cible_logistique(
            nom
        )

        categorie = categorie_logistique(
            nom
        )

        dispo = disponibilite_logistique(
            nom
        )

        consommation = consommation_recente(
            nom
        )

        deficit = max(
            0.0,
            (
                cible
                - stock
            )
            / max(
                1,
                cible
            )
        )

        # Même un stock correct garde une faible chance d'être ravitaillé.
        facteur_besoin = (
            0.35
            + 1.85 * deficit
        )

        facteur_usage = (
            1.0
            + min(
                1.25,
                consommation
                / max(
                    1.0,
                    cible * 0.55
                )
            )
            * 0.45
        )

        coef_categorie = max(
            0.0,
            float(
                parametres[
                    cle_coefficient_categorie(
                        categorie
                    )
                ]
            )
        )

        poids = (
            dispo
            * facteur_besoin
            * facteur_usage
            * coef_categorie
        )

        # Evite que les stocks déjà très élevés continuent de grossir.
        if stock >= cible * 1.50:
            poids *= 0.18

        elif stock >= cible:
            poids *= 0.52

        candidats.append(
            {
                "nom": nom,
                "stock": stock,
                "cible": cible,
                "categorie": categorie,
                "disponibilite": dispo,
                "consommation": consommation,
                "deficit": deficit,
                "cout": cout_logistique(nom),
                "poids": max(0.0, poids)
            }
        )

    somme_poids = sum(
        element["poids"]
        for element in candidats
    )

    livraisons = []

    if (
        somme_poids <= 0
        or budget_reel <= 0
    ):
        return {
            "budget_prevu": budget_prevu,
            "budget_reel": budget_reel,
            "budget_utilise": 0.0,
            "capacite_libre": capacite_libre,
            "facteur_aleatoire": facteur_aleatoire,
            "livraisons": []
        }

    budget_utilise = 0.0

    for element in candidats:
        part = (
            budget_reel
            * element["poids"]
            / somme_poids
        )

        quantite = int(
            part
            / max(
                0.01,
                element["cout"]
            )
        )

        # La rareté peut provoquer une semaine sans livraison
        # même si l'arme fait partie du calcul.
        probabilite = min(
            0.97,
            max(
                0.12,
                element["disponibilite"]
                * 0.78
                + element["deficit"]
                * 0.18
            )
        )

        if random.random() > probabilite:
            quantite = 0

        if quantite < 1:
            quantite = 0

        cout_total = (
            quantite
            * element["cout"]
        )

        if (
            budget_utilise
            + cout_total
            > budget_reel
        ):
            quantite = int(
                max(
                    0.0,
                    budget_reel
                    - budget_utilise
                )
                / element["cout"]
            )

            cout_total = (
                quantite
                * element["cout"]
            )

        budget_utilise += cout_total

        raison = []

        if element["deficit"] >= 0.65:
            raison.append(
                "stock critique"
            )

        elif element["deficit"] >= 0.25:
            raison.append(
                "stock faible"
            )

        if element["consommation"] > 0:
            raison.append(
                "consommation récente"
            )

        if element["disponibilite"] < 0.50:
            raison.append(
                "approvisionnement rare"
            )

        elif element["disponibilite"] >= 1.05:
            raison.append(
                "approvisionnement courant"
            )

        if not raison:
            raison.append(
                "dotation régulière"
            )

        livraisons.append(
            {
                **element,
                "quantite": quantite,
                "cout_total": cout_total,
                "raison": " • ".join(
                    raison
                )
            }
        )

    return {
        "budget_prevu": budget_prevu,
        "budget_reel": budget_reel,
        "budget_utilise": budget_utilise,
        "capacite_libre": capacite_libre,
        "facteur_aleatoire": facteur_aleatoire,
        "livraisons": livraisons
    }


def appliquer_ravitaillement_simule(
    avion,
    simulation,
    parametres
):
    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    details = {}

    for element in simulation["livraisons"]:
        quantite = int(
            element["quantite"]
        )

        if quantite <= 0:
            continue

        curseur.execute(
            """
            UPDATE munitions
            SET stock = stock + ?
            WHERE nom = ?
            """,
            (
                quantite,
                element["nom"]
            )
        )

        details[element["nom"]] = quantite

    curseur.execute(
        """
        INSERT INTO ravitaillements (
            date_heure,
            avion,
            budget_prevu,
            budget_reel,
            modificateur,
            details
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime(
                "%d.%m.%Y - %H:%M"
            ),
            avion,
            float(
                simulation["budget_prevu"]
            ),
            float(
                simulation["budget_reel"]
            ),
            float(
                parametres[
                    "modificateur_global"
                ]
            ),
            json.dumps(
                details,
                ensure_ascii=False
            )
        )
    )

    connexion.commit()
    connexion.close()

    return details



# ============================================================
# PROFILS DE SIMULATION — PERSISTANCE
# ============================================================

def charger_modele_avance(cle_profil):
    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    curseur.execute(
        """
        SELECT donnees
        FROM modeles_simulation
        WHERE profil = ?
        LIMIT 1
        """,
        (
            cle_profil,
        )
    )

    ligne = curseur.fetchone()

    if ligne is None:
        modele = construire_modele_avance_defaut(
            cle_profil
        )
        connexion.close()
        return modele

    try:
        modele = json.loads(
            ligne[0]
        )
    except Exception:
        modele = construire_modele_avance_defaut(
            cle_profil
        )

    connexion.close()

    # Migration douce si une future clé manque.
    defaut = construire_modele_avance_defaut(
        cle_profil
    )

    for cle in (
        "budget_hebdo",
        "capacite_depot",
        "variation",
        "modificateur_global",
        "priorites",
        "mois",
        "munitions"
    ):
        if cle not in modele:
            modele[cle] = defaut[cle]

    for nom in MUNITIONS:
        if nom not in modele["munitions"]:
            modele["munitions"][nom] = defaut["munitions"][nom]

    return modele


def sauvegarder_modele_avance(
    cle_profil,
    modele
):
    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    curseur.execute(
        """
        INSERT INTO modeles_simulation (
            profil,
            donnees
        )
        VALUES (?, ?)
        ON CONFLICT(profil)
        DO UPDATE SET donnees = excluded.donnees
        """,
        (
            cle_profil,
            json.dumps(
                modele,
                ensure_ascii=False
            )
        )
    )

    connexion.commit()
    connexion.close()


def reinitialiser_modele_avance(
    cle_profil
):
    modele = construire_modele_avance_defaut(
        cle_profil
    )

    sauvegarder_modele_avance(
        cle_profil,
        modele
    )

    return modele


def simuler_ravitaillement_avance(
    noms_munitions,
    cle_profil,
    mois,
    priorites_rapides=None
):
    modele = charger_modele_avance(
        cle_profil
    )

    mois = int(
        max(
            1,
            min(
                12,
                int(mois)
            )
        )
    )

    if priorites_rapides is None:
        priorites_rapides = {}

    capacite = max(
        1.0,
        float(
            modele["capacite_depot"]
        )
    )

    stock_utilise, _ = calculer_capacite_stock()

    capacite_libre = max(
        0.0,
        capacite - stock_utilise
    )

    coef_mois_global = float(
        modele["mois"][
            str(mois)
        ]["global"]
    )

    variation = max(
        0.0,
        min(
            0.50,
            float(
                modele["variation"]
            )
        )
    )

    facteur_aleatoire = random.uniform(
        1.0 - variation,
        1.0 + variation
    )

    budget_prevu = max(
        0.0,
        float(
            modele["budget_hebdo"]
        )
        * coef_mois_global
    )

    budget_reel = (
        budget_prevu
        * max(
            0.0,
            float(
                modele["modificateur_global"]
            )
        )
        * facteur_aleatoire
    )

    budget_reel = min(
        budget_reel,
        capacite_libre
    )

    candidats = []

    for nom in noms_munitions:
        stock = lire_stock_unitaire(
            nom
        )

        params_munition = modele[
            "munitions"
        ][nom]

        categorie = categorie_logistique(
            nom
        )

        stock_cible = max(
            1,
            int(
                params_munition[
                    "stock_cible"
                ]
            )
        )

        disponibilite = max(
            0.0,
            float(
                params_munition[
                    "disponibilite"
                ]
            )
        )

        cout = max(
            0.01,
            float(
                params_munition[
                    "cout_logistique"
                ]
            )
        )

        coef_munition_mois = max(
            0.0,
            float(
                params_munition[
                    "mois"
                ][str(mois)]
            )
        )

        coef_categorie_mois = max(
            0.0,
            float(
                modele["mois"][
                    str(mois)
                ]["categories"][
                    categorie
                ]
            )
        )

        priorite_modele = max(
            0.0,
            float(
                modele["priorites"][
                    categorie
                ]
            )
        )

        priorite_rapide = max(
            0.0,
            float(
                priorites_rapides.get(
                    categorie,
                    1.0
                )
            )
        )

        consommation = consommation_recente(
            nom
        )

        deficit = max(
            0.0,
            (
                stock_cible
                - stock
            )
            / stock_cible
        )

        facteur_besoin = (
            0.30
            + 1.95 * deficit
        )

        facteur_usage = (
            1.0
            + min(
                1.25,
                consommation
                / max(
                    1.0,
                    stock_cible * 0.55
                )
            )
            * 0.45
        )

        poids = (
            disponibilite
            * coef_munition_mois
            * coef_categorie_mois
            * priorite_modele
            * priorite_rapide
            * facteur_besoin
            * facteur_usage
        )

        if stock >= stock_cible * 1.50:
            poids *= 0.16
        elif stock >= stock_cible:
            poids *= 0.50

        candidats.append(
            {
                "nom": nom,
                "stock": stock,
                "stock_cible": stock_cible,
                "categorie": categorie,
                "disponibilite": disponibilite,
                "consommation": consommation,
                "deficit": deficit,
                "cout": cout,
                "poids": max(
                    0.0,
                    poids
                )
            }
        )

    somme_poids = sum(
        element["poids"]
        for element in candidats
    )

    livraisons = []
    budget_utilise = 0.0

    if (
        somme_poids > 0
        and budget_reel > 0
    ):
        for element in candidats:
            part = (
                budget_reel
                * element["poids"]
                / somme_poids
            )

            quantite = int(
                part
                / element["cout"]
            )

            probabilite = min(
                0.98,
                max(
                    0.08,
                    element["disponibilite"]
                    * 0.76
                    + element["deficit"]
                    * 0.20
                )
            )

            if random.random() > probabilite:
                quantite = 0

            cout_total = (
                quantite
                * element["cout"]
            )

            if (
                budget_utilise
                + cout_total
                > budget_reel
            ):
                quantite = int(
                    max(
                        0.0,
                        budget_reel
                        - budget_utilise
                    )
                    / element["cout"]
                )

                cout_total = (
                    quantite
                    * element["cout"]
                )

            budget_utilise += cout_total

            raisons = []

            if element["deficit"] >= 0.65:
                raisons.append(
                    "stock critique"
                )
            elif element["deficit"] >= 0.25:
                raisons.append(
                    "stock faible"
                )

            if element["consommation"] > 0:
                raisons.append(
                    "consommation récente"
                )

            if element["disponibilite"] < 0.50:
                raisons.append(
                    "approvisionnement rare"
                )
            elif element["disponibilite"] >= 1.05:
                raisons.append(
                    "approvisionnement courant"
                )

            if not raisons:
                raisons.append(
                    "dotation régulière"
                )

            livraisons.append(
                {
                    **element,
                    "quantite": max(
                        0,
                        int(
                            quantite
                        )
                    ),
                    "cout_total": cout_total,
                    "raison": " • ".join(
                        raisons
                    )
                }
            )

    return {
        "profil": cle_profil,
        "mois": mois,
        "budget_prevu": budget_prevu,
        "budget_reel": budget_reel,
        "budget_utilise": budget_utilise,
        "capacite_libre": capacite_libre,
        "facteur_aleatoire": facteur_aleatoire,
        "livraisons": livraisons
    }



# ============================================================
# SYNCHRONISATION STOCK <-> CARRIERE IL-2
# ============================================================
#
# NOTE ARCHITECTURE :
# Le type d'appareil d'une carrière IL-2 peut évoluer au cours de la carrière.
# La v0.9.6 ne traite volontairement PAS encore ce cas fonctionnellement.
# Ce point devra être géré dans une future version dédiée pour éviter
# de mélanger les stocks de plusieurs appareils / périodes de carrière.
#
#
# Principe :
# - IL-2 fournit ammoQty = volume abstrait de munitions disponible.
# - Le logiciel transforme ce volume en munitions concrètes compatibles.
# - La répartition v0.9.4 est un MODELE STANDARD PROVISOIRE.
# - Elle est déterministe : même carrière / avion / ammoQty = même résultat.
# - Si ammoQty ne change pas, on ne régénère PAS le stock local afin de
#   conserver les consommations effectuées dans le logiciel.
# ============================================================


# ============================================================
# BOOSTS DU HAUT COMMANDEMENT — LECTURE NÉCESSAIRE AU STOCK
# ============================================================
#
# IMPORTANT :
# lire_boost_commandement() est utilisée par
# calculer_repartition_standard_carriere(), donc elle doit être définie
# AVANT la synchronisation initiale de la carrière.
#
# Un ravitaillement IL-2 peut provoquer un delta positif ammoQty dès le
# démarrage et entrer immédiatement dans ce chemin.
# ============================================================

def lire_boost_commandement(
    annee,
    mois,
    avion,
    munition
):
    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        curseur = connexion.cursor()

        ligne = curseur.execute(
            """
            SELECT
                boost_pourcent,
                cout_total,
                date_demande
            FROM boosts_commandement
            WHERE
                annee = ?
                AND mois = ?
                AND avion = ?
                AND munition = ?
            LIMIT 1
            """,
            (
                int(
                    annee
                ),
                int(
                    mois
                ),
                str(
                    avion
                ),
                str(
                    munition
                )
            )
        ).fetchone()

        connexion.close()

        if ligne is None:
            return {
                "boost_pourcent": 0.0,
                "cout_total": 0,
                "date_demande": ""
            }

        return {
            "boost_pourcent": max(
                0.0,
                float(
                    ligne[0]
                )
            ),
            "cout_total": max(
                0,
                int(
                    ligne[1]
                )
            ),
            "date_demande": str(
                ligne[2]
                or ""
            )
        }

    except sqlite3.Error:
        return {
            "boost_pourcent": 0.0,
            "cout_total": 0,
            "date_demande": ""
        }


def calculer_repartition_standard_carriere(
    avion,
    ammo_qty,
    donnees_carriere
):
    """
    Transforme un delta abstrait IL-2 en stock concret.

    La répartition utilise désormais :
    - le modèle actif STANDARD ou PERSONNALISÉ ;
    - le niveau attribué à chaque munition ;
    - la quantité de référence associée à ce niveau ;
    - une normalisation des poids à 100 %.

    Les coûts logistiques restent utilisés pour convertir la part du budget
    abstrait IL-2 en quantité concrète de munition.
    """

    compatibles = trier_munitions_logiquement(
        AVIONS_EMPORTS.get(
            avion,
            []
        )
    )

    if not compatibles:
        return {}

    annee_modele, mois_modele = (
        extraire_annee_mois_carriere(
            donnees_carriere
        )
    )

    modele_repartition = (
        cle_modele_repartition_actif()
    )

    quantites_niveaux = (
        obtenir_quantites_niveaux_periode(
            modele_repartition,
            annee_modele,
            mois_modele
        )
    )

    modele_logistique = charger_modele_avance(
        CLE_MODELE_LOGISTIQUE
    )

    candidats = []

    for nom in compatibles:
        niveau = lire_niveau_munition_periode(
            modele_repartition,
            annee_modele,
            mois_modele,
            avion,
            nom
        )

        if modele_repartition == "STANDARD":
            niveau = niveau_standard_effectif_avec_directive(
                annee_modele,
                mois_modele,
                avion,
                nom
            )

            poids = max(
                0.0,
                float(
                    QUANTITES_STANDARD_NIVEAUX.get(
                        niveau,
                        0.0
                    )
                )
            )
        else:
            poids = max(
                0.0,
                float(
                    quantites_niveaux.get(
                        niveau,
                        0.0
                    )
                )
            )

        if niveau == "INDISPONIBLE":
            poids = 0.0

        boost_pourcent = float(
            lire_boost_commandement(
                annee_modele,
                mois_modele,
                avion,
                nom
            )[
                "boost_pourcent"
            ]
        )

        params = modele_logistique[
            "munitions"
        ].get(
            nom,
            {}
        )

        cout = max(
            0.01,
            float(
                params.get(
                    "cout_logistique",
                    cout_logistique(
                        nom
                    )
                )
            )
        )

        candidats.append(
            {
                "nom": nom,
                "niveau": niveau,
                "cout": cout,
                "poids": poids,
                "boost_pourcent": boost_pourcent
            }
        )

    somme_poids = sum(
        element[
            "poids"
        ]
        for element in candidats
    )

    if somme_poids <= 0:
        return {
            nom: 0
            for nom in compatibles
        }

    budget_restant = max(
        0.0,
        float(
            ammo_qty
        )
    )

    resultat = {
        nom: 0
        for nom in compatibles
    }

    # Première passe : parts strictement normalisées par les quantités
    # de référence du modèle.
    for element in candidats:
        if element[
            "poids"
        ] <= 0:
            continue

        part_budget = (
            float(
                ammo_qty
            )
            * element[
                "poids"
            ]
            / somme_poids
        )

        quantite = max(
            0,
            int(
                part_budget
                / element[
                    "cout"
                ]
            )
        )

        resultat[
            element[
                "nom"
            ]
        ] = quantite

        budget_restant -= (
            quantite
            * element[
                "cout"
            ]
        )

    # Reliquat : on privilégie d'abord les munitions qui ont le plus
    # grand poids de référence, puis le coût logistique le plus faible.
    candidats_reliquat = sorted(
        (
            element
            for element in candidats
            if element[
                "poids"
            ] > 0
        ),
        key=lambda element: (
            -element[
                "poids"
            ],
            element[
                "cout"
            ],
            element[
                "nom"
            ]
        )
    )

    securite = 0

    while (
        budget_restant > 0.01
        and securite < 10000
    ):
        progression = False

        for element in candidats_reliquat:
            cout = element[
                "cout"
            ]

            if cout <= budget_restant:
                resultat[
                    element[
                        "nom"
                    ]
                ] += 1

                budget_restant -= cout
                progression = True

        if not progression:
            break

        securite += 1

    # --------------------------------------------------------
    # BONUS DU HAUT COMMANDEMENT
    # --------------------------------------------------------
    # Le boost ne consomme PAS le budget ammoQty reçu d'IL-2.
    # C'est un ajout local offert par le commandement.
    #
    # Exemple :
    # ammo_qty = 300
    # boost HVAR = +15 %
    # budget bonus HVAR = 45 unités logistiques supplémentaires.
    #
    # Les autres munitions ne sont jamais diminuées.
    for element in candidats:
        boost_pourcent = max(
            0.0,
            float(
                element.get(
                    "boost_pourcent",
                    0.0
                )
            )
        )

        if boost_pourcent <= 0:
            continue

        budget_bonus = (
            float(
                ammo_qty
            )
            * boost_pourcent
            / 100.0
        )

        quantite_bonus = max(
            0,
            int(
                budget_bonus
                / element[
                    "cout"
                ]
            )
        )

        resultat[
            element[
                "nom"
            ]
        ] += quantite_bonus

    return resultat




def calculer_retrait_stock_carriere(
    avion,
    budget_a_retirer
):
    """
    Retire un delta d'unités IL-2 du stock concret existant.

    Le retrait est réparti proportionnellement à la place logistique
    actuellement occupée par chaque munition compatible.
    """
    budget_a_retirer = max(
        0.0,
        float(
            budget_a_retirer
        )
    )

    compatibles = trier_munitions_logiquement(
        AVIONS_EMPORTS.get(
            avion,
            []
        )
    )

    modele = charger_modele_avance(
        CLE_MODELE_LOGISTIQUE
    )

    elements = []

    for nom in compatibles:
        stock = lire_stock_unitaire(
            nom
        )

        if stock <= 0:
            continue

        params = modele[
            "munitions"
        ].get(
            nom,
            {}
        )

        cout = max(
            0.01,
            float(
                params.get(
                    "cout_logistique",
                    cout_logistique(
                        nom
                    )
                )
            )
        )

        valeur = (
            stock
            * cout
        )

        elements.append(
            {
                "nom": nom,
                "stock": stock,
                "cout": cout,
                "valeur": valeur
            }
        )

    valeur_totale = sum(
        element[
            "valeur"
        ]
        for element in elements
    )

    if valeur_totale <= 0:
        return {}

    cible = min(
        budget_a_retirer,
        valeur_totale
    )

    retraits = {
        element["nom"]: 0
        for element in elements
    }

    budget_restant = cible

    # Première passe proportionnelle.
    for element in elements:
        part = (
            cible
            * element["valeur"]
            / valeur_totale
        )

        quantite = min(
            element["stock"],
            int(
                part
                / element["cout"]
            )
        )

        retraits[
            element["nom"]
        ] = quantite

        budget_restant -= (
            quantite
            * element["cout"]
        )

    # Deuxième passe : consomme le reliquat avec les plus petits coûts.
    ordre_reliquat = sorted(
        elements,
        key=lambda element: (
            element["cout"],
            element["nom"]
        )
    )

    securite = 0

    while (
        budget_restant > 0.01
        and securite < 10000
    ):
        progression = False

        for element in ordre_reliquat:
            nom = element["nom"]

            restant_munition = (
                element["stock"]
                - retraits[nom]
            )

            if restant_munition <= 0:
                continue

            if element["cout"] <= budget_restant:
                retraits[nom] += 1
                budget_restant -= element["cout"]
                progression = True

        if not progression:
            break

        securite += 1

    return {
        nom: quantite
        for nom, quantite in retraits.items()
        if quantite > 0
    }


def synchroniser_stock_avec_carriere(
    donnees_carriere
):
    """
    Wrapper historique conservé pour l'interface.

    Le moteur SQLite de synchronisation vit dans stock_engine.py.
    """
    return stock_engine.synchroniser_stock_avec_carriere(
        FICHIER_BASE,
        donnees_carriere,
        calculer_stock_initial=calculer_stock_initial_standard_carriere,
        calculer_repartition=calculer_repartition_standard_carriere
    )



# ============================================================
# DELTA TEMPS RÉEL DE LA CARRIÈRE
# ============================================================

def appliquer_delta_carriere_temps_reel(
    donnees_carriere,
    ancienne_valeur,
    nouvelle_valeur
):
    """
    Wrapper historique conservé pour le watcher Tkinter.

    Le traitement stock + snapshot est effectué dans stock_engine.py.
    """
    return stock_engine.appliquer_delta_carriere_temps_reel(
        FICHIER_BASE,
        donnees_carriere,
        ancienne_valeur,
        nouvelle_valeur,
        calculer_repartition=calculer_repartition_standard_carriere
    )


# ============================================================
# CAPACITÉ IL-2 / RÉFÉRENCE HAUTE DE CARRIÈRE
# ============================================================

def mettre_a_jour_reference_capacite_carriere(
    donnees_carriere
):
    """
    Le 100 % du donut correspond à la plus haute valeur ammoQty
    jamais observée pour CE fichier de carrière.

    Une baisse ne modifie jamais cette référence.
    Une hausse qui dépasse l'ancien maximum devient le nouveau 100 %.
    """
    if not donnees_carriere:
        return 1

    fichier = cle_sync_carriere(
        donnees_carriere
    )

    ammo_qty = max(
        0,
        int(
            donnees_carriere.get(
                "ammo_qty",
                0
            )
        )
    )

    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    ligne = curseur.execute(
        """
        SELECT reference_max
        FROM capacite_carriere
        WHERE fichier = ?
        LIMIT 1
        """,
        (
            fichier,
        )
    ).fetchone()

    if ligne is None:
        reference = max(
            1,
            ammo_qty
        )

        curseur.execute(
            """
            INSERT INTO capacite_carriere (
                fichier,
                reference_max
            )
            VALUES (?, ?)
            """,
            (
                fichier,
                reference
            )
        )

    else:
        reference = max(
            1,
            int(
                ligne[0]
            )
        )

        if ammo_qty > reference:
            reference = ammo_qty

            curseur.execute(
                """
                UPDATE capacite_carriere
                SET reference_max = ?
                WHERE fichier = ?
                """,
                (
                    reference,
                    fichier
                )
            )

    connexion.commit()
    connexion.close()

    return reference


def lire_reference_capacite_carriere(
    donnees_carriere
):
    """
    Lit la référence haute mémorisée.
    Si elle n'existe pas encore, elle est créée à partir de ammoQty.
    """
    if not donnees_carriere:
        return 1

    fichier = cle_sync_carriere(
        donnees_carriere
    )

    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    ligne = curseur.execute(
        """
        SELECT reference_max
        FROM capacite_carriere
        WHERE fichier = ?
        LIMIT 1
        """,
        (
            fichier,
        )
    ).fetchone()

    connexion.close()

    if ligne is None:
        return mettre_a_jour_reference_capacite_carriere(
            donnees_carriere
        )

    return max(
        1,
        int(
            ligne[0]
        )
    )


# ============================================================
# RAPPORTS DE CARRIÈRE / NOTIFICATIONS
# ============================================================

def reinitialiser_rapports_pour_nouvelle_carriere():
    """
    Tant que le logiciel ne gère pas encore plusieurs carrières en parallèle,
    les rapports appartiennent uniquement à la carrière actuellement liée.

    Lorsqu'un autre fichier de carrière est sélectionné :
    - anciens rapports supprimés ;
    - compteur de notifications remis à zéro.

    Le stock de munitions est géré séparément par la synchronisation carrière.
    """
    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        curseur = connexion.cursor()

        curseur.execute(
            """
            DELETE FROM rapports_carriere
            """
        )

        connexion.commit()
        connexion.close()

    except sqlite3.Error as erreur:
        print(
            "Impossible de réinitialiser les rapports :",
            erreur
        )

    actualiser_badge_rapports()



def enregistrer_rapport_carriere(
    donnees_carriere,
    resultat
):
    """
    Enregistre une alerte persistante dans stock.db.
    """
    if not resultat:
        return None

    type_changement = resultat.get(
        "type_changement",
        "aucun"
    )

    if type_changement == "aucun":
        return None

    details = resultat.get(
        "changements",
        {}
    )

    date_jeu = str(
        donnees_carriere.get(
            "date_jeu",
            ""
        )
        or "DATE IN-GAME INCONNUE"
    )

    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    curseur.execute(
        """
        INSERT INTO rapports_carriere (
            date_jeu,
            date_locale,
            type_changement,
            ancienne_valeur,
            nouvelle_valeur,
            delta,
            details,
            valide
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            date_jeu,
            datetime.now().strftime(
                "%d.%m.%Y - %H:%M:%S"
            ),
            type_changement,
            resultat.get(
                "ancienne_valeur"
            ),
            int(
                resultat.get(
                    "nouvelle_valeur",
                    0
                )
            ),
            int(
                resultat.get(
                    "delta",
                    0
                )
            ),
            json.dumps(
                details,
                ensure_ascii=False
            )
        )
    )

    identifiant = curseur.lastrowid

    connexion.commit()
    connexion.close()

    actualiser_badge_rapports()

    return identifiant


def charger_rapports_carriere():
    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    curseur.execute(
        """
        SELECT
            id,
            date_jeu,
            date_locale,
            type_changement,
            ancienne_valeur,
            nouvelle_valeur,
            delta,
            details,
            valide
        FROM rapports_carriere
        ORDER BY id DESC
        """
    )

    lignes = curseur.fetchall()

    connexion.close()

    resultat = []

    for ligne in lignes:
        try:
            details = json.loads(
                ligne[7]
            )
        except Exception:
            details = {}

        resultat.append(
            {
                "id": int(
                    ligne[0]
                ),
                "date_jeu": ligne[1],
                "date_locale": ligne[2],
                "type_changement": ligne[3],
                "ancienne_valeur": ligne[4],
                "nouvelle_valeur": int(
                    ligne[5]
                ),
                "delta": int(
                    ligne[6]
                ),
                "details": details,
                "valide": bool(
                    ligne[8]
                )
            }
        )

    return resultat


def compter_rapports_non_valides():
    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        curseur = connexion.cursor()

        valeur = curseur.execute(
            """
            SELECT COUNT(*)
            FROM rapports_carriere
            WHERE valide = 0
            """
        ).fetchone()[0]

        connexion.close()

        return int(
            valeur
        )

    except Exception:
        return 0


def actualiser_badge_rapports():
    compteur = compter_rapports_non_valides()

    label = globals().get(
        "label_badge_rapports"
    )

    if label is None:
        return

    try:
        if not label.winfo_exists():
            return
    except Exception:
        return

    valeur_affichee = min(
        25,
        compteur
    )

    label.configure(
        text=str(
            valeur_affichee
        ),
        fg=(
            theme["blanc"]
            if compteur > 0
            else theme["texte_faible"]
        ),
        bg=(
            theme["rouge"]
            if compteur > 0
            else theme["panneau_alt"]
        )
    )



def supprimer_rapport_carriere(
    identifiant
):
    """
    Supprime définitivement un rapport de la carrière active.
    """
    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    curseur.execute(
        """
        DELETE FROM rapports_carriere
        WHERE id = ?
        """,
        (
            int(
                identifiant
            ),
        )
    )

    connexion.commit()
    connexion.close()

    actualiser_badge_rapports()


def supprimer_tous_les_rapports_carriere():
    """
    Supprime tous les rapports de la carrière active uniquement.

    Comme chaque carrière possède sa propre base locale, cette opération
    ne touche jamais aux rapports d'une autre carrière.
    """
    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    curseur.execute(
        """
        DELETE FROM rapports_carriere
        """
    )

    connexion.commit()
    connexion.close()

    actualiser_badge_rapports()


def valider_rapport_carriere(
    identifiant
):
    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    curseur.execute(
        """
        UPDATE rapports_carriere
        SET valide = 1
        WHERE id = ?
        """,
        (
            int(
                identifiant
            ),
        )
    )

    connexion.commit()
    connexion.close()

    actualiser_badge_rapports()


def formater_date_jeu_rapport(texte):
    if not texte:
        return "DATE IN-GAME INCONNUE"

    for format_source in (
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d"
    ):
        try:
            date = datetime.strptime(
                texte,
                format_source
            )

            if " " in texte:
                return date.strftime(
                    "%d.%m.%Y - %H:%M"
                )

            return date.strftime(
                "%d.%m.%Y"
            )

        except ValueError:
            pass

    return str(
        texte
    )



# ============================================================
# MODELE DE REPARTITION ACTIF
# ============================================================

NIVEAUX_REPARTITION = (
    "TRÈS ÉLEVÉE",
    "ÉLEVÉE",
    "NORMALE",
    "FAIBLE",
    "TRÈS FAIBLE",
    "INDISPONIBLE"
)

# Les clés internes historiques sont conservées pour ne casser ni SQLite
# ni les presets JSON déjà créés. L'interface affiche des termes plus clairs.
NOMS_NIVEAUX_REPARTITION = {
    "TRÈS ÉLEVÉE": "CRITIQUE",
    "ÉLEVÉE": "FORTE",
    "NORMALE": "NORMALE",
    "FAIBLE": "FAIBLE",
    "TRÈS FAIBLE": "RARE",
    "INDISPONIBLE": "INDISPONIBLE"
}


def nom_affiche_niveau_repartition(
    niveau
):
    # La valeur interne française reste inchangée pour SQLite / presets.
    # Seul l'affichage suit la langue active.
    return t_priorite(
        niveau
    )


# Poids fixes du STANDARD.
# Ils représentent une FORCE DE RÉPARTITION, pas un stock physique.
# Le STANDARD historique varie donc par les niveaux attribués aux munitions,
# mois par mois, tandis que ces poids restent stables et lisibles.
QUANTITES_STANDARD_NIVEAUX = {
    "TRÈS ÉLEVÉE": 100.0,
    "ÉLEVÉE": 60.0,
    "NORMALE": 30.0,
    "FAIBLE": 15.0,
    "TRÈS FAIBLE": 5.0,
    "INDISPONIBLE": 0.0
}

LIMITES_NIVEAUX_REPARTITION = {
    "TRÈS ÉLEVÉE": 1,
    "ÉLEVÉE": 2
}


def compter_affectations_par_niveau(
    affectations,
    ignorer_munition=None
):
    compteurs = {
        niveau: 0
        for niveau in NIVEAUX_REPARTITION
    }

    for munition, niveau in affectations.items():
        if (
            ignorer_munition is not None
            and munition == ignorer_munition
        ):
            continue

        if niveau in compteurs:
            compteurs[
                niveau
            ] += 1

    return compteurs


def niveau_repartition_disponible(
    niveau,
    affectations,
    ignorer_munition=None
):
    """
    Indique si une nouvelle munition peut encore être placée dans ce niveau.

    Les niveaux sans quota restent toujours disponibles.
    """
    maximum = LIMITES_NIVEAUX_REPARTITION.get(
        niveau
    )

    if maximum is None:
        return True

    compteurs = compter_affectations_par_niveau(
        affectations,
        ignorer_munition=ignorer_munition
    )

    return (
        compteurs.get(
            niveau,
            0
        )
        < maximum
    )


def normaliser_affectations_selon_limites(
    affectations,
    scores=None
):
    """
    Rend une répartition STRICTEMENT valide.

    Si un niveau limité est surchargé, les affectations excédentaires
    sont rétrogradées vers le meilleur niveau inférieur encore disponible.

    `scores` permet de conserver dans les niveaux rares les munitions
    les plus importantes (utile pour le STANDARD historique).
    """
    affectations = dict(
        affectations
    )

    scores = dict(
        scores
        or {}
    )

    resultat = {}

    compteurs = {
        niveau: 0
        for niveau in NIVEAUX_REPARTITION
    }

    index_niveaux = {
        niveau: index
        for index, niveau
        in enumerate(
            NIVEAUX_REPARTITION
        )
    }

    groupes = {
        niveau: []
        for niveau in NIVEAUX_REPARTITION
    }

    for munition, niveau in affectations.items():
        if niveau not in groupes:
            niveau = "NORMALE"

        groupes[
            niveau
        ].append(
            munition
        )

    for niveau in NIVEAUX_REPARTITION:
        munitions = groupes[
            niveau
        ]

        # Les armes avec le score historique le plus élevé gardent
        # en priorité les places rares.
        munitions.sort(
            key=lambda munition: (
                -float(
                    scores.get(
                        munition,
                        0.0
                    )
                ),
                str(
                    munition
                ).casefold()
            )
        )

        for munition in munitions:
            depart = index_niveaux[
                niveau
            ]

            niveau_final = "INDISPONIBLE"

            for candidat in NIVEAUX_REPARTITION[
                depart:
            ]:
                maximum = LIMITES_NIVEAUX_REPARTITION.get(
                    candidat
                )

                if (
                    maximum is None
                    or compteurs[
                        candidat
                    ] < maximum
                ):
                    niveau_final = candidat
                    break

            resultat[
                munition
            ] = niveau_final

            compteurs[
                niveau_final
            ] += 1

    return resultat


def assurer_migration_profils_repartition():
    """
    Migration UNIQUE de l'ancien modèle PERSONNALISE.

    Important : une fois la migration effectuée, elle ne doit jamais
    recréer un profil après que l'utilisateur a supprimé son dernier
    modèle personnalisé.
    """
    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )
        curseur = connexion.cursor()

        curseur.execute(
            """
            CREATE TABLE IF NOT EXISTS profils_repartition (
                modele TEXT PRIMARY KEY,
                nom TEXT NOT NULL,
                date_creation TEXT NOT NULL
            )
            """
        )

        # Marqueur persistant : la migration legacy n'est autorisée
        # qu'une seule fois dans la vie de cette base de carrière.
        ligne_migration = curseur.execute(
            """
            SELECT valeur
            FROM preferences_repartition
            WHERE cle = 'migration_profils_repartition_v1'
            LIMIT 1
            """
        ).fetchone()

        migration_deja_effectuee = (
            ligne_migration is not None
            and str(ligne_migration[0]) == '1'
        )

        if not migration_deja_effectuee:
            nombre = curseur.execute(
                """
                SELECT COUNT(*)
                FROM profils_repartition
                """
            ).fetchone()[0]

            if int(nombre) == 0:
                ligne_nom = curseur.execute(
                    """
                    SELECT valeur
                    FROM preferences_repartition
                    WHERE cle = 'nom_modele_personnalise'
                    LIMIT 1
                    """
                ).fetchone()

                nom_ancien = str(
                    ligne_nom[0]
                    if ligne_nom
                    else ''
                ).strip()

                if nom_ancien:
                    curseur.execute(
                        """
                        INSERT OR IGNORE INTO profils_repartition (
                            modele,
                            nom,
                            date_creation
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            'PERSONNALISE',
                            nom_ancien,
                            datetime.now().strftime(
                                '%Y-%m-%d %H:%M:%S'
                            )
                        )
                    )

                    curseur.execute(
                        """
                        INSERT INTO preferences_repartition (
                            cle,
                            valeur
                        )
                        VALUES ('modele_repartition_actif', 'PERSONNALISE')
                        ON CONFLICT(cle)
                        DO NOTHING
                        """
                    )

            # Même s'il n'y avait rien à migrer, on marque l'étape
            # comme terminée afin qu'elle ne puisse jamais ressusciter
            # un profil supprimé plus tard.
            curseur.execute(
                """
                INSERT INTO preferences_repartition (
                    cle,
                    valeur
                )
                VALUES ('migration_profils_repartition_v1', '1')
                ON CONFLICT(cle)
                DO UPDATE SET valeur = '1'
                """
            )

        connexion.commit()
        connexion.close()

    except sqlite3.Error:
        pass


def lister_profils_repartition_personnalises():
    assurer_migration_profils_repartition()

    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )
        curseur = connexion.cursor()

        lignes = curseur.execute(
            """
            SELECT
                modele,
                nom
            FROM profils_repartition
            ORDER BY
                date_creation ASC,
                nom COLLATE NOCASE ASC
            """
        ).fetchall()

        connexion.close()

        return [
            (
                str(modele),
                str(nom)
            )
            for modele, nom in lignes
        ]

    except sqlite3.Error:
        return []


def cle_modele_repartition_actif():
    assurer_migration_profils_repartition()

    cle = lire_preference_repartition(
        "modele_repartition_actif",
        ""
    ).strip()

    if not cle:
        ancien_mode = lire_preference_repartition(
            "mode_repartition",
            "STANDARD"
        ).upper()

        if ancien_mode == "PERSONNALISE":
            profils = lister_profils_repartition_personnalises()
            if profils:
                cle = profils[0][0]

    if cle == "STANDARD":
        return "STANDARD"

    profils = {
        identifiant
        for identifiant, nom in lister_profils_repartition_personnalises()
    }

    if cle in profils:
        return cle

    return "STANDARD"


def definir_modele_repartition_actif(
    modele
):
    if modele != "STANDARD":
        profils = {
            identifiant
            for identifiant, nom in lister_profils_repartition_personnalises()
        }

        if modele not in profils:
            modele = "STANDARD"

    ecrire_preference_repartition(
        "modele_repartition_actif",
        modele
    )

    # Compatibilité avec les anciennes fonctions / bases.
    ecrire_preference_repartition(
        "mode_repartition",
        (
            "STANDARD"
            if modele == "STANDARD"
            else "PERSONNALISE"
        )
    )


def cle_modele_personnalise():
    cle = cle_modele_repartition_actif()

    if cle != "STANDARD":
        return cle

    profils = lister_profils_repartition_personnalises()

    if profils:
        return profils[0][0]

    return "PERSONNALISE"


def existe_modele_personnalise():
    return bool(
        lister_profils_repartition_personnalises()
    )


def nom_profil_repartition(
    modele
):
    if modele == "STANDARD":
        return "STANDARD"

    for identifiant, nom in lister_profils_repartition_personnalises():
        if identifiant == modele:
            return nom

    return "MODÈLE PERSONNALISÉ"


def nom_modele_personnalise_actuel():
    cle = cle_modele_repartition_actif()

    if cle != "STANDARD":
        return nom_profil_repartition(
            cle
        )

    profils = lister_profils_repartition_personnalises()

    if profils:
        return profils[0][1]

    return "MODÈLE PERSONNALISÉ"


VERSION_FORMAT_PRESET = 1


def dossier_presets_carriere():
    """
    Dossier portable propre à la carrière courante :

    careers/<career_id>/presets/

    La base SQLite reste :
    careers/<career_id>.db
    """
    try:
        nom_local = FICHIER_BASE.stem
    except Exception:
        nom_local = "carriere"

    dossier = (
        DOSSIER_CARRIERES
        / nom_local
        / "presets"
    )

    dossier.mkdir(
        parents=True,
        exist_ok=True
    )

    return dossier


def nom_fichier_preset_portable(
    nom,
    modele
):
    propre = re.sub(
        r'[^A-Za-z0-9À-ÿ _.-]',
        "_",
        str(
            nom
            or "Modele"
        )
    ).strip(
        " ._"
    )

    propre = re.sub(
        r"\s+",
        "_",
        propre
    )

    if not propre:
        propre = "Modele"

    suffixe = re.sub(
        r"[^A-Za-z0-9_-]",
        "",
        str(
            modele
        )
    )[-12:]

    if suffixe:
        return f"{propre}__{suffixe}.json"

    return f"{propre}.json"


def construire_preset_portable(
    modele
):
    """
    Extrait l'intégralité d'un modèle personnalisé.

    Le fichier contient :
    - métadonnées ;
    - quantités legacy ;
    - quantités mensuelles ;
    - toutes les affectations mensuelles, tous avions confondus.
    """
    if (
        not modele
        or modele == "STANDARD"
    ):
        raise ValueError(
            t("model.validation.standard_export")
        )

    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    profil = curseur.execute(
        """
        SELECT
            nom,
            date_creation
        FROM profils_repartition
        WHERE modele = ?
        LIMIT 1
        """,
        (
            modele,
        )
    ).fetchone()

    if profil is None:
        connexion.close()
        raise ValueError(
            t("model.validation.custom_missing")
        )

    niveaux_globaux = [
        {
            "niveau": str(
                niveau
            ),
            "quantite_reference": float(
                quantite
            )
        }
        for niveau, quantite
        in curseur.execute(
            """
            SELECT
                niveau,
                quantite_reference
            FROM niveaux_repartition
            WHERE modele = ?
            ORDER BY niveau
            """,
            (
                modele,
            )
        ).fetchall()
    ]

    niveaux_periodes = [
        {
            "annee": int(
                annee
            ),
            "mois": int(
                mois
            ),
            "niveau": str(
                niveau
            ),
            "quantite_reference": float(
                quantite
            )
        }
        for annee, mois, niveau, quantite
        in curseur.execute(
            """
            SELECT
                annee,
                mois,
                niveau,
                quantite_reference
            FROM niveaux_repartition_periodes
            WHERE modele = ?
            ORDER BY
                annee,
                mois,
                niveau
            """,
            (
                modele,
            )
        ).fetchall()
    ]

    affectations = [
        {
            "annee": int(
                annee
            ),
            "mois": int(
                mois
            ),
            "avion": str(
                avion
            ),
            "munition": str(
                munition
            ),
            "niveau": str(
                niveau
            )
        }
        for annee, mois, avion, munition, niveau
        in curseur.execute(
            """
            SELECT
                annee,
                mois,
                avion,
                munition,
                niveau
            FROM affectations_repartition
            WHERE modele = ?
            ORDER BY
                annee,
                mois,
                avion,
                munition
            """,
            (
                modele,
            )
        ).fetchall()
    ]

    connexion.close()

    return {
        "format": "IL2_KOREA_GESTION_STOCK_PRESET",
        "schema_version": VERSION_FORMAT_PRESET,
        "application_version": VERSION_APPLICATION,
        "exporte_le": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "preset": {
            "id_source": str(
                modele
            ),
            "nom": str(
                profil[0]
            ),
            "date_creation": str(
                profil[1]
            ),
            "niveaux_globaux": niveaux_globaux,
            "niveaux_periodes": niveaux_periodes,
            "affectations": affectations
        }
    }


def exporter_preset_portable(
    modele
):
    """
    Sauvegarde automatiquement le preset dans le dossier de la carrière.
    Écriture atomique via .tmp puis remplacement.
    """
    donnees = construire_preset_portable(
        modele
    )

    nom = donnees[
        "preset"
    ][
        "nom"
    ]

    destination = (
        dossier_presets_carriere()
        / nom_fichier_preset_portable(
            nom,
            modele
        )
    )

    temporaire = destination.with_suffix(
        ".json.tmp"
    )

    with open(
        temporaire,
        "w",
        encoding="utf-8"
    ) as fichier:
        json.dump(
            donnees,
            fichier,
            ensure_ascii=False,
            indent=2
        )

        fichier.flush()

        try:
            os.fsync(
                fichier.fileno()
            )
        except OSError:
            pass

    temporaire.replace(
        destination
    )

    return destination


def exporter_preset_vers(
    modele,
    destination
):
    """
    Exporte le preset actif vers l'emplacement choisi par l'utilisateur.

    Le fichier est écrit de manière atomique :
    destination.tmp -> destination
    """
    destination = Path(
        destination
    )

    if destination.suffix.lower() != ".json":
        destination = destination.with_suffix(
            ".json"
        )

    donnees = construire_preset_portable(
        modele
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporaire = destination.with_suffix(
        destination.suffix + ".tmp"
    )

    with open(
        temporaire,
        "w",
        encoding="utf-8"
    ) as fichier:
        json.dump(
            donnees,
            fichier,
            ensure_ascii=False,
            indent=2
        )

        fichier.flush()

        try:
            os.fsync(
                fichier.fileno()
            )
        except OSError:
            pass

    temporaire.replace(
        destination
    )

    return destination



def valider_preset_portable(
    donnees
):
    if not isinstance(
        donnees,
        dict
    ):
        raise ValueError(
            t("model.validation.json_object")
        )

    if donnees.get(
        "format"
    ) != "IL2_KOREA_GESTION_STOCK_PRESET":
        raise ValueError(
            t("model.validation.format")
        )

    version = donnees.get(
        "schema_version"
    )

    if version != VERSION_FORMAT_PRESET:
        raise ValueError(
            t("model.validation.version", version=version)
        )

    preset = donnees.get(
        "preset"
    )

    if not isinstance(
        preset,
        dict
    ):
        raise ValueError(
            t("model.validation.section")
        )

    nom = str(
        preset.get(
            "nom",
            ""
        )
    ).strip()

    if not nom:
        raise ValueError(
            t("model.validation.name")
        )

    niveaux_valides = set(
        NIVEAUX_REPARTITION
    )

    for ligne in preset.get(
        "niveaux_globaux",
        []
    ):
        if not isinstance(
            ligne,
            dict
        ):
            raise ValueError(
                t("model.validation.global_quantity")
            )

        niveau = str(
            ligne.get(
                "niveau",
                ""
            )
        )

        if niveau not in niveaux_valides:
            raise ValueError(
                t("model.validation.unknown_level", level=t_priorite(niveau))
            )

        quantite = float(
            ligne.get(
                "quantite_reference",
                0
            )
        )

        if quantite < 0:
            raise ValueError(
                t("model.validation.negative_reference")
            )

    for ligne in preset.get(
        "niveaux_periodes",
        []
    ):
        if not isinstance(
            ligne,
            dict
        ):
            raise ValueError(
                t("model.validation.period_quantity")
            )

        annee = int(
            ligne.get(
                "annee"
            )
        )

        mois = int(
            ligne.get(
                "mois"
            )
        )

        niveau = str(
            ligne.get(
                "niveau",
                ""
            )
        )

        quantite = float(
            ligne.get(
                "quantite_reference",
                0
            )
        )

        if not (
            1 <= mois <= 12
        ):
            raise ValueError(
                t("model.validation.invalid_month", month=mois)
            )

        if not (
            1900 <= annee <= 2100
        ):
            raise ValueError(
                t("model.validation.invalid_year", year=annee)
            )

        if niveau not in niveaux_valides:
            raise ValueError(
                t("model.validation.unknown_level", level=t_priorite(niveau))
            )

        if quantite < 0:
            raise ValueError(
                t("model.validation.negative_monthly")
            )

    avions_valides = set(
        AVIONS_EMPORTS.keys()
    )

    munitions_valides = set(
        MUNITIONS.keys()
    )

    for ligne in preset.get(
        "affectations",
        []
    ):
        if not isinstance(
            ligne,
            dict
        ):
            raise ValueError(
                t("model.validation.assignment")
            )

        annee = int(
            ligne.get(
                "annee"
            )
        )

        mois = int(
            ligne.get(
                "mois"
            )
        )

        avion = str(
            ligne.get(
                "avion",
                ""
            )
        )

        munition = str(
            ligne.get(
                "munition",
                ""
            )
        )

        niveau = str(
            ligne.get(
                "niveau",
                ""
            )
        )

        if not (
            1 <= mois <= 12
        ):
            raise ValueError(
                t("model.validation.assignment_month", month=mois)
            )

        if not (
            1900 <= annee <= 2100
        ):
            raise ValueError(
                t("model.validation.assignment_year", year=annee)
            )

        if avion not in avions_valides:
            raise ValueError(
                t("model.validation.unknown_aircraft", aircraft=avion)
            )

        if munition not in munitions_valides:
            raise ValueError(
                t("model.validation.unknown_ammo", munition=t_munition(munition))
            )

        if munition not in AVIONS_EMPORTS.get(
            avion,
            []
        ):
            raise ValueError(
                t("model.validation.incompatible", munition=t_munition(munition), aircraft=avion)
            )

        if niveau not in niveaux_valides:
            raise ValueError(
                t("model.validation.unknown_level", level=t_priorite(niveau))
            )

    return preset


def nom_importe_unique(
    nom
):
    existants = {
        str(
            nom_existant
        ).casefold()
        for identifiant, nom_existant
        in lister_profils_repartition_personnalises()
    }

    base = str(
        nom
        or "PRESET IMPORTÉ"
    ).strip()

    if base.casefold() not in existants:
        return base

    numero = 2

    while True:
        candidat = f"{base} ({numero})"

        if candidat.casefold() not in existants:
            return candidat

        numero += 1


def importer_preset_portable(
    chemin
):
    """
    Importe un preset comme NOUVEAU modèle local.

    L'id source du fichier n'est jamais réutilisé, ce qui évite
    les collisions entre carrières / utilisateurs.
    """
    chemin = Path(
        chemin
    )

    with open(
        chemin,
        "r",
        encoding="utf-8"
    ) as fichier:
        donnees = json.load(
            fichier
        )

    preset = valider_preset_portable(
        donnees
    )

    nouveau_modele = (
        "MODELE_"
        + datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )
    )

    nouveau_nom = nom_importe_unique(
        preset[
            "nom"
        ]
    )

    # Regroupe et normalise les affectations importées période par période.
    affectations_importees = preset.get(
        "affectations",
        []
    )

    groupes_affectations = {}

    for ligne in affectations_importees:
        cle_periode = (
            int(
                ligne[
                    "annee"
                ]
            ),
            int(
                ligne[
                    "mois"
                ]
            ),
            str(
                ligne[
                    "avion"
                ]
            )
        )

        groupes_affectations.setdefault(
            cle_periode,
            {}
        )[
            str(
                ligne[
                    "munition"
                ]
            )
        ] = str(
            ligne[
                "niveau"
            ]
        )

    affectations_normalisees = []

    for (
        annee,
        mois,
        avion
    ), affectations in groupes_affectations.items():
        valides = normaliser_affectations_selon_limites(
            affectations
        )

        for munition, niveau in valides.items():
            affectations_normalisees.append(
                {
                    "annee": annee,
                    "mois": mois,
                    "avion": avion,
                    "munition": munition,
                    "niveau": niveau
                }
            )

    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    try:
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        curseur.execute(
            """
            INSERT INTO profils_repartition (
                modele,
                nom,
                date_creation
            )
            VALUES (?, ?, ?)
            """,
            (
                nouveau_modele,
                nouveau_nom,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )

        for ligne in preset.get(
            "niveaux_globaux",
            []
        ):
            curseur.execute(
                """
                INSERT INTO niveaux_repartition (
                    modele,
                    niveau,
                    quantite_reference
                )
                VALUES (?, ?, ?)
                ON CONFLICT(
                    modele,
                    niveau
                )
                DO UPDATE SET
                    quantite_reference = excluded.quantite_reference
                """,
                (
                    nouveau_modele,
                    str(
                        ligne[
                            "niveau"
                        ]
                    ),
                    float(
                        ligne[
                            "quantite_reference"
                        ]
                    )
                )
            )

        for ligne in preset.get(
            "niveaux_periodes",
            []
        ):
            curseur.execute(
                """
                INSERT INTO niveaux_repartition_periodes (
                    modele,
                    annee,
                    mois,
                    niveau,
                    quantite_reference
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    nouveau_modele,
                    int(
                        ligne[
                            "annee"
                        ]
                    ),
                    int(
                        ligne[
                            "mois"
                        ]
                    ),
                    str(
                        ligne[
                            "niveau"
                        ]
                    ),
                    float(
                        ligne[
                            "quantite_reference"
                        ]
                    )
                )
            )

        for ligne in affectations_normalisees:
            curseur.execute(
                """
                INSERT INTO affectations_repartition (
                    modele,
                    annee,
                    mois,
                    avion,
                    munition,
                    niveau
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    nouveau_modele,
                    int(
                        ligne[
                            "annee"
                        ]
                    ),
                    int(
                        ligne[
                            "mois"
                        ]
                    ),
                    str(
                        ligne[
                            "avion"
                        ]
                    ),
                    str(
                        ligne[
                            "munition"
                        ]
                    ),
                    str(
                        ligne[
                            "niveau"
                        ]
                    )
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
                ?
            )
            ON CONFLICT(cle)
            DO UPDATE SET
                valeur = excluded.valeur
            """,
            (
                nouveau_modele,
            )
        )

        curseur.execute(
            """
            INSERT INTO preferences_repartition (
                cle,
                valeur
            )
            VALUES (
                'mode_repartition',
                'PERSONNALISE'
            )
            ON CONFLICT(cle)
            DO UPDATE SET
                valeur = 'PERSONNALISE'
            """
        )

        connexion.commit()

    except Exception:
        connexion.rollback()
        connexion.close()
        raise

    connexion.close()

    # Copie normalisée dans le dossier de la carrière.
    exporter_preset_portable(
        nouveau_modele
    )

    return (
        nouveau_modele,
        nouveau_nom
    )



def creer_nouveau_modele_repartition():
    assurer_migration_profils_repartition()

    profils = lister_profils_repartition_personnalises()

    numero = len(profils) + 1
    noms_existants = {
        nom.upper()
        for identifiant, nom in profils
    }

    while True:
        nom = f"MODÈLE {numero}"

        if nom.upper() not in noms_existants:
            break

        numero += 1

    modele = (
        "MODELE_"
        + datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )
    )

    connexion = sqlite3.connect(
        FICHIER_BASE
    )
    curseur = connexion.cursor()

    curseur.execute(
        """
        INSERT INTO profils_repartition (
            modele,
            nom,
            date_creation
        )
        VALUES (?, ?, ?)
        """,
        (
            modele,
            nom,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    )

    connexion.commit()
    connexion.close()

    sauvegarder_quantites_niveaux(
        modele,
        QUANTITES_STANDARD_NIVEAUX
    )

    definir_modele_repartition_actif(
        modele
    )

    return (
        modele,
        nom
    )


def renommer_modele_repartition(
    modele,
    nouveau_nom
):
    if modele == "STANDARD":
        return

    nouveau_nom = str(
        nouveau_nom
        or ""
    ).strip()

    if not nouveau_nom:
        nouveau_nom = "MODÈLE PERSONNALISÉ"

    connexion = sqlite3.connect(
        FICHIER_BASE
    )
    curseur = connexion.cursor()

    curseur.execute(
        """
        UPDATE profils_repartition
        SET nom = ?
        WHERE modele = ?
        """,
        (
            nouveau_nom,
            modele
        )
    )

    connexion.commit()
    connexion.close()

    # Compatibilité ancienne préférence : garde le nom du profil actif.
    ecrire_preference_repartition(
        "nom_modele_personnalise",
        nouveau_nom
    )


def supprimer_modele_repartition(
    modele
):
    """
    Supprime définitivement un modèle personnalisé.

    STANDARD est intouchable.
    La suppression du dernier profil personnalisé est autorisée et ne
    provoque plus aucune recréation automatique du profil legacy.
    """
    if (
        not modele
        or modele == 'STANDARD'
    ):
        return False

    # On lit directement la base sans passer par une fonction susceptible
    # de déclencher la migration legacy.
    connexion = sqlite3.connect(
        FICHIER_BASE
    )
    curseur = connexion.cursor()

    try:
        existe = curseur.execute(
            """
            SELECT 1
            FROM profils_repartition
            WHERE modele = ?
            LIMIT 1
            """,
            (
                modele,
            )
        ).fetchone()

        if not existe:
            connexion.close()
            return False

        ligne_active = curseur.execute(
            """
            SELECT valeur
            FROM preferences_repartition
            WHERE cle = 'modele_repartition_actif'
            LIMIT 1
            """
        ).fetchone()

        etait_actif = (
            ligne_active is not None
            and str(ligne_active[0]) == str(modele)
        )

        curseur.execute(
            'BEGIN IMMEDIATE'
        )

        curseur.execute(
            """
            DELETE FROM affectations_repartition
            WHERE modele = ?
            """,
            (
                modele,
            )
        )

        curseur.execute(
            """
            DELETE FROM niveaux_repartition
            WHERE modele = ?
            """,
            (
                modele,
            )
        )

        curseur.execute(
            """
            DELETE FROM niveaux_repartition_periodes
            WHERE modele = ?
            """,
            (
                modele,
            )
        )

        curseur.execute(
            """
            DELETE FROM profils_repartition
            WHERE modele = ?
            """,
            (
                modele,
            )
        )

        # Le marqueur reste à 1 quoi qu'il arrive : l'ancien système
        # PERSONNALISE ne doit jamais être remigré après une suppression.
        curseur.execute(
            """
            INSERT INTO preferences_repartition (
                cle,
                valeur
            )
            VALUES ('migration_profils_repartition_v1', '1')
            ON CONFLICT(cle)
            DO UPDATE SET valeur = '1'
            """
        )

        if etait_actif:
            curseur.execute(
                """
                INSERT INTO preferences_repartition (
                    cle,
                    valeur
                )
                VALUES ('modele_repartition_actif', 'STANDARD')
                ON CONFLICT(cle)
                DO UPDATE SET valeur = 'STANDARD'
                """
            )

            curseur.execute(
                """
                INSERT INTO preferences_repartition (
                    cle,
                    valeur
                )
                VALUES ('mode_repartition', 'STANDARD')
                ON CONFLICT(cle)
                DO UPDATE SET valeur = 'STANDARD'
                """
            )

        restant = curseur.execute(
            """
            SELECT COUNT(*)
            FROM profils_repartition
            """
        ).fetchone()[0]

        if int(restant) == 0:
            # Nettoyage de l'ancien nom sans jamais relancer sa migration.
            curseur.execute(
                """
                INSERT INTO preferences_repartition (
                    cle,
                    valeur
                )
                VALUES ('nom_modele_personnalise', '')
                ON CONFLICT(cle)
                DO UPDATE SET valeur = ''
                """
            )

            curseur.execute(
                """
                INSERT INTO preferences_repartition (
                    cle,
                    valeur
                )
                VALUES ('modele_repartition_actif', 'STANDARD')
                ON CONFLICT(cle)
                DO UPDATE SET valeur = 'STANDARD'
                """
            )

            curseur.execute(
                """
                INSERT INTO preferences_repartition (
                    cle,
                    valeur
                )
                VALUES ('mode_repartition', 'STANDARD')
                ON CONFLICT(cle)
                DO UPDATE SET valeur = 'STANDARD'
                """
            )

        connexion.commit()

        # Vérification forte : le profil doit avoir réellement disparu.
        verification = curseur.execute(
            """
            SELECT 1
            FROM profils_repartition
            WHERE modele = ?
            LIMIT 1
            """,
            (
                modele,
            )
        ).fetchone()

        connexion.close()

        return verification is None

    except sqlite3.Error:
        try:
            connexion.rollback()
        except Exception:
            pass

        connexion.close()
        return False


def obtenir_quantites_niveaux(
    modele
):
    """
    Quantités de référence utilisées pour calculer les parts relatives.

    STANDARD :
        valeurs internes de référence.

    PERSONNALISE :
        valeurs sauvegardées par l'utilisateur, avec fallback STANDARD.
    """
    resultat = dict(
        QUANTITES_STANDARD_NIVEAUX
    )

    if modele == "STANDARD":
        return resultat

    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        curseur = connexion.cursor()

        lignes = curseur.execute(
            """
            SELECT
                niveau,
                quantite_reference
            FROM niveaux_repartition
            WHERE modele = ?
            """,
            (
                modele,
            )
        ).fetchall()

        connexion.close()

        for niveau, quantite in lignes:
            if niveau in resultat:
                resultat[
                    niveau
                ] = max(
                    0.0,
                    float(
                        quantite
                    )
                )

    except sqlite3.Error:
        pass

    resultat[
        "INDISPONIBLE"
    ] = 0.0

    return resultat


def obtenir_quantites_niveaux_periode(
    modele,
    annee,
    mois
):
    """
    Quantités de référence d'un modèle personnalisé pour une période précise.

    Fallback :
    - anciennes quantités globales du modèle ;
    - puis valeurs STANDARD intégrées.
    """
    resultat = obtenir_quantites_niveaux(
        modele
    )

    if modele == "STANDARD":
        return resultat

    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        curseur = connexion.cursor()

        lignes = curseur.execute(
            """
            SELECT
                niveau,
                quantite_reference
            FROM niveaux_repartition_periodes
            WHERE
                modele = ?
                AND annee = ?
                AND mois = ?
            """,
            (
                modele,
                int(
                    annee
                ),
                int(
                    mois
                )
            )
        ).fetchall()

        connexion.close()

        for niveau, quantite in lignes:
            if niveau in resultat:
                resultat[
                    niveau
                ] = max(
                    0.0,
                    float(
                        quantite
                    )
                )

    except sqlite3.Error:
        pass

    resultat[
        "INDISPONIBLE"
    ] = 0.0

    return resultat


def sauvegarder_quantites_niveaux_periode(
    modele,
    annee,
    mois,
    quantites,
    connexion=None
):
    """
    Sauvegarde les quantités de référence pour UN mois du modèle.

    Si une connexion est fournie, elle est réutilisée pour permettre
    l'enregistrement atomique d'un modèle complet.
    """
    connexion_interne = (
        connexion is None
    )

    if connexion_interne:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )

    curseur = connexion.cursor()

    for niveau in NIVEAUX_REPARTITION:
        valeur = max(
            0.0,
            float(
                quantites.get(
                    niveau,
                    0.0
                )
            )
        )

        if niveau == "INDISPONIBLE":
            valeur = 0.0

        curseur.execute(
            """
            INSERT INTO niveaux_repartition_periodes (
                modele,
                annee,
                mois,
                niveau,
                quantite_reference
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(
                modele,
                annee,
                mois,
                niveau
            )
            DO UPDATE SET
                quantite_reference = excluded.quantite_reference
            """,
            (
                modele,
                int(
                    annee
                ),
                int(
                    mois
                ),
                niveau,
                valeur
            )
        )

    if connexion_interne:
        connexion.commit()
        connexion.close()



def sauvegarder_quantites_niveaux(
    modele,
    quantites
):
    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    for niveau in NIVEAUX_REPARTITION:
        valeur = max(
            0.0,
            float(
                quantites.get(
                    niveau,
                    0.0
                )
            )
        )

        if niveau == "INDISPONIBLE":
            valeur = 0.0

        curseur.execute(
            """
            INSERT INTO niveaux_repartition (
                modele,
                niveau,
                quantite_reference
            )
            VALUES (?, ?, ?)
            ON CONFLICT(
                modele,
                niveau
            )
            DO UPDATE SET
                quantite_reference = excluded.quantite_reference
            """,
            (
                modele,
                niveau,
                valeur
            )
        )

    connexion.commit()
    connexion.close()



VERSION_STANDARD_HISTORIQUE = "KOREA_STANDARD_HIST_V1"

SOURCES_STANDARD_HISTORIQUE = (
    "USAF Historical Division, USAF Tactical Operations WWII and Korean War "
    "with Statistical Tables (1962); Robert F. Futrell, The United States "
    "Air Force in Korea 1950-1953; USAF, The USAF in Korea: A Chronology "
    "1950-1953; Combat Support in Korea; Naval History and Heritage Command "
    "Korean War Chronology; AFHRA/USAF historical studies."
)


def _arrondir_reference_historique(
    valeur,
    pas=25
):
    valeur = max(
        0.0,
        float(
            valeur
        )
    )

    if valeur <= 0:
        return 0.0

    return float(
        int(
            round(
                valeur
                / float(
                    pas
                )
            )
        )
        * int(
            pas
        )
    )


def _intensite_operationnelle_korea(
    annee,
    mois
):
    """
    Indice mensuel reconstruit à partir des grandes phases documentées
    de la guerre aérienne en Corée.

    Cet indice n'est PAS présenté comme un registre comptable de dépôt.
    Il sert à transformer les quantités de référence du modèle STANDARD
    en fonction de l'intensité réelle des opérations du mois concerné.
    """
    annee = int(
        annee
    )
    mois = int(
        mois
    )

    profils = {
        1950: {
            1: 0.30, 2: 0.30, 3: 0.30, 4: 0.30, 5: 0.30,
            6: 0.75, 7: 1.35, 8: 1.50, 9: 1.45, 10: 1.25,
            11: 1.40, 12: 1.50
        },
        1951: {
            1: 1.55, 2: 1.45, 3: 1.35, 4: 1.30, 5: 1.30,
            6: 1.25, 7: 1.05, 8: 1.00, 9: 1.05, 10: 1.10,
            11: 1.05, 12: 1.00
        },
        1952: {
            1: 1.00, 2: 1.00, 3: 1.05, 4: 1.10, 5: 1.40,
            6: 1.50, 7: 1.40, 8: 1.30, 9: 1.30, 10: 1.20,
            11: 1.15, 12: 1.15
        },
        1953: {
            1: 1.15, 2: 1.20, 3: 1.25, 4: 1.30, 5: 1.45,
            6: 1.50, 7: 1.55, 8: 0.08, 9: 0.05, 10: 0.05,
            11: 0.05, 12: 0.05
        }
    }

    return float(
        profils.get(
            annee,
            {}
        ).get(
            mois,
            1.0
        )
    )


def _facteur_activite_avion_standard(
    avion,
    annee,
    mois
):
    """
    Facteur de présence / rôle historique de l'appareil dans le théâtre.

    Il évite par exemple de donner un stock offensif normal au F-84E
    avant son arrivée en combat en décembre 1950, ou au F-86A durant
    sa période principalement consacrée à la supériorité aérienne.
    """
    cle = (
        int(
            annee
        ),
        int(
            mois
        )
    )

    if avion == "F-84E":
        if cle < (1950, 12):
            return 0.0
        return 1.05

    if avion == "F-86A-5":
        if cle < (1950, 12):
            return 0.0

        if cle < (1952, 5):
            return 0.38

        if cle < (1953, 1):
            return 0.80

        return 1.10

    if avion == "F-80C-10":
        if cle >= (1953, 1):
            return 0.65
        return 1.00

    if avion == "F-51D":
        if cle >= (1953, 1):
            return 0.72
        return 1.05

    if avion == "IL-10":
        if cle < (1950, 6):
            return 0.85

        if cle <= (1950, 8):
            return 1.25

        if cle <= (1950, 10):
            return 0.65

        if cle <= (1951, 3):
            return 0.35

        return 0.18

    if avion == "MiG-15bis":
        if cle < (1950, 11):
            return 0.0

        # Les MiG-15 furent employés avant tout en défense / interception.
        # Le potentiel bombardement existait, mais l'emploi air-sol fut rare.
        return 0.28

    if avion in (
        "Yak-9P",
        "La-11"
    ):
        return 0.20

    return 1.0


def quantites_standard_historiques_periode(
    annee,
    mois,
    avion
):
    """
    Poids fixes du preset STANDARD.

    L'historicité mensuelle est portée par le NIVEAU attribué à chaque
    munition (CRITIQUE / FORTE / NORMALE / FAIBLE / RARE / INDISPONIBLE),
    pas par une pseudo-quantité physique.

    Ainsi :
    - CRITIQUE vaut toujours 100 ;
    - FORTE vaut toujours 60 ;
    - etc.

    Le mois et l'année restent dans la signature pour conserver une API
    stable et permettre au STANDARD de charger ses priorités historiques.
    """
    return dict(
        QUANTITES_STANDARD_NIVEAUX
    )



def profil_standard_historique_munition(
    annee,
    mois,
    avion,
    munition
):
    """
    Niveau + quantité de référence d'une munition pour une période précise.

    Cette fonction introduit les différences historiques majeures :
    - priorité très forte aux HVAR / 500 lb sur les fighter-bombers US ;
    - pic napalm durant les phases de CAS 1950-début 1951 ;
    - ATAR surtout pertinent pendant la crise antichar de 1950 ;
    - montée relative des bombes lourdes durant les campagnes
      d'interdiction / pression 1952-1953 ;
    - rôle air-sol très limité du MiG-15 ;
    - effondrement rapide de l'activité IL-10 nord-coréenne après 1950.
    """
    annee = int(
        annee
    )
    mois = int(
        mois
    )
    cle = (
        annee,
        mois
    )

    nom = str(
        munition
    ).lower()

    quantites = quantites_standard_historiques_periode(
        annee,
        mois,
        avion
    )

    niveau = "NORMALE"
    modificateur = 1.0

    # --------------------------------------------------------
    # APPAREILS US
    # --------------------------------------------------------
    if avion in (
        "F-51D",
        "F-80C-10",
        "F-84E",
        "F-86A-5"
    ):
        # Avion absent / quasiment absent du rôle historique correspondant.
        if _facteur_activite_avion_standard(
            avion,
            annee,
            mois
        ) <= 0.0:
            return {
                "niveau": "INDISPONIBLE",
                "quantite_reference": 0.0,
                "statut_historique": "HISTORIQUE_RECONSTRUIT",
                "source": SOURCES_STANDARD_HISTORIQUE
            }

        # HVAR standard : arme de base très utilisée sur fighter-bombers.
        if "hvar" in nom and "semi-perforante" not in nom:
            niveau = "ÉLEVÉE"

            if (
                (1950, 7) <= cle <= (1951, 6)
                or (1952, 5) <= cle <= (1952, 9)
            ):
                niveau = "TRÈS ÉLEVÉE"

            if avion == "F-86A-5" and cle < (1952, 5):
                niveau = "TRÈS FAIBLE"

            if avion == "F-86A-5" and cle >= (1953, 1):
                niveau = "FAIBLE"

        # HVAR AP / anti-blindage : surtout utile quand les blindés nord-coréens
        # sont encore un problème majeur.
        elif "hvar" in nom and "semi-perforante" in nom:
            if cle < (1950, 7):
                niveau = "FAIBLE"
            elif cle <= (1951, 3):
                niveau = "ÉLEVÉE"
            elif cle <= (1951, 6):
                niveau = "NORMALE"
            else:
                niveau = "FAIBLE"

        # ATAR : urgence antichar développée en juillet 1950,
        # première livraison fin juillet et emploi surtout en 1950.
        elif "atar" in nom:
            if cle < (1950, 8):
                niveau = "INDISPONIBLE"
            elif cle <= (1950, 10):
                niveau = "ÉLEVÉE"
            elif cle <= (1951, 3):
                niveau = "FAIBLE"
            else:
                niveau = "TRÈS FAIBLE"

        # Napalm : extrêmement important pendant l'arrêt de l'offensive,
        # Pusan, la retraite et le CAS d'hiver 1950-51.
        elif "napalm" in nom:
            if cle < (1950, 6):
                niveau = "FAIBLE"
            elif cle <= (1951, 2):
                niveau = "TRÈS ÉLEVÉE"
                modificateur = 1.15
            elif cle <= (1951, 6):
                niveau = "ÉLEVÉE"
            elif cle <= (1952, 6):
                niveau = "NORMALE"
            else:
                niveau = "FAIBLE"

            if avion == "F-86A-5" and cle >= (1953, 1):
                niveau = "TRÈS FAIBLE"

        # 500 lb GP : véritable cheval de bataille.
        elif "anm64" in nom or "500 lb" in nom:
            niveau = "ÉLEVÉE"

            if (
                (1951, 3) <= cle <= (1951, 6)
                or (1952, 5) <= cle <= (1952, 9)
                or (1953, 4) <= cle <= (1953, 7)
            ):
                niveau = "TRÈS ÉLEVÉE"

        # 1000 lb : plus forte importance avec l'interdiction lourde
        # et les grands objectifs 1952-53.
        elif "anm65" in nom or "1000 lb" in nom:
            if cle <= (1951, 6):
                niveau = "NORMALE"
            elif cle <= (1952, 4):
                niveau = "ÉLEVÉE"
            else:
                niveau = "TRÈS ÉLEVÉE"

            if avion == "F-51D":
                niveau = (
                    "ÉLEVÉE"
                    if cle >= (1952, 1)
                    else "NORMALE"
                )

        elif "anm57" in nom or "250 lb" in nom:
            niveau = "NORMALE"

        elif "anm88" in nom or "fragmentation" in nom:
            niveau = "FAIBLE"

        elif "m26a2" in nom or "m29a1" in nom or "sous-munitions" in nom:
            niveau = "FAIBLE"

        elif "éclairante" in nom or "flare" in nom:
            niveau = "TRÈS FAIBLE"

        elif "tiny tim" in nom:
            # Armes navales / très marginales pour les unités USAF simulées.
            niveau = "TRÈS FAIBLE"

        elif "réservoir" in nom:
            # Les réservoirs largables sont très importants pour les jets,
            # mais ils ne doivent pas dominer la part "munition".
            niveau = (
                "ÉLEVÉE"
                if avion in (
                    "F-80C-10",
                    "F-84E",
                    "F-86A-5"
                )
                else "NORMALE"
            )

    # --------------------------------------------------------
    # IL-10 NORD-COREEN
    # --------------------------------------------------------
    elif avion == "IL-10":
        if cle <= (1950, 8):
            if (
                "m-13uk" in nom
                or "m-8" in nom
                or "fab-100" in nom
                or "fab-250" in nom
            ):
                niveau = "ÉLEVÉE"
            elif "ptab" in nom:
                niveau = "NORMALE"
            elif "ao-" in nom:
                niveau = "NORMALE"
            elif "sab-" in nom:
                niveau = "TRÈS FAIBLE"
            else:
                niveau = "NORMALE"

        elif cle <= (1950, 10):
            niveau = (
                "NORMALE"
                if (
                    "fab-" in nom
                    or "m-13uk" in nom
                    or "m-8" in nom
                )
                else "FAIBLE"
            )

        elif cle <= (1951, 3):
            niveau = "FAIBLE"

        else:
            niveau = "TRÈS FAIBLE"

    # --------------------------------------------------------
    # MiG-15 : principalement chasseur / intercepteur.
    # --------------------------------------------------------
    elif avion == "MiG-15bis":
        if "réservoir" in nom:
            niveau = "ÉLEVÉE"

        elif "fab-" in nom:
            niveau = "TRÈS FAIBLE"
            modificateur = 0.55

        elif "sab-" in nom:
            niveau = "TRÈS FAIBLE"
            modificateur = 0.40

        else:
            niveau = "TRÈS FAIBLE"

    else:
        niveau = niveau_standard_munition(
            munition
        )

    if niveau == "INDISPONIBLE":
        quantite = 0.0
    else:
        quantite = float(
            quantites.get(
                niveau,
                0.0
            )
        )

        quantite = _arrondir_reference_historique(
            quantite
            * float(
                modificateur
            )
        )

    return {
        "niveau": niveau,
        "quantite_reference": quantite,
        "statut_historique": "HISTORIQUE_RECONSTRUIT",
        "source": SOURCES_STANDARD_HISTORIQUE
    }


def assurer_modele_standard_mensuel(
    annee,
    mois,
    avion
):
    """
    Génère / actualise le STANDARD historique pour le mois demandé.

    Les règles de quota sont appliquées AVANT écriture en base :
    - TRÈS ÉLEVÉE : max 1
    - ÉLEVÉE : max 2

    Si le profil historique brut dépasse une limite, les munitions
    les plus importantes conservent les places rares et les autres
    sont rétrogradées automatiquement.
    """
    compatibles = trier_munitions_logiquement(
        AVIONS_EMPORTS.get(
            avion,
            []
        )
    )

    if not compatibles:
        return

    profils_bruts = {}
    affectations_brutes = {}
    scores = {}

    for munition in compatibles:
        historique = (
            profil_standard_historique_munition(
                annee,
                mois,
                avion,
                munition
            )
        )

        profils_bruts[
            munition
        ] = historique

        affectations_brutes[
            munition
        ] = historique[
            "niveau"
        ]

        scores[
            munition
        ] = float(
            historique.get(
                "quantite_reference",
                0.0
            )
        )

    affectations_valides = (
        normaliser_affectations_selon_limites(
            affectations_brutes,
            scores=scores
        )
    )

    quantites_periode = (
        quantites_standard_historiques_periode(
            annee,
            mois,
            avion
        )
    )

    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    for munition in compatibles:
        historique = profils_bruts[
            munition
        ]

        niveau_initial = historique[
            "niveau"
        ]

        niveau_final = affectations_valides[
            munition
        ]

        if niveau_final == "INDISPONIBLE":
            quantite_finale = 0.0

        elif niveau_final != niveau_initial:
            # Une rétrogradation de quota doit utiliser la quantité
            # de référence correspondant au nouveau niveau.
            quantite_finale = float(
                quantites_periode.get(
                    niveau_final,
                    0.0
                )
            )

        else:
            quantite_finale = float(
                historique[
                    "quantite_reference"
                ]
            )

        source = (
            VERSION_STANDARD_HISTORIQUE
            + " | "
            + historique[
                "source"
            ]
        )

        if niveau_final != niveau_initial:
            source += (
                " | QUOTA_APPLIQUE:"
                + niveau_initial
                + "->"
                + niveau_final
            )

        curseur.execute(
            """
            INSERT INTO standard_repartition_mensuelle (
                annee,
                mois,
                avion,
                munition,
                niveau,
                quantite_reference,
                statut_historique,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(
                annee,
                mois,
                avion,
                munition
            )
            DO UPDATE SET
                niveau = excluded.niveau,
                quantite_reference = excluded.quantite_reference,
                statut_historique = excluded.statut_historique,
                source = excluded.source
            """,
            (
                int(
                    annee
                ),
                int(
                    mois
                ),
                str(
                    avion
                ),
                str(
                    munition
                ),
                niveau_final,
                quantite_finale,
                historique[
                    "statut_historique"
                ],
                source
            )
        )

    connexion.commit()
    connexion.close()



def lire_standard_mensuel_munition(
    annee,
    mois,
    avion,
    munition
):
    assurer_modele_standard_mensuel(
        annee,
        mois,
        avion
    )

    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    ligne = curseur.execute(
        """
        SELECT
            niveau,
            quantite_reference,
            statut_historique,
            source
        FROM standard_repartition_mensuelle
        WHERE
            annee = ?
            AND mois = ?
            AND avion = ?
            AND munition = ?
        LIMIT 1
        """,
        (
            int(
                annee
            ),
            int(
                mois
            ),
            str(
                avion
            ),
            str(
                munition
            )
        )
    ).fetchone()

    connexion.close()

    if ligne is None:
        return profil_standard_historique_munition(
            annee,
            mois,
            avion,
            munition
        )

    return {
        "niveau": str(
            ligne[0]
        ),
        "quantite_reference": float(
            ligne[1]
        ),
        "statut_historique": str(
            ligne[2]
            or "HISTORIQUE_RECONSTRUIT"
        ),
        "source": str(
            ligne[3]
            or SOURCES_STANDARD_HISTORIQUE
        )
    }


def statut_standard_mensuel(
    annee,
    mois,
    avion
):
    assurer_modele_standard_mensuel(
        annee,
        mois,
        avion
    )

    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    lignes = curseur.execute(
        """
        SELECT DISTINCT statut_historique
        FROM standard_repartition_mensuelle
        WHERE
            annee = ?
            AND mois = ?
            AND avion = ?
        """,
        (
            int(
                annee
            ),
            int(
                mois
            ),
            str(
                avion
            )
        )
    ).fetchall()

    connexion.close()

    statuts = {
        str(
            ligne[0]
            or ""
        )
        for ligne in lignes
    }

    if statuts == {
        "HISTORIQUE_RECONSTRUIT"
    }:
        return "HISTORIQUE RECONSTRUIT"

    if "DOCUMENTE" in statuts:
        return "DOCUMENTÉ"

    return "HISTORIQUE RECONSTRUIT"


def niveau_standard_munition(
    munition
):
    """
    Fallback générique uniquement.

    Le STANDARD principal passe désormais par
    profil_standard_historique_munition(année, mois, avion, munition).
    """
    nom = munition.lower()
    categorie = categorie_affichage_munition(
        munition
    )

    if (
        "éclairante" in nom
        or "flare" in nom
        or "sab-" in nom
    ):
        return "TRÈS FAIBLE"

    if (
        "napalm" in nom
        or "tiny tim" in nom
        or "atar" in nom
    ):
        return "FAIBLE"

    if categorie == "Roquettes":
        return "ÉLEVÉE"

    if categorie == "Bombes":
        return "NORMALE"

    if categorie == "Réservoirs":
        return "NORMALE"

    if categorie == "Napalm":
        return "FAIBLE"

    return "NORMALE"


# ============================================================
# DIRECTIVES STANDARD — NÉCESSAIRES AU MOTEUR DE STOCK
# ============================================================
#
# IMPORTANT :
# Ces fonctions doivent être définies AVANT toute synchronisation de
# démarrage. Un ravitaillement IL-2 peut déclencher immédiatement
# calculer_repartition_standard_carriere(), qui passe par
# lire_niveau_munition_periode().
#
# Ne pas déplacer ce bloc après RESULTAT_SYNCHRO_CARRIERE.
# ============================================================

def lire_directive_standard_applicable(
    annee,
    mois,
    avion
):
    """
    Retourne la dernière directive entrée en vigueur avant ou pendant
    la période demandée.

    mode CUSTOM : priorités imposées par le haut commandement.
    mode BASE   : retour au STANDARD historique à partir de cette date.
    """
    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        curseur = connexion.cursor()

        ligne = curseur.execute(
            """
            SELECT
                id,
                annee_effet,
                mois_effet,
                mode,
                cout,
                date_creation
            FROM directives_standard_commandement
            WHERE
                avion = ?
                AND (
                    annee_effet < ?
                    OR (
                        annee_effet = ?
                        AND mois_effet <= ?
                    )
                )
            ORDER BY
                annee_effet DESC,
                mois_effet DESC,
                id DESC
            LIMIT 1
            """,
            (
                str(
                    avion
                ),
                int(
                    annee
                ),
                int(
                    annee
                ),
                int(
                    mois
                )
            )
        ).fetchone()

        if ligne is None:
            connexion.close()
            return None

        directive = {
            "id": int(
                ligne[0]
            ),
            "annee_effet": int(
                ligne[1]
            ),
            "mois_effet": int(
                ligne[2]
            ),
            "mode": str(
                ligne[3]
            ),
            "cout": int(
                ligne[4]
            ),
            "date_creation": str(
                ligne[5]
                or ""
            ),
            "priorites": {}
        }

        if directive[
            "mode"
        ] == "CUSTOM":
            priorites = curseur.execute(
                """
                SELECT
                    munition,
                    niveau
                FROM directives_standard_priorites
                WHERE directive_id = ?
                """,
                (
                    directive[
                        "id"
                    ],
                )
            ).fetchall()

            directive[
                "priorites"
            ] = {
                str(
                    munition
                ): str(
                    niveau
                )
                for munition, niveau
                in priorites
            }

        connexion.close()

        return directive

    except sqlite3.Error:
        return None


def niveau_standard_effectif_avec_directive(
    annee,
    mois,
    avion,
    munition
):
    """
    Niveau réellement utilisé par le STANDARD.

    La donnée historique reste intacte dans standard_repartition_mensuelle.
    Une directive CUSTOM la remplace de manière persistante jusqu'à ce
    qu'une nouvelle directive ou un événement BASE entre en vigueur.
    """
    historique = lire_standard_mensuel_munition(
        annee,
        mois,
        avion,
        munition
    )[
        "niveau"
    ]

    directive = lire_directive_standard_applicable(
        annee,
        mois,
        avion
    )

    if (
        directive is None
        or directive[
            "mode"
        ] == "BASE"
    ):
        return historique

    niveau = directive[
        "priorites"
    ].get(
        munition
    )

    if niveau in NIVEAUX_REPARTITION:
        return niveau

    return historique


def lire_niveau_munition_periode(
    modele,
    annee,
    mois,
    avion,
    munition
):
    if modele == "STANDARD":
        return niveau_standard_effectif_avec_directive(
            annee,
            mois,
            avion,
            munition
        )

    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        curseur = connexion.cursor()

        ligne = curseur.execute(
            """
            SELECT niveau
            FROM affectations_repartition
            WHERE
                modele = ?
                AND annee = ?
                AND mois = ?
                AND avion = ?
                AND munition = ?
            LIMIT 1
            """,
            (
                modele,
                int(
                    annee
                ),
                int(
                    mois
                ),
                str(
                    avion
                ),
                str(
                    munition
                )
            )
        ).fetchone()

        connexion.close()

        if (
            ligne
            and ligne[0] in NIVEAUX_REPARTITION
        ):
            return ligne[0]

    except sqlite3.Error:
        pass

    # Une nouvelle configuration personnalisée démarre comme copie du
    # STANDARD HISTORIQUE de la période courante.
    return lire_standard_mensuel_munition(
        annee,
        mois,
        avion,
        munition
    )["niveau"]


def sauvegarder_niveau_munition_periode(
    modele,
    annee,
    mois,
    avion,
    munition,
    niveau
):
    if niveau not in NIVEAUX_REPARTITION:
        niveau = "NORMALE"

    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    curseur.execute(
        """
        INSERT INTO affectations_repartition (
            modele,
            annee,
            mois,
            avion,
            munition,
            niveau
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(
            modele,
            annee,
            mois,
            avion,
            munition
        )
        DO UPDATE SET
            niveau = excluded.niveau
        """,
        (
            modele,
            int(
                annee
            ),
            int(
                mois
            ),
            str(
                avion
            ),
            str(
                munition
            ),
            niveau
        )
    )

    connexion.commit()
    connexion.close()


def verifier_limites_niveaux(
    affectations
):
    compteurs = {
        niveau: 0
        for niveau in NIVEAUX_REPARTITION
    }

    for niveau in affectations.values():
        if niveau in compteurs:
            compteurs[
                niveau
            ] += 1

    erreurs = []

    for niveau, maximum in LIMITES_NIVEAUX_REPARTITION.items():
        if compteurs[
            niveau
        ] > maximum:
            erreurs.append(
                (
                    niveau,
                    compteurs[
                        niveau
                    ],
                    maximum
                )
            )

    return erreurs


def calculer_parts_modele(
    modele,
    annee,
    mois,
    avion,
    munitions
):
    quantites = obtenir_quantites_niveaux(
        modele
    )

    donnees = {}

    total_reference = 0.0

    for munition in munitions:
        niveau = lire_niveau_munition_periode(
            modele,
            annee,
            mois,
            avion,
            munition
        )

        quantite = max(
            0.0,
            float(
                quantites.get(
                    niveau,
                    0.0
                )
            )
        )

        if niveau == "INDISPONIBLE":
            quantite = 0.0

        donnees[
            munition
        ] = {
            "niveau": niveau,
            "quantite_reference": quantite,
            "part": 0.0
        }

        total_reference += quantite

    if total_reference > 0:
        for munition in donnees:
            donnees[
                munition
            ][
                "part"
            ] = (
                donnees[
                    munition
                ][
                    "quantite_reference"
                ]
                / total_reference
                * 100.0
            )

    return donnees


def nom_affiche_modele_actif():
    cle = cle_modele_repartition_actif()

    if cle == "STANDARD":
        return "STANDARD"

    return nom_profil_repartition(
        cle
    )



MOIS_FRANCAIS = {
    1: "JANVIER",
    2: "FÉVRIER",
    3: "MARS",
    4: "AVRIL",
    5: "MAI",
    6: "JUIN",
    7: "JUILLET",
    8: "AOÛT",
    9: "SEPTEMBRE",
    10: "OCTOBRE",
    11: "NOVEMBRE",
    12: "DÉCEMBRE"
}


def positionner_spinbox_mois(
    spinbox,
    variable,
    mois
):
    """
    Force réellement le mois sélectionné dans un tk.Spinbox.

    Important :
    avec un Spinbox créé directement en state='readonly', Tkinter peut
    sélectionner automatiquement la première valeur de la liste
    (JANVIER), même si le StringVar contenait déjà AVRIL / MAI / etc.

    On passe donc brièvement le widget en mode normal, on positionne
    explicitement sa valeur, puis on le remet en readonly.
    """
    mois = int(
        mois
    )

    texte_mois = t_mois(
        mois
    )

    try:
        spinbox.configure(
            state="normal"
        )

        spinbox.delete(
            0,
            "end"
        )

        spinbox.insert(
            0,
            texte_mois
        )

        variable.set(
            texte_mois
        )

        spinbox.configure(
            state="readonly"
        )

    except Exception:
        variable.set(
            texte_mois
        )


def extraire_annee_mois_carriere(
    donnees_carriere
):
    """
    Extrait année/mois depuis career.currentTime/currentDate.
    Fallback : avril 1951.
    """
    texte = str(
        donnees_carriere.get(
            "date_jeu",
            ""
        )
        or ""
    )

    for format_source in (
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ):
        try:
            date = datetime.strptime(
                texte,
                format_source
            )

            return (
                int(
                    date.year
                ),
                int(
                    date.month
                )
            )

        except ValueError:
            pass

    return (
        1951,
        4
    )


def lire_priorite_munition_periode(
    annee,
    mois,
    munition
):
    """
    Priorité technique du modèle STANDARD pour une munition donnée.

    100 % = poids normal.
    50 %  = moitié du poids.
    0 %   = munition exclue de la répartition pour cette période.
    """
    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    ligne = curseur.execute(
        """
        SELECT priorite
        FROM priorites_repartition_mensuelles
        WHERE
            annee = ?
            AND mois = ?
            AND munition = ?
        LIMIT 1
        """,
        (
            int(
                annee
            ),
            int(
                mois
            ),
            str(
                munition
            )
        )
    ).fetchone()

    connexion.close()

    if ligne is None:
        return 100.0

    return max(
        0.0,
        min(
            100.0,
            float(
                ligne[0]
            )
        )
    )


def sauvegarder_priorite_munition_periode(
    annee,
    mois,
    munition,
    priorite
):
    priorite = max(
        0.0,
        min(
            100.0,
            float(
                priorite
            )
        )
    )

    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    curseur.execute(
        """
        INSERT INTO priorites_repartition_mensuelles (
            annee,
            mois,
            munition,
            priorite
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(
            annee,
            mois,
            munition
        )
        DO UPDATE SET
            priorite = excluded.priorite
        """,
        (
            int(
                annee
            ),
            int(
                mois
            ),
            str(
                munition
            ),
            priorite
        )
    )

    connexion.commit()
    connexion.close()


def charger_priorites_periode(
    annee,
    mois,
    avion
):
    return {
        nom: lire_priorite_munition_periode(
            annee,
            mois,
            nom
        )
        for nom in trier_munitions_logiquement(
            AVIONS_EMPORTS.get(
                avion,
                []
            )
        )
    }



def lire_preference_repartition(
    cle,
    valeur_defaut=""
):
    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        curseur = connexion.cursor()

        ligne = curseur.execute(
            """
            SELECT valeur
            FROM preferences_repartition
            WHERE cle = ?
            LIMIT 1
            """,
            (
                cle,
            )
        ).fetchone()

        connexion.close()

        if ligne is None:
            return valeur_defaut

        return str(
            ligne[0]
        )

    except sqlite3.Error:
        return valeur_defaut


def ecrire_preference_repartition(
    cle,
    valeur
):
    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    curseur.execute(
        """
        INSERT INTO preferences_repartition (
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
            str(
                valeur
            )
        )
    )

    connexion.commit()
    connexion.close()


def mode_repartition_actif():
    return (
        "STANDARD"
        if cle_modele_repartition_actif() == "STANDARD"
        else "PERSONNALISE"
    )


def ouvrir_menu_profils_repartition(
    bouton_mode,
    callback_selection=None
):
    """
    Sélecteur de profils intégré à la fenêtre courante.

    - apparaît directement sous la box ;
    - maximum 6 profils visibles ;
    - scrollbar verticale fonctionnelle ;
    - molette fonctionnelle sur TOUT le menu, y compris sur les boutons ;
    - style cohérent avec l'interface IL-2.
    """

    if bouton_mode is None:
        return


    # --------------------------------------------------------
    # SECOND CLIC = FERMETURE
    # --------------------------------------------------------

    ancien_menu = getattr(
        bouton_mode,
        "_menu_profils_repartition",
        None
    )

    if ancien_menu is not None:
        try:
            if ancien_menu.winfo_exists():
                ancien_menu.destroy()

                bouton_mode._menu_profils_repartition = None

                return
        except Exception:
            pass


    profils = [
        (
            "STANDARD",
            "STANDARD"
        )
    ]

    profils.extend(
        lister_profils_repartition_personnalises()
    )


    parent = bouton_mode.winfo_toplevel()

    parent.update_idletasks()
    bouton_mode.update_idletasks()


    largeur_bouton = max(
        1,
        bouton_mode.winfo_width()
    )

    largeur_menu = max(
        220,
        largeur_bouton
    )


    hauteur_ligne = 38
    hauteur_separateur = 1

    nombre_visible = min(
        6,
        max(
            1,
            len(
                profils
            )
        )
    )

    hauteur_menu = (
        nombre_visible
        * hauteur_ligne
        + max(
            0,
            nombre_visible
            - 1
        )
        * hauteur_separateur
        + 2
    )


    # --------------------------------------------------------
    # POSITION RELATIVE AU TOPLEVEL
    # --------------------------------------------------------

    x = (
        bouton_mode.winfo_rootx()
        - parent.winfo_rootx()
    )

    y = (
        bouton_mode.winfo_rooty()
        - parent.winfo_rooty()
        + bouton_mode.winfo_height()
        + 2
    )


    largeur_parent = max(
        1,
        parent.winfo_width()
    )

    hauteur_parent = max(
        1,
        parent.winfo_height()
    )


    if (
        x
        + largeur_menu
        > largeur_parent
        - 4
    ):
        x = max(
            4,
            largeur_parent
            - largeur_menu
            - 4
        )


    if (
        y
        + hauteur_menu
        > hauteur_parent
        - 4
    ):
        y = max(
            4,
            (
                bouton_mode.winfo_rooty()
                - parent.winfo_rooty()
                - hauteur_menu
                - 2
            )
        )


    # --------------------------------------------------------
    # PANNEAU
    # --------------------------------------------------------

    menu = tk.Frame(
        parent,
        bg=theme["panneau"],
        highlightbackground=theme["contour_fenetre"],
        highlightthickness=1,
        bd=0
    )

    menu.place(
        x=x,
        y=y,
        width=largeur_menu,
        height=hauteur_menu
    )

    menu.lift()

    bouton_mode._menu_profils_repartition = (
        menu
    )


    # --------------------------------------------------------
    # CANVAS + SCROLLBAR
    # --------------------------------------------------------

    canvas = tk.Canvas(
        menu,
        bg=theme["champ"],
        highlightthickness=0,
        bd=0,
        yscrollincrement=(
            hauteur_ligne
            + hauteur_separateur
        )
    )

    canvas.pack(
        side="left",
        fill="both",
        expand=True
    )


    scrollbar = tk.Scrollbar(
        menu,
        orient="vertical",
        command=canvas.yview,
        bg=theme["panneau_alt"],
        activebackground=theme["bleu"],
        troughcolor=theme["fond"],
        relief="flat",
        borderwidth=0,
        highlightthickness=0,
        width=14
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )


    canvas.configure(
        yscrollcommand=scrollbar.set
    )


    contenu = tk.Frame(
        canvas,
        bg=theme["champ"]
    )

    item_contenu = canvas.create_window(
        (
            0,
            0
        ),
        window=contenu,
        anchor="nw"
    )


    def ajuster_scroll(event=None):
        canvas.update_idletasks()

        zone = canvas.bbox(
            "all"
        )

        if zone is not None:
            canvas.configure(
                scrollregion=zone
            )

        canvas.itemconfigure(
            item_contenu,
            width=canvas.winfo_width()
        )


    contenu.bind(
        "<Configure>",
        ajuster_scroll
    )

    canvas.bind(
        "<Configure>",
        ajuster_scroll
    )


    # --------------------------------------------------------
    # FERMETURE
    # --------------------------------------------------------

    def fermer_menu():
        try:
            if menu.winfo_exists():
                menu.destroy()
        except Exception:
            pass

        try:
            bouton_mode._menu_profils_repartition = (
                None
            )
        except Exception:
            pass


    # --------------------------------------------------------
    # SELECTION
    # --------------------------------------------------------

    cle_active = cle_modele_repartition_actif()

    # La box garde une copie directe de la clé sélectionnée.
    # Cela évite toute ambiguïté lorsqu'il y a beaucoup de profils.
    bouton_mode._profil_repartition_actif = (
        cle_active
    )


    def choisir_profil(
        cle,
        libelle
    ):
        definir_modele_repartition_actif(
            cle
        )

        # Mémorisation locale immédiate de l'identifiant exact.
        bouton_mode._profil_repartition_actif = (
            cle
        )

        try:
            bouton_mode.configure(
                text=libelle
            )
        except Exception:
            pass

        fermer_menu()

        if callback_selection is not None:
            try:
                callback_selection(
                    cle
                )
            except Exception:
                pass


    # --------------------------------------------------------
    # SCROLL ROBUSTE
    # --------------------------------------------------------

    def defiler_molette(event):
        delta = getattr(
            event,
            "delta",
            0
        )

        if delta:
            direction = (
                -1
                if delta > 0
                else 1
            )

        else:
            numero = getattr(
                event,
                "num",
                0
            )

            if numero == 4:
                direction = -1
            elif numero == 5:
                direction = 1
            else:
                return "break"


        canvas.yview_scroll(
            direction,
            "units"
        )

        return "break"


    def lier_scroll_widget(widget):
        """
        Lie la molette au widget ET à tous ses descendants.
        Important car les boutons Tk interceptent sinon la molette.
        """
        try:
            widget.bind(
                "<MouseWheel>",
                defiler_molette
            )

            widget.bind(
                "<Button-4>",
                defiler_molette
            )

            widget.bind(
                "<Button-5>",
                defiler_molette
            )
        except Exception:
            pass

        try:
            for enfant in widget.winfo_children():
                lier_scroll_widget(
                    enfant
                )
        except Exception:
            pass


    # --------------------------------------------------------
    # LIGNES
    # --------------------------------------------------------

    for index, (
        cle,
        libelle
    ) in enumerate(
        profils
    ):
        actif = (
            cle
            == cle_active
        )

        fond = (
            theme["bleu"]
            if actif
            else theme["champ"]
        )

        texte = (
            theme["blanc"]
            if actif
            else theme["champ_texte"]
        )


        ligne = tk.Frame(
            contenu,
            height=hauteur_ligne,
            bg=fond
        )

        ligne.pack(
            fill="x"
        )

        ligne.pack_propagate(
            False
        )


        marqueur = tk.Frame(
            ligne,
            width=4,
            bg=(
                theme["blanc"]
                if actif
                else theme["separateur"]
            )
        )

        marqueur.pack(
            side="left",
            fill="y"
        )


        bouton_profil = tk.Button(
            ligne,
            text=libelle,
            command=lambda
                c=cle,
                l=libelle:
                choisir_profil(
                    c,
                    l
                ),
            font=(POLICE, 8, "bold"),
            anchor="w",
            padx=10,
            bg=fond,
            fg=texte,
            activebackground=theme["bleu"],
            activeforeground=theme["blanc"],
            relief="flat",
            borderwidth=0,
            cursor="hand2"
        )

        bouton_profil.pack(
            side="left",
            fill="both",
            expand=True
        )


        if (
            index
            < len(
                profils
            )
            - 1
        ):
            separateur = tk.Frame(
                contenu,
                height=hauteur_separateur,
                bg=theme["separateur"]
            )

            separateur.pack(
                fill="x"
            )


    # --------------------------------------------------------
    # FINALISATION DU SCROLL
    # --------------------------------------------------------

    menu.update_idletasks()
    ajuster_scroll()

    lier_scroll_widget(
        menu
    )

    lier_scroll_widget(
        canvas
    )

    lier_scroll_widget(
        contenu
    )

    lier_scroll_widget(
        scrollbar
    )


    # Positionne automatiquement le profil actif dans la zone visible.
    index_actif = 0

    for index, (
        cle,
        libelle
    ) in enumerate(
        profils
    ):
        if cle == cle_active:
            index_actif = index
            break


    if len(
        profils
    ) > nombre_visible:
        fraction = (
            index_actif
            / max(
                1,
                len(
                    profils
                )
                - 1
            )
        )

        canvas.yview_moveto(
            max(
                0.0,
                min(
                    1.0,
                    fraction
                )
            )
        )




def profil_repartition_selectionne_depuis_bouton(
    bouton_mode
):
    """
    Renvoie l'identifiant précis du profil représenté par une box.

    Priorité :
    1. clé mémorisée directement sur le bouton ;
    2. clé active enregistrée en base.

    La valeur est toujours validée avant utilisation.
    """
    cle = getattr(
        bouton_mode,
        "_profil_repartition_actif",
        ""
    )

    if cle == "STANDARD":
        return "STANDARD"

    profils_valides = {
        identifiant
        for identifiant, nom
        in lister_profils_repartition_personnalises()
    }

    if cle in profils_valides:
        return cle

    cle = cle_modele_repartition_actif()

    if cle == "STANDARD":
        return "STANDARD"

    if cle in profils_valides:
        return cle

    return "STANDARD"



def basculer_mode_repartition(
    bouton_mode=None
):
    """
    Compatibilité avec le reste de l'interface :
    un clic ouvre désormais le menu de profils au lieu de basculer
    immédiatement entre les deux modes.
    """

    if bouton_mode is None:
        return

    ouvrir_menu_profils_repartition(
        bouton_mode
    )



def ouvrir_editeur_modele_repartition():
    _debut_performance_ui = time.perf_counter()
    """
    Editeur de modèle COMPLET.

    Un modèle contient plusieurs périodes mensuelles.

    Pendant la session :
    - l'utilisateur change d'année / mois ;
    - les modifications de chaque période restent en mémoire ;
    - revenir sur une période restaure le brouillon ;
    - ENREGISTRER LE MODÈLE sauvegarde toutes les périodes modifiées
      en une seule transaction.
    """

    avion = DONNEES_CARRIERE_IL2.get(
        "avion",
        avion_selectionne
    )

    annee_courante, mois_courant = (
        obtenir_annee_mois_carriere_frais()
    )

    COULEURS_PRIORITES = {
        "TRÈS ÉLEVÉE": ("#b75b55", "#f2f0ea"),
        "ÉLEVÉE": ("#b98548", "#f2f0ea"),
        "NORMALE": (theme["bleu"], theme["blanc"]),
        "FAIBLE": (theme["vert"], theme["blanc"]),
        "TRÈS FAIBLE": ("#7f8379", "#f2f0ea"),
        "INDISPONIBLE": (theme["bordure"], theme["blanc"])
    }

    fenetre_modele = tk.Toplevel(
        fenetre
    )

    fenetre_modele.after_idle(
        lambda debut=_debut_performance_ui:
        journaliser_performance_ui(
            'Éditeur modèle',
            debut
        )
    )

    appliquer_chrome_custom(
        fenetre_modele,
        t("model.window"),
        1680,
        930,
        fenetre_modele.destroy
    )

    corps = tk.Frame(
        fenetre_modele,
        bg=theme["fond"]
    )

    corps.pack(
        fill="both",
        expand=True
    )

    # ========================================================
    # ENTETE
    # ========================================================

    entete = tk.Frame(
        corps,
        height=96,
        bg=theme["barre"]
    )

    entete.pack(
        fill="x"
    )

    entete.pack_propagate(
        False
    )

    tk.Label(
        entete,
        text=t("model.title"),
        font=(POLICE, 17, "bold"),
        bg=theme["barre"],
        fg=theme["blanc"]
    ).pack(
        pady=(12, 2)
    )

    tk.Label(
        entete,
        text=t("model.subtitle", aircraft=avion),
        font=(POLICE, 8, "bold"),
        bg=theme["barre"],
        fg=theme["texte_faible"]
    ).pack()

    tk.Label(
        entete,
        text=t("model.description"),
        font=(POLICE, 8),
        bg=theme["barre"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(3, 0)
    )

    # ========================================================
    # BARRE MODELE
    # ========================================================

    barre = tk.Frame(
        corps,
        height=78,
        bg=theme["panneau"]
    )

    barre.pack(
        fill="x",
        padx=22,
        pady=(12, 8)
    )

    barre.pack_propagate(
        False
    )

    tk.Label(
        barre,
        text=t("model.selector"),
        font=(POLICE, 8, "bold"),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).place(
        x=16,
        y=5,
        width=180,
        height=18
    )

    variable_mode = tk.StringVar(
        value=(
            "PERSONNALISE"
            if (
                cle_modele_repartition_actif()
                != "STANDARD"
                and existe_modele_personnalise()
            )
            else "STANDARD"
        )
    )

    variable_nom_modele = tk.StringVar(
        value=(
            nom_affiche_modele_actif()
            if (
                cle_modele_repartition_actif()
                != "STANDARD"
            )
            else "MODÈLE 1"
        )
    )

    bouton_mode = tk.Button(
        barre,
        text=(
            nom_affiche_modele_actif()
            if variable_mode.get() == "PERSONNALISE"
            else "STANDARD"
        ),
        font=(POLICE, 9, "bold"),
        bg=theme["champ"],
        fg=theme["texte"],
        activebackground=theme["panneau_alt"],
        activeforeground=theme["texte"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    )

    bouton_mode.place(
        x=16,
        y=27,
        width=180,
        height=38
    )

    bouton_ajouter_modele = tk.Button(
        barre,
        text="+",
        font=(POLICE, 14, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte"],
        activebackground=theme["bleu"],
        activeforeground=theme["blanc"],
        disabledforeground=theme["texte_faible"],
        relief="solid",
        borderwidth=1,
        cursor="hand2",
        state="normal"
    )

    bouton_ajouter_modele.place(
        x=202,
        y=27,
        width=36,
        height=38
    )

    bouton_supprimer_modele = tk.Button(
        barre,
        text="−",
        font=(POLICE, 14, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte_faible"],
        activebackground=theme["rouge"],
        activeforeground=theme["blanc"],
        disabledforeground=theme["texte_faible"],
        relief="solid",
        borderwidth=1,
        cursor="arrow",
        state="disabled"
    )

    bouton_supprimer_modele.place(
        x=244,
        y=27,
        width=36,
        height=38
    )

    label_etat = tk.Label(
        barre,
        text="",
        font=(POLICE, 8),
        anchor="e",
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    )

    label_etat.place(
        x=315,
        y=27,
        width=1315,
        height=38
    )

    # ========================================================
    # NIVEAUX + PERIODE A DROITE
    # ========================================================

    cadre_niveaux = tk.Frame(
        corps,
        bg=theme["panneau"]
    )

    cadre_niveaux.pack(
        fill="x",
        padx=22,
        pady=(0, 8)
    )

    # Hauteur automatique : le cadre suit réellement le contenu.
    # Cela évite que le bas des cartes de priorité soit coupé lorsque
    # la taille de police STANDARD ou GRAND est active.

    tk.Label(
        cadre_niveaux,
        text=t("model.weights.title"),
        font=(POLICE, 9, "bold"),
        anchor="w",
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        fill="x",
        padx=14,
        pady=(7, 1)
    )

    tk.Label(
        cadre_niveaux,
        text=t("model.weights.description"),
        font=(POLICE, 7),
        anchor="w",
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        fill="x",
        padx=14,
        pady=(0, 4)
    )

    zone_niveaux = tk.Frame(
        cadre_niveaux,
        bg=theme["panneau"]
    )

    zone_niveaux.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=(0, 8)
    )

    variables_quantites = {}
    widgets_quantites = {}
    variables_niveaux = {}
    lignes_niveaux = {}
    cartes_niveaux = {}

    variable_annee = tk.IntVar(
        value=annee_courante
    )

    variable_mois = tk.StringVar(
        value=t_mois(
            mois_courant
        )
    )

    # Brouillons conservés en mémoire jusqu'au clic final Enregistrer.
    # Structure :
    # {
    #   modele: {
    #       (annee, mois): {
    #           "quantites": {...},
    #           "affectations": {...}
    #       }
    #   }
    # }
    brouillons_modeles = {}

    periode_chargee = [
        annee_courante,
        mois_courant
    ]

    # --------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------

    def modele_cle():
        if variable_mode.get() == "STANDARD":
            return "STANDARD"

        cle = cle_modele_repartition_actif()

        if cle == "STANDARD":
            return cle_modele_personnalise()

        return cle

    def mode_est_editable():
        return (
            variable_mode.get()
            == "PERSONNALISE"
        )

    def mois_numero_depuis_nom(
        nom_mois
    ):
        texte = str(
            nom_mois
            or ""
        ).strip()

        for numero, nom in MOIS_FRANCAIS.items():
            if (
                nom.casefold() == texte.casefold()
                or t_mois(numero).casefold() == texte.casefold()
            ):
                return int(
                    numero
                )

        return mois_courant

    def periode_selectionnee():
        try:
            annee = int(
                variable_annee.get()
            )
        except Exception:
            annee = annee_courante

        mois = mois_numero_depuis_nom(
            variable_mois.get()
        )

        return (
            annee,
            mois
        )

    def couleur_priorite(
        niveau
    ):
        return COULEURS_PRIORITES.get(
            niveau,
            (
                theme["panneau_alt"],
                theme["texte"]
            )
        )

    def configurer_badge(
        widget,
        niveau
    ):
        fond, texte = couleur_priorite(
            niveau
        )

        widget.configure(
            bg=fond,
            fg=texte,
            activebackground=fond,
            activeforeground=texte
        )

    def lire_quantites_interface():
        resultat = {}

        for niveau, variable in variables_quantites.items():
            try:
                valeur = max(
                    0,
                    int(
                        variable.get()
                    )
                )
            except Exception:
                valeur = 0

            if niveau == "INDISPONIBLE":
                valeur = 0

            resultat[
                niveau
            ] = valeur

        return resultat

    def lire_affectations_interface():
        return {
            munition: variable.get()
            for munition, variable
            in variables_niveaux.items()
        }

    def memoriser_periode_courante():
        """
        Conserve le mois affiché en mémoire AVANT de naviguer vers un autre.
        Aucune écriture SQLite ici.
        """
        if not mode_est_editable():
            return

        if not variables_niveaux:
            return

        cle_modele = modele_cle()

        if cle_modele == "STANDARD":
            return

        annee, mois = (
            periode_chargee[0],
            periode_chargee[1]
        )

        brouillons_modeles.setdefault(
            cle_modele,
            {}
        )[
            (
                int(
                    annee
                ),
                int(
                    mois
                )
            )
        ] = {
            "quantites": lire_quantites_interface(),
            "affectations": lire_affectations_interface()
        }

    def lire_periode_brouillon_ou_base(
        cle_modele,
        annee,
        mois
    ):
        brouillon = (
            brouillons_modeles
            .get(
                cle_modele,
                {}
            )
            .get(
                (
                    int(
                        annee
                    ),
                    int(
                        mois
                    )
                )
            )
        )

        if brouillon is not None:
            return {
                "quantites": dict(
                    brouillon[
                        "quantites"
                    ]
                ),
                "affectations": dict(
                    brouillon[
                        "affectations"
                    ]
                )
            }

        compatibles = trier_munitions_logiquement(
            AVIONS_EMPORTS.get(
                avion,
                []
            )
        )

        if cle_modele == "STANDARD":
            quantites = (
                quantites_standard_historiques_periode(
                    annee,
                    mois,
                    avion
                )
            )

            affectations = {
                munition:
                lire_niveau_munition_periode(
                    "STANDARD",
                    annee,
                    mois,
                    avion,
                    munition
                )
                for munition in compatibles
            }

        else:
            quantites = (
                obtenir_quantites_niveaux_periode(
                    cle_modele,
                    annee,
                    mois
                )
            )

            affectations = {
                munition:
                lire_niveau_munition_periode(
                    cle_modele,
                    annee,
                    mois,
                    avion,
                    munition
                )
                for munition in compatibles
            }

        # Protection supplémentaire : un ancien preset créé avant v0.9.26
        # peut contenir des quotas invalides. On le normalise à l'affichage.
        affectations = normaliser_affectations_selon_limites(
            affectations
        )

        return {
            "quantites": quantites,
            "affectations": affectations
        }

    # ========================================================
    # CARTES DES NIVEAUX
    # ========================================================

    for colonne, niveau in enumerate(
        NIVEAUX_REPARTITION
    ):
        zone_niveaux.grid_columnconfigure(
            colonne,
            weight=1
        )

        fond_niveau, texte_niveau = (
            couleur_priorite(
                niveau
            )
        )

        carte = tk.Frame(
            zone_niveaux,
            bg=theme["panneau_alt"],
            highlightbackground=theme["bordure"],
            highlightthickness=1
        )

        carte.grid(
            row=0,
            column=colonne,
            sticky="nsew",
            padx=3
        )

        label_titre_niveau = tk.Label(
            carte,
            text=nom_affiche_niveau_repartition(
                niveau
            ),
            font=(POLICE, 7, "bold"),
            bg=fond_niveau,
            fg=texte_niveau
        )

        label_titre_niveau.pack(
            fill="x",
            padx=5,
            pady=(5, 3),
            ipady=2
        )

        maximum = LIMITES_NIVEAUX_REPARTITION.get(
            niveau
        )

        texte_limite = (
            f"0/{maximum}"
            if maximum is not None
            else t("model.free")
        )

        label_limite_niveau = tk.Label(
            carte,
            text=texte_limite,
            font=(POLICE, 7, "bold"),
            bg=theme["panneau_alt"],
            fg=theme["texte_faible"]
        )

        label_limite_niveau.pack(
            pady=(0, 3)
        )

        variable = tk.IntVar(
            value=int(
                QUANTITES_STANDARD_NIVEAUX[
                    niveau
                ]
            )
        )

        variables_quantites[
            niveau
        ] = variable

        spin = tk.Spinbox(
            carte,
            from_=0,
            to=100000,
            increment=25,
            textvariable=variable,
            justify="center",
            font=(POLICE, 10, "bold"),
            bg=theme["champ"],
            fg=theme["champ_texte"],
            buttonbackground=theme["panneau_alt"],
            relief="solid",
            borderwidth=1
        )

        spin.pack(
            fill="x",
            padx=5,
            pady=(0, 5),
            ipady=4
        )

        widgets_quantites[
            niveau
        ] = spin

        cartes_niveaux[
            niveau
        ] = {
            "carte": carte,
            "titre": label_titre_niveau,
            "limite": label_limite_niveau,
            "spin": spin,
            "fond_original": fond_niveau,
            "texte_original": texte_niveau
        }

        tk.Label(
            carte,
            text=t("model.weight"),
            font=(POLICE, 7),
            bg=theme["panneau_alt"],
            fg=theme["texte_faible"]
        ).pack(
            pady=(0, 6)
        )

        if niveau == "INDISPONIBLE":
            variable.set(
                0
            )

            spin.configure(
                state="disabled"
            )

    # --------------------------------------------------------
    # BLOC PERIODE A DROITE DE "INDISPONIBLE"
    # --------------------------------------------------------

    zone_niveaux.grid_columnconfigure(
        6,
        weight=0
    )

    cadre_periode = tk.Frame(
        zone_niveaux,
        width=310,
        bg=theme["panneau_alt"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    cadre_periode.grid(
        row=0,
        column=6,
        sticky="nsew",
        padx=(8, 3)
    )

    cadre_periode.grid_propagate(
        False
    )

    tk.Label(
        cadre_periode,
        text=t("model.period"),
        font=(POLICE, 8, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte"]
    ).pack(
        pady=(8, 6)
    )

    ligne_periode = tk.Frame(
        cadre_periode,
        bg=theme["panneau_alt"]
    )

    ligne_periode.pack(
        fill="x",
        padx=10
    )

    bloc_annee = tk.Frame(
        ligne_periode,
        bg=theme["panneau_alt"]
    )

    bloc_annee.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(0, 5)
    )

    tk.Label(
        bloc_annee,
        text=t("common.year"),
        font=(POLICE, 7, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 3)
    )

    spin_annee = tk.Spinbox(
        bloc_annee,
        from_=1950,
        to=1953,
        wrap=True,
        textvariable=variable_annee,
        justify="center",
        font=(POLICE, 9, "bold"),
        bg=theme["champ"],
        fg=theme["champ_texte"],
        buttonbackground=theme["panneau_alt"],
        relief="solid",
        borderwidth=1
    )

    spin_annee.pack(
        fill="x",
        ipady=4
    )

    bloc_mois = tk.Frame(
        ligne_periode,
        bg=theme["panneau_alt"]
    )

    bloc_mois.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(5, 0)
    )

    tk.Label(
        bloc_mois,
        text=t("common.month"),
        font=(POLICE, 7, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 3)
    )

    spin_mois = tk.Spinbox(
        bloc_mois,
        values=tuple(
            t_mois(
                numero
            )
            for numero in range(
                1,
                13
            )
        ),
        wrap=True,
        state="readonly",
        textvariable=variable_mois,
        justify="center",
        font=(POLICE, 8, "bold"),
        bg=theme["champ"],
        fg=theme["champ_texte"],
        readonlybackground=theme["champ"],
        buttonbackground=theme["panneau_alt"],
        relief="solid",
        borderwidth=1
    )

    spin_mois.pack(
        fill="x",
        ipady=4
    )

    label_periode_info = tk.Label(
        cadre_periode,
        text="",
        font=(POLICE, 7),
        bg=theme["panneau_alt"],
        fg=theme["texte_faible"]
    )

    label_periode_info.pack(
        pady=(8, 0)
    )

    # ========================================================
    # TABLEAU MUNITIONS
    # ========================================================

    zone_tableau = tk.Frame(
        corps,
        bg=theme["fond"]
    )

    zone_tableau.pack(
        fill="both",
        expand=True,
        padx=22,
        pady=(0, 8)
    )

    canvas = tk.Canvas(
        zone_tableau,
        bg=theme["fond"],
        highlightthickness=0
    )

    canvas.pack(
        side="left",
        fill="both",
        expand=True
    )

    scrollbar = tk.Scrollbar(
        zone_tableau,
        orient="vertical",
        command=canvas.yview
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    canvas.configure(
        yscrollcommand=scrollbar.set
    )

    contenu = tk.Frame(
        canvas,
        bg=theme["fond"]
    )

    item_contenu = canvas.create_window(
        (
            0,
            0
        ),
        window=contenu,
        anchor="nw"
    )

    def ajuster_canvas(
        event=None
    ):
        try:
            canvas.configure(
                scrollregion=canvas.bbox(
                    "all"
                )
            )

            canvas.itemconfigure(
                item_contenu,
                width=canvas.winfo_width()
            )
        except Exception:
            pass

    contenu.bind(
        "<Configure>",
        ajuster_canvas
    )

    canvas.bind(
        "<Configure>",
        ajuster_canvas
    )

    def affectations_interface():
        return {
            munition: variable.get()
            for munition, variable
            in variables_niveaux.items()
        }


    def actualiser_disponibilite_priorites():
        """
        Met à jour les cartes de priorité selon l'occupation du mois courant.

        Une priorité limitée pleine devient grisée.
        """
        affectations = affectations_interface()

        compteurs = compter_affectations_par_niveau(
            affectations
        )

        for niveau, infos in cartes_niveaux.items():
            maximum = LIMITES_NIVEAUX_REPARTITION.get(
                niveau
            )

            if maximum is None:
                infos[
                    "limite"
                ].configure(
                    text=t("model.free"),
                    fg=theme["texte_faible"]
                )

                infos[
                    "titre"
                ].configure(
                    bg=infos[
                        "fond_original"
                    ],
                    fg=infos[
                        "texte_original"
                    ]
                )

                continue

            utilise = compteurs.get(
                niveau,
                0
            )

            complet = (
                utilise >= maximum
            )

            infos[
                "limite"
            ].configure(
                text=f"{utilise}/{maximum}"
                + (
                    " • " + t("model.full")
                    if complet
                    else ""
                ),
                fg=(
                    theme["texte_faible"]
                    if complet
                    else theme["texte"]
                )
            )

            if complet:
                infos[
                    "titre"
                ].configure(
                    bg=theme["bordure"],
                    fg=theme["texte_faible"]
                )
            else:
                infos[
                    "titre"
                ].configure(
                    bg=infos[
                        "fond_original"
                    ],
                    fg=infos[
                        "texte_original"
                    ]
                )


    def niveaux_disponibles_pour_munition(
        munition
    ):
        affectations = affectations_interface()

        return [
            niveau
            for niveau in NIVEAUX_REPARTITION
            if niveau_repartition_disponible(
                niveau,
                affectations,
                ignorer_munition=munition
            )
        ]


    def recalculer_parts_affichees():
        quantites = lire_quantites_interface()

        poids_par_munition = {}
        total = 0.0

        annee, mois = (
            periode_chargee[0],
            periode_chargee[1]
        )

        for munition, variable in variables_niveaux.items():
            if modele_cle() == "STANDARD":
                poids = float(
                    lire_standard_mensuel_munition(
                        annee,
                        mois,
                        avion,
                        munition
                    ).get(
                        "quantite_reference",
                        0.0
                    )
                )
            else:
                poids = float(
                    quantites.get(
                        variable.get(),
                        0
                    )
                )

            poids = max(
                0.0,
                poids
            )

            poids_par_munition[
                munition
            ] = poids

            total += poids

        for munition, variable in variables_niveaux.items():
            niveau = variable.get()

            poids = poids_par_munition.get(
                munition,
                0.0
            )

            part = (
                poids
                / total
                * 100.0
                if total > 0
                else 0.0
            )

            infos = lignes_niveaux[
                munition
            ]

            infos[
                "label_part"
            ].configure(
                text=f"{part:.1f} %"
            )

            configurer_badge(
                infos[
                    "bouton_niveau"
                ],
                niveau
            )

            infos[
                "bouton_niveau"
            ].configure(
                text=nom_affiche_niveau_repartition(
                    niveau
                )
            )

        actualiser_disponibilite_priorites()

    def appliquer_etat_edition():
        editable = mode_est_editable()

        for niveau, widget in widgets_quantites.items():
            if niveau == "INDISPONIBLE":
                widget.configure(
                    state="disabled"
                )
            else:
                widget.configure(
                    state=(
                        "normal"
                        if editable
                        else "disabled"
                    )
                )

        for infos in lignes_niveaux.values():
            infos[
                "bouton_niveau"
            ].configure(
                state=(
                    "normal"
                    if editable
                    else "disabled"
                ),
                cursor=(
                    "hand2"
                    if editable
                    else "arrow"
                )
            )

        entree_nom.configure(
            state=(
                "normal"
                if editable
                else "disabled"
            )
        )

    def cycle_niveau_munition(
        munition
    ):
        if not mode_est_editable():
            return

        variable = variables_niveaux[
            munition
        ]

        niveaux_disponibles = (
            niveaux_disponibles_pour_munition(
                munition
            )
        )

        if not niveaux_disponibles:
            return

        niveau_actuel = variable.get()

        try:
            index_depart = list(
                NIVEAUX_REPARTITION
            ).index(
                niveau_actuel
            )
        except ValueError:
            index_depart = -1

        prochain = niveau_actuel

        for decalage in range(
            1,
            len(
                NIVEAUX_REPARTITION
            )
            + 1
        ):
            candidat = NIVEAUX_REPARTITION[
                (
                    index_depart
                    + decalage
                )
                % len(
                    NIVEAUX_REPARTITION
                )
            ]

            if candidat in niveaux_disponibles:
                prochain = candidat
                break

        variable.set(
            prochain
        )

        recalculer_parts_affichees()

    def reconstruire_tableau(
        affectations
    ):
        for enfant in contenu.winfo_children():
            enfant.destroy()

        variables_niveaux.clear()
        lignes_niveaux.clear()

        compatibles = trier_munitions_logiquement(
            AVIONS_EMPORTS.get(
                avion,
                []
            )
        )

        entete_tableau = tk.Frame(
            contenu,
            height=40,
            bg=theme["panneau_alt"]
        )

        entete_tableau.pack(
            fill="x",
            pady=(0, 4)
        )

        entete_tableau.pack_propagate(
            False
        )

        tk.Label(
            entete_tableau,
            text=t("common.ammunition"),
            font=(POLICE, 8, "bold"),
            anchor="w",
            bg=theme["panneau_alt"],
            fg=theme["texte_faible"]
        ).place(
            x=18,
            y=0,
            width=850,
            height=40
        )

        tk.Label(
            entete_tableau,
            text=t("model.importance"),
            font=(POLICE, 8, "bold"),
            bg=theme["panneau_alt"],
            fg=theme["texte_faible"]
        ).place(
            x=940,
            y=0,
            width=230,
            height=40
        )

        tk.Label(
            entete_tableau,
            text=t("model.estimated_share"),
            font=(POLICE, 8, "bold"),
            bg=theme["panneau_alt"],
            fg=theme["texte_faible"]
        ).place(
            x=1260,
            y=0,
            width=180,
            height=40
        )

        compte_categorie = {}

        for munition in compatibles:
            categorie = categorie_affichage_munition(
                munition
            )

            indice = compte_categorie.get(
                categorie,
                0
            )

            compte_categorie[
                categorie
            ] = (
                indice
                + 1
            )

            ligne = tk.Frame(
                contenu,
                height=68,
                bg=theme["panneau"],
                highlightbackground=theme["bordure"],
                highlightthickness=1
            )

            ligne.pack(
                fill="x",
                pady=2
            )

            ligne.pack_propagate(
                False
            )

            tk.Frame(
                ligne,
                width=5,
                bg=couleur_munition_stock(
                    munition,
                    indice
                )
            ).pack(
                side="left",
                fill="y"
            )

            tk.Label(
                ligne,
                text=t_munition(munition),
                font=(POLICE, 9, "bold"),
                anchor="w",
                bg=theme["panneau"],
                fg=theme["texte"]
            ).place(
                x=18,
                y=8,
                width=850,
                height=24
            )

            tk.Label(
                ligne,
                text=t_categorie(categorie).upper(),
                font=(POLICE, 7),
                anchor="w",
                bg=theme["panneau"],
                fg=theme["texte_faible"]
            ).place(
                x=18,
                y=35,
                width=850,
                height=18
            )

            niveau = affectations.get(
                munition,
                "NORMALE"
            )

            variable = tk.StringVar(
                value=niveau
            )

            variables_niveaux[
                munition
            ] = variable

            bouton_niveau = tk.Button(
                ligne,
                text=nom_affiche_niveau_repartition(
                    niveau
                ),
                command=lambda
                    m=munition:
                    cycle_niveau_munition(
                        m
                    ),
                font=(POLICE, 8, "bold"),
                relief="solid",
                borderwidth=1,
                cursor="hand2"
            )

            bouton_niveau.place(
                x=930,
                y=14,
                width=250,
                height=36
            )

            configurer_badge(
                bouton_niveau,
                niveau
            )

            label_part = tk.Label(
                ligne,
                text="0.0 %",
                font=(POLICE, 10, "bold"),
                bg=theme["panneau"],
                fg=theme["texte"]
            )

            label_part.place(
                x=1280,
                y=16,
                width=150,
                height=30
            )

            lignes_niveaux[
                munition
            ] = {
                "bouton_niveau": bouton_niveau,
                "label_part": label_part,
                "variable": variable
            }

        appliquer_etat_edition()
        recalculer_parts_affichees()
        ajuster_canvas()

        lier_molette_recursivement(
            contenu,
            canvas
        )

    def charger_periode(
        annee,
        mois,
        memoriser_avant=True
    ):
        if memoriser_avant:
            memoriser_periode_courante()

        cle_modele = modele_cle()

        donnees = (
            lire_periode_brouillon_ou_base(
                cle_modele,
                annee,
                mois
            )
        )

        for niveau in NIVEAUX_REPARTITION:
            valeur = int(
                round(
                    float(
                        donnees[
                            "quantites"
                        ].get(
                            niveau,
                            0.0
                        )
                    )
                )
            )

            if niveau == "INDISPONIBLE":
                valeur = 0

            variables_quantites[
                niveau
            ].set(
                valeur
            )

        periode_chargee[0] = int(
            annee
        )

        periode_chargee[1] = int(
            mois
        )

        variable_annee.set(
            int(
                annee
            )
        )

        variable_mois.set(
            t_mois(
                int(
                    mois
                )
            )
        )

        reconstruire_tableau(
            donnees[
                "affectations"
            ]
        )

        label_periode_info.configure(
            text=(
                f"{t_mois(int(mois))} {int(annee)}"
                + (
                    " • " + t("model.period.historical")
                    if cle_modele == "STANDARD"
                    else ""
                )
                + (
                    " • " + t("model.period.draft")
                    if (
                        (
                            int(
                                annee
                            ),
                            int(
                                mois
                            )
                        )
                        in brouillons_modeles.get(
                            cle_modele,
                            {}
                        )
                    )
                    else ""
                )
            )
        )

    def changement_periode(
        event=None
    ):
        annee, mois = (
            periode_selectionnee()
        )

        if (
            annee == periode_chargee[0]
            and mois == periode_chargee[1]
        ):
            return

        charger_periode(
            annee,
            mois,
            memoriser_avant=True
        )

    spin_annee.configure(
        command=changement_periode
    )

    spin_mois.configure(
        command=changement_periode
    )

    spin_annee.bind(
        "<Return>",
        changement_periode
    )

    spin_annee.bind(
        "<FocusOut>",
        changement_periode
    )

    # ========================================================
    # ACTIONS MODELE
    # ========================================================

    def rafraichir_mode(
        memoriser_avant=True
    ):
        if memoriser_avant:
            memoriser_periode_courante()

        cle_active = cle_modele_repartition_actif()

        if cle_active == "STANDARD":
            variable_mode.set(
                "STANDARD"
            )

            variable_nom_modele.set(
                t("model.create_with_plus")
            )

            bouton_mode._profil_repartition_actif = (
                "STANDARD"
            )

            bouton_mode.configure(
                text="STANDARD"
            )

            bouton_ajouter_modele.configure(
                state="normal",
                cursor="hand2"
            )

            bouton_supprimer_modele.configure(
                state="disabled",
                bg=theme["panneau_alt"],
                fg=theme["texte_faible"],
                cursor="arrow"
            )

            try:
                bouton_exporter.configure(
                    state="disabled",
                    fg=theme["texte_faible"],
                    cursor="arrow"
                )
            except Exception:
                pass

            label_etat.configure(
                text=t("model.status.standard"),
                fg=theme["texte_faible"]
            )

        else:
            variable_mode.set(
                "PERSONNALISE"
            )

            bouton_ajouter_modele.configure(
                state="normal",
                cursor="hand2"
            )

            bouton_mode._profil_repartition_actif = (
                cle_active
            )

            nom_actif = nom_profil_repartition(
                cle_active
            )

            variable_nom_modele.set(
                nom_actif
            )

            bouton_mode.configure(
                text=nom_actif
            )

            bouton_supprimer_modele.configure(
                state="normal",
                bg=theme["rouge"],
                fg=theme["blanc"],
                cursor="hand2"
            )

            try:
                bouton_exporter.configure(
                    state="normal",
                    fg=theme["texte"],
                    cursor="hand2"
                )
            except Exception:
                pass

            label_etat.configure(
                text=t("model.status.custom"),
                fg=theme["vert"]
            )

        charger_periode(
            periode_chargee[0],
            periode_chargee[1],
            memoriser_avant=False
        )

    def selectionner_mode_editeur(
        modele_selectionne
    ):
        memoriser_periode_courante()

        definir_modele_repartition_actif(
            modele_selectionne
        )

        rafraichir_mode(
            memoriser_avant=False
        )

    def ajouter_nouveau_modele_editeur():
        """
        Crée un modèle personnalisé pour n'importe quel joueur.

        Le MODE ADMIN n'est pas requis : les modèles personnalisés font
        partie du fonctionnement normal de l'application.
        """
        memoriser_periode_courante()

        modele, nom = (
            creer_nouveau_modele_repartition()
        )

        bouton_mode._profil_repartition_actif = (
            modele
        )

        variable_mode.set(
            "PERSONNALISE"
        )

        variable_nom_modele.set(
            nom
        )

        brouillons_modeles.setdefault(
            modele,
            {}
        )

        rafraichir_mode(
            memoriser_avant=False
        )

        try:
            entree_nom.focus_set()
            entree_nom.selection_range(
                0,
                "end"
            )
        except Exception:
            pass

    bouton_mode.configure(
        command=lambda:
        ouvrir_menu_profils_repartition(
            bouton_mode,
            selectionner_mode_editeur
        )
    )

    bouton_ajouter_modele.configure(
        command=ajouter_nouveau_modele_editeur
    )

    def supprimer_modele_editeur():
        cle_active = (
            profil_repartition_selectionne_depuis_bouton(
                bouton_mode
            )
        )

        if cle_active == "STANDARD":
            return

        nom_actif = nom_profil_repartition(
            cle_active
        )

        confirmer = dialogue_message_custom(
            t("model.delete.title"),
            t("model.delete.body", name=nom_actif),
            "question",
            fenetre_modele
        )

        if not confirmer:
            return

        if not supprimer_modele_repartition(
            cle_active
        ):
            dialogue_message_custom(
                t("model.delete.fail_title"),
                t("model.delete.fail_body"),
                "error",
                fenetre_modele
            )
            return

        brouillons_modeles.pop(
            cle_active,
            None
        )

        definir_modele_repartition_actif(
            "STANDARD"
        )

        rafraichir_mode(
            memoriser_avant=False
        )

    bouton_supprimer_modele.configure(
        command=supprimer_modele_editeur
    )

    # ========================================================
    # BARRE BASSE
    # ========================================================

    zone_actions = tk.Frame(
        corps,
        height=86,
        bg=theme["fond"]
    )

    zone_actions.pack(
        fill="x",
        padx=22,
        pady=(2, 14)
    )

    zone_actions.pack_propagate(
        False
    )

    tk.Label(
        zone_actions,
        text=t("model.name_label"),
        font=(POLICE, 7),
        anchor="w",
        bg=theme["fond"],
        fg=theme["texte_faible"]
    ).place(
        x=0,
        y=2,
        width=360,
        height=16
    )

    entree_nom = tk.Entry(
        zone_actions,
        textvariable=variable_nom_modele,
        font=(POLICE, 9, "bold"),
        bg=theme["champ"],
        fg=theme["champ_texte"],
        insertbackground=theme["texte"],
        disabledbackground=theme["panneau_alt"],
        disabledforeground=theme["texte_faible"],
        relief="solid",
        borderwidth=1
    )

    entree_nom.place(
        x=0,
        y=22,
        width=360,
        height=40
    )

    label_brouillons = tk.Label(
        zone_actions,
        text="",
        font=(POLICE, 8),
        anchor="w",
        bg=theme["fond"],
        fg=theme["texte_faible"]
    )

    label_brouillons.place(
        x=390,
        y=22,
        width=650,
        height=40
    )

    def actualiser_compteur_brouillons():
        cle = modele_cle()

        nombre = len(
            brouillons_modeles.get(
                cle,
                {}
            )
        )

        if nombre > 0:
            label_brouillons.configure(
                text=t(
                    "model.pending.count",
                    count=nombre
                ),
                fg=theme["vert"]
            )
        else:
            label_brouillons.configure(
                text=t("model.pending.none"),
                fg=theme["texte_faible"]
            )

    def enregistrer_configuration():
        if not mode_est_editable():
            dialogue_message_custom(
                t("model.standard.title"),
                t("model.standard.readonly"),
                "info",
                fenetre_modele
            )

            return

        memoriser_periode_courante()

        cle_active = modele_cle()

        if cle_active == "STANDARD":
            return

        brouillons = brouillons_modeles.get(
            cle_active,
            {}
        )

        if not brouillons:
            dialogue_message_custom(
                t("model.no_change.title"),
                t("model.no_change.body"),
                "info",
                fenetre_modele
            )

            return

        # Validation de TOUTES les périodes avant toute écriture.
        for (
            annee,
            mois
        ), donnees in brouillons.items():
            erreurs = verifier_limites_niveaux(
                donnees[
                    "affectations"
                ]
            )

            if erreurs:
                textes = [
                    (
                        f"{nom_affiche_niveau_repartition(niveau)} "
                        f": {utilise}/{maximum}"
                    )
                    for niveau, utilise, maximum
                    in erreurs
                ]

                dialogue_message_custom(
                    t("model.limit.title"),
                    t(
                        "model.limit.body",
                        period=f"{t_mois(mois)} {annee}",
                        details="\n".join(textes)
                    ),
                    "info",
                    fenetre_modele
                )

                charger_periode(
                    annee,
                    mois,
                    memoriser_avant=False
                )

                return

            total_reference = sum(
                donnees[
                    "quantites"
                ].get(
                    niveau,
                    0
                )
                for niveau
                in donnees[
                    "affectations"
                ].values()
            )

            if total_reference <= 0:
                dialogue_message_custom(
                    t("model.empty.title"),
                    t(
                        "model.empty.body",
                        period=f"{t_mois(mois)} {annee}"
                    ),
                    "info",
                    fenetre_modele
                )

                charger_periode(
                    annee,
                    mois,
                    memoriser_avant=False
                )

                return

        nom = (
            variable_nom_modele.get().strip()
            or "MODÈLE 1"
        )

        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        try:
            connexion.execute(
                "BEGIN IMMEDIATE"
            )

            curseur = connexion.cursor()

            curseur.execute(
                """
                UPDATE profils_repartition
                SET nom = ?
                WHERE modele = ?
                """,
                (
                    nom,
                    cle_active
                )
            )

            for (
                annee,
                mois
            ), donnees in brouillons.items():

                sauvegarder_quantites_niveaux_periode(
                    cle_active,
                    annee,
                    mois,
                    donnees[
                        "quantites"
                    ],
                    connexion=connexion
                )

                for munition, niveau in donnees[
                    "affectations"
                ].items():
                    curseur.execute(
                        """
                        INSERT INTO affectations_repartition (
                            modele,
                            annee,
                            mois,
                            avion,
                            munition,
                            niveau
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(
                            modele,
                            annee,
                            mois,
                            avion,
                            munition
                        )
                        DO UPDATE SET
                            niveau = excluded.niveau
                        """,
                        (
                            cle_active,
                            int(
                                annee
                            ),
                            int(
                                mois
                            ),
                            avion,
                            munition,
                            niveau
                        )
                    )

            connexion.commit()

        except sqlite3.Error as erreur:
            connexion.rollback()
            connexion.close()

            dialogue_message_custom(
                t("model.save_error.title"),
                t("model.save_error.body", error=str(erreur)),
                "error",
                fenetre_modele
            )

            return

        connexion.close()

        chemin_preset = None

        try:
            chemin_preset = exporter_preset_portable(
                cle_active
            )
        except Exception as erreur_export:
            dialogue_message_custom(
                t("model.portable_error.title"),
                t("model.portable_error.body", error=str(erreur_export)),
                "error",
                fenetre_modele
            )

        variable_nom_modele.set(
            nom
        )

        definir_modele_repartition_actif(
            cle_active
        )

        bouton_mode.configure(
            text=nom
        )

        nombre_periodes = len(
            brouillons
        )

        brouillons_modeles[
            cle_active
        ] = {}

        actualiser_compteur_brouillons()

        dialogue_message_custom(
            t("model.saved.title"),
            t(
                "model.saved.body",
                name=nom,
                count=nombre_periodes,
                portable=(
                    t("model.portable_path", path=str(chemin_preset))
                    if chemin_preset is not None
                    else ""
                )
            ),
            "info",
            fenetre_modele
        )

    def importer_preset_editeur():
        chemin = filedialog.askopenfilename(
            parent=fenetre_modele,
            title=t("model.import.dialog"),
            initialdir=str(
                dossier_presets_carriere()
            ),
            filetypes=(
                (
                    t("model.filetype.preset"),
                    "*.json"
                ),
                (
                    t("model.filetype.json"),
                    "*.json"
                ),
                (
                    t("model.filetype.all"),
                    "*.*"
                )
            )
        )

        if not chemin:
            return

        try:
            nouveau_modele, nouveau_nom = (
                importer_preset_portable(
                    chemin
                )
            )

        except Exception as erreur:
            dialogue_message_custom(
                t("model.import.fail_title"),
                t("model.import.fail_body", error=str(erreur)),
                "error",
                fenetre_modele
            )
            return

        bouton_mode._profil_repartition_actif = (
            nouveau_modele
        )

        variable_mode.set(
            "PERSONNALISE"
        )

        variable_nom_modele.set(
            nouveau_nom
        )

        brouillons_modeles.setdefault(
            nouveau_modele,
            {}
        )

        definir_modele_repartition_actif(
            nouveau_modele
        )

        rafraichir_mode(
            memoriser_avant=False
        )

        dialogue_message_custom(
            t("model.import.success_title"),
            t("model.import.success_body", name=nouveau_nom),
            "info",
            fenetre_modele
        )


    bouton_importer = tk.Button(
        zone_actions,
        text=t("model.import.button"),
        command=importer_preset_editeur,
        font=(POLICE, 8, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte"],
        activebackground=theme["bleu"],
        activeforeground=theme["blanc"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    )

    bouton_importer.place(
        x=1040,
        y=22,
        width=200,
        height=40
    )


    def exporter_preset_editeur():
        if not mode_est_editable():
            dialogue_message_custom(
                t("model.export.fail_title"),
                t("model.export.standard_body"),
                "info",
                fenetre_modele
            )
            return

        memoriser_periode_courante()

        cle_active = modele_cle()

        if cle_active == "STANDARD":
            return

        nom_preset = (
            variable_nom_modele.get().strip()
            or nom_profil_repartition(
                cle_active
            )
            or "Preset"
        )

        nom_suggere = nom_fichier_preset_portable(
            nom_preset,
            cle_active
        )

        chemin = filedialog.asksaveasfilename(
            parent=fenetre_modele,
            title=t("model.export.dialog"),
            initialfile=nom_suggere,
            defaultextension=".json",
            filetypes=(
                (
                    t("model.filetype.preset"),
                    "*.json"
                ),
                (
                    t("model.filetype.json"),
                    "*.json"
                ),
                (
                    t("model.filetype.all"),
                    "*.*"
                )
            )
        )

        if not chemin:
            return

        # Si l'utilisateur a des changements non encore enregistrés,
        # on lui demande d'enregistrer le modèle avant l'export afin
        # que le fichier partagé corresponde exactement à SQLite.
        brouillons = brouillons_modeles.get(
            cle_active,
            {}
        )

        if brouillons:
            dialogue_message_custom(
                t("model.export.unsaved_title"),
                t("model.export.unsaved_body"),
                "info",
                fenetre_modele
            )
            return

        try:
            destination = exporter_preset_vers(
                cle_active,
                chemin
            )

        except Exception as erreur:
            dialogue_message_custom(
                t("model.export.fail_title"),
                t("model.export.fail_body", error=str(erreur)),
                "error",
                fenetre_modele
            )
            return

        dialogue_message_custom(
            t("model.export.success_title"),
            t("model.export.success_body", path=str(destination)),
            "info",
            fenetre_modele
        )


    bouton_exporter = tk.Button(
        zone_actions,
        text=t("model.export.button"),
        command=exporter_preset_editeur,
        font=(POLICE, 8, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte"],
        activebackground=theme["bleu"],
        activeforeground=theme["blanc"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    )

    bouton_exporter.place(
        x=830,
        y=22,
        width=200,
        height=40
    )


    bouton_enregistrer = tk.Button(
        zone_actions,
        text=t("model.save_all"),
        command=enregistrer_configuration,
        font=(POLICE, 9, "bold"),
        bg=theme["rouge"],
        fg=theme["blanc"],
        activebackground=theme["rouge"],
        activeforeground=theme["blanc"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    )

    bouton_enregistrer.place(
        x=1260,
        y=22,
        width=360,
        height=40
    )

    # Les modifications de quantité recalculent immédiatement les parts.
    for spin in widgets_quantites.values():
        spin.bind(
            "<KeyRelease>",
            lambda event:
            (
                recalculer_parts_affichees(),
                actualiser_compteur_brouillons()
            )
        )

        spin.bind(
            "<ButtonRelease-1>",
            lambda event:
            fenetre_modele.after(
                20,
                recalculer_parts_affichees
            )
        )

    # Chargement initial sur le mois réel de la carrière.
    charger_periode(
        annee_courante,
        mois_courant,
        memoriser_avant=False
    )

    rafraichir_mode(
        memoriser_avant=False
    )

    actualiser_compteur_brouillons()




# ============================================================
# PERFORMANCE UI / CACHES
# ============================================================

_CACHE_IMAGES_PIL = {}
_CACHE_PHOTOIMAGES = {}
_CACHE_DONUTS_PIL = {}

FICHIER_LOG_PERFORMANCE_UI = DOSSIER_LOGS / "ui_performance.log"


def journaliser_performance_ui(nom_fenetre, debut):
    """Journal léger des temps de construction des fenêtres secondaires."""
    try:
        duree_ms = (time.perf_counter() - float(debut)) * 1000.0
        DOSSIER_LOGS.mkdir(exist_ok=True)
        with FICHIER_LOG_PERFORMANCE_UI.open("a", encoding="utf-8") as fichier:
            fichier.write(
                f"{datetime.now().isoformat(timespec='seconds')} | "
                f"{nom_fenetre} | {duree_ms:.1f} ms\n"
            )
    except Exception:
        pass


def charger_image_pil_cache(chemin, mode="RGBA"):
    """Charge une image disque une seule fois et renvoie toujours une copie PIL."""
    chemin = Path(chemin)
    try:
        signature = (str(chemin.resolve()), int(chemin.stat().st_mtime_ns), str(mode))
    except Exception:
        signature = (str(chemin), 0, str(mode))

    image = _CACHE_IMAGES_PIL.get(signature)
    if image is None:
        image = Image.open(chemin).convert(mode)
        _CACHE_IMAGES_PIL[signature] = image.copy()

    return image.copy()


def creer_photoimage_cache(chemin, largeur, hauteur, mode="contain"):
    """Cache le chargement et le redimensionnement des assets statiques."""
    chemin = Path(chemin)
    try:
        mtime = int(chemin.stat().st_mtime_ns)
    except Exception:
        mtime = 0

    cle = (
        str(chemin.resolve()) if chemin.exists() else str(chemin),
        mtime,
        int(largeur),
        int(hauteur),
        str(mode),
    )

    photo = _CACHE_PHOTOIMAGES.get(cle)
    if photo is not None:
        return photo

    image = charger_image_pil_cache(chemin, "RGBA")

    if mode == "career_banner":
        hauteur_source = max(
            1,
            int(round(image.height * 0.65))
        )
        image = image.crop((0, 0, image.width, hauteur_source))
        image = adapter_image_cover(image, int(largeur), int(hauteur))
    elif mode == "cover":
        image = adapter_image_cover(image, int(largeur), int(hauteur))
    else:
        image = adapter_image_contain(image, int(largeur), int(hauteur))

    photo = ImageTk.PhotoImage(image)
    _CACHE_PHOTOIMAGES[cle] = photo
    return photo


def vider_caches_graphiques_dynamiques():
    """Les donuts dépendent des couleurs du thème actif."""
    _CACHE_DONUTS_PIL.clear()


# ============================================================
# OUTILS IMAGES
# ============================================================

def adapter_image_cover(image, largeur_cible, hauteur_cible):
    facteur = max(
        largeur_cible / image.width,
        hauteur_cible / image.height
    )

    nouvelle_largeur = round(image.width * facteur)
    nouvelle_hauteur = round(image.height * facteur)

    image = image.resize(
        (nouvelle_largeur, nouvelle_hauteur),
        Image.Resampling.LANCZOS
    )

    gauche = (nouvelle_largeur - largeur_cible) // 2
    haut = (nouvelle_hauteur - hauteur_cible) // 2

    return image.crop(
        (
            gauche,
            haut,
            gauche + largeur_cible,
            haut + hauteur_cible
        )
    )


def adapter_image_contain(image, largeur_cible, hauteur_cible):
    image = image.copy()

    image.thumbnail(
        (largeur_cible, hauteur_cible),
        Image.Resampling.LANCZOS
    )

    return image


def creer_icone_munition(nom_munition, couleur=None, taille=34):
    """
    Charge directement l'icône PNG transparente depuis images/ordnance.
    La couleur du PNG est conservée telle quelle.
    """
    donnees = MUNITIONS.get(nom_munition)

    if not donnees:
        return None

    chemin = DOSSIER_MUNITIONS / donnees["icone"]

    if not chemin.exists():
        return None

    try:
        return creer_photoimage_cache(
            chemin,
            taille,
            taille,
            mode="contain"
        )

    except Exception:
        return None


# ============================================================
# SPLASH
# ============================================================

def afficher_splash():
    splash = tk.Toplevel(fenetre)
    splash.overrideredirect(True)

    # La fenêtre principale est encore cachée hors écran à ce stade.
    # On utilise donc le moniteur sous le curseur comme référence pour
    # garantir que le splash apparaît réellement au centre de l'écran utilisé.
    try:
        point_splash = (
            int(fenetre.winfo_pointerx()),
            int(fenetre.winfo_pointery())
        )
    except Exception:
        point_splash = None

    zone_splash = _zone_travail_moniteur(
        point_ecran=point_splash
    )
    facteur_splash = _facteur_pour_zone_travail(
        LARGEUR_SPLASH,
        HAUTEUR_SPLASH,
        zone_splash
    )
    largeur_splash = max(320, int(round(LARGEUR_SPLASH * facteur_splash)))
    hauteur_splash = max(220, int(round(HAUTEUR_SPLASH * facteur_splash)))

    _centrer_dans_zone_travail(
        splash,
        largeur_splash,
        hauteur_splash,
        parent=fenetre,
        zone_travail=zone_splash
    )

    splash.attributes("-topmost", True)

    try:
        splash.lift()
        splash.focus_force()
    except Exception:
        pass

    canvas = tk.Canvas(
        splash,
        width=largeur_splash,
        height=hauteur_splash,
        highlightthickness=0,
        borderwidth=0,
        bg="#111111"
    )

    canvas.pack(fill="both", expand=True)

    # Contour très fin du splash, cohérent avec le thème actif.
    canvas.create_rectangle(
        0,
        0,
        largeur_splash - 1,
        hauteur_splash - 1,
        outline=theme["contour_fenetre"],
        width=1
    )

    reference_fond = {"image": None}

    try:
        fond = Image.open(FICHIER_FOND_SPLASH).convert("RGB")

        fond = adapter_image_cover(
            fond,
            largeur_splash,
            hauteur_splash
        )

        reference_fond["image"] = ImageTk.PhotoImage(fond, master=splash)

        canvas.create_image(
            0,
            0,
            image=reference_fond["image"],
            anchor="nw"
        )

    except Exception:
        pass

    try:
        image_logo = Image.open(
            FICHIER_LOGO_SPLASH
        ).convert("RGBA")

    except Exception:
        image_logo = None

    centre_x = largeur_splash // 2
    centre_y = hauteur_splash // 2

    item_logo = canvas.create_image(
        centre_x,
        centre_y - int(round(45 * facteur_splash))
    )

    canvas.create_text(
        centre_x,
        centre_y + int(round(45 * facteur_splash)),
        text=t("startup.loading"),
        font=(POLICE, max(9, int(round(14 * facteur_splash))), "bold"),
        fill="#ffffff"
    )

    item_points = canvas.create_text(
        centre_x,
        centre_y + int(round(72 * facteur_splash)),
        text="",
        font=(POLICE, max(8, int(round(13 * facteur_splash))), "bold"),
        fill="#ffffff"
    )

    canvas.create_text(
        18,
        hauteur_splash - 16,
        text=VERSION_APPLICATION,
        anchor="sw",
        font=(POLICE, max(7, int(round(8 * facteur_splash)))),
        fill="#d0cec8"
    )

    # Le contour final est redessiné au premier plan après le fond.
    canvas.create_rectangle(
        0,
        0,
        largeur_splash - 1,
        hauteur_splash - 1,
        outline=theme["contour_fenetre"],
        width=1
    )

    reference_logo = {"image": None}
    debut = time.perf_counter()

    def animer():
        temps = time.perf_counter() - debut

        if (
            image_logo is not None
            and temps < DUREE_PULSE
        ):
            frequence = NOMBRE_PULSES / DUREE_PULSE

            progression = (
                1
                - math.cos(
                    2 * math.pi * frequence * temps
                )
            ) / 2

            facteur = (
                1.0
                + AGRANDISSEMENT_PULSE * progression
            )

            taille = round(
                TAILLE_LOGO_SPLASH * facteur_splash * facteur
            )

            logo = image_logo.copy()

            logo.thumbnail(
                (taille, taille),
                Image.Resampling.LANCZOS
            )

            reference_logo["image"] = (
                ImageTk.PhotoImage(logo, master=splash)
            )

            canvas.itemconfig(
                item_logo,
                image=reference_logo["image"]
            )

        canvas.itemconfig(
            item_points,
            text="." * (int(temps * 3) % 4)
        )

        if temps >= DUREE_SPLASH:
            splash.destroy()
            return

        splash.after(16, animer)

    animer()

    fenetre.wait_window(splash)


# ============================================================
# HÔTE WINDOWS PERSISTANT
# ============================================================
#
# Cette fenêtre Tk existe AVANT le splash et reste la même jusqu'à la
# fermeture du programme. C'est elle qui possède le bouton Windows dans
# la barre des tâches.
#
# Pendant le splash et la sélection de carrière, elle est simplement
# minimisée et placée hors écran. Après la sélection de carrière, elle
# devient directement l'interface principale.
# ============================================================

# Identité Windows de l'application.
# L'AppUserModelID aide Windows à associer correctement l'icône de
# l'exécutable à la fenêtre et aux raccourcis dans la barre des tâches.
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "hawax270.IL2KoreaALM"
    )
except Exception:
    pass

fenetre = tk.Tk()

fenetre.title(
    t("app.window_title")
)

# Icône de la fenêtre / barre des tâches.
# Le .ico est également intégré directement dans l'exécutable par
# PyInstaller (voir IL2_Korea_Ammunition_Logistics_Manager.spec).
try:
    fenetre.iconbitmap(
        default=str(DOSSIER_IMAGES / "app_icon.ico")
    )
except Exception:
    pass

# iconphoto sert de complément pour Tk et conserve correctement
# la transparence du logo. La référence est gardée sur la fenêtre pour
# éviter que Tkinter ne libère l'image.
try:
    _icone_application_pil = Image.open(
        DOSSIER_IMAGES / "app_icon.png"
    ).convert("RGBA")
    _icone_application_tk = ImageTk.PhotoImage(
        _icone_application_pil,
        master=fenetre
    )
    fenetre.iconphoto(
        True,
        _icone_application_tk
    )
    fenetre._icone_application_tk = _icone_application_tk
except Exception:
    pass

# Une vraie fenêtre Tk classique possède naturellement un bouton
# dans la barre des tâches Windows.
fenetre.geometry(
    "1x1+-32000+-32000"
)

fenetre.resizable(
    False,
    False
)

fenetre.update_idletasks()

# La racine reste active pour Windows pendant le splash et la liaison,
# mais elle est invisible à l'écran.
try:
    fenetre.attributes(
        "-alpha",
        0.0
    )
except Exception:
    pass


def afficher_chargement_carriere(
    donnees_carriere,
    fonction_chargement,
    duree_minimale=5.0
):
    """Affiche le chargement carrière à chaque lancement.

    Le backend de préparation tourne dans un worker. Tkinter reste
    exclusivement sur le thread principal. L'écran dure au minimum
    ``duree_minimale`` secondes et attend plus longtemps si nécessaire.
    """
    avion = str(
        donnees_carriere.get(
            "avion",
            t("startup.unknown_aircraft")
        )
        or t("startup.unknown_aircraft")
    )

    date_jeu = str(
        donnees_carriere.get("date_jeu", "")
        or ""
    )

    try:
        date_affichee = datetime.strptime(
            date_jeu[:10],
            "%Y.%m.%d"
        ).strftime("%d.%m.%Y")
    except Exception:
        date_affichee = date_jeu or t("startup.unknown_date")

    popup = tk.Toplevel(fenetre)

    # Sous Windows, une Toplevel overrideredirect créée alors que la racine
    # principale est encore invisible peut être réalisée en (0, 0).
    # On la construit donc cachée, puis on la centre juste avant affichage.
    popup.withdraw()
    popup.overrideredirect(True)

    largeur = 690
    hauteur = 290

    popup.configure(
        bg=theme["barre"]
    )

    cadre = tk.Frame(
        popup,
        bg=theme["panneau"],
        highlightbackground=theme["contour_fenetre"],
        highlightthickness=1
    )
    cadre.pack(fill="both", expand=True, padx=1, pady=1)

    largeur_interieure = 688
    hauteur_banniere = 188

    zone_banniere = tk.Canvas(
        cadre,
        width=largeur_interieure,
        height=hauteur_banniere,
        bg=theme["panneau"],
        highlightthickness=0,
        borderwidth=0
    )
    zone_banniere.pack(fill="x")

    chemin_banniere = chemin_banniere_chargement_avion(avion)
    banniere_chargee = False

    if chemin_banniere is not None:
        try:
            photo_banniere = creer_photoimage_cache(
                chemin_banniere,
                largeur_interieure,
                hauteur_banniere,
                mode="career_banner"
            )
            zone_banniere.create_image(
                largeur_interieure // 2,
                hauteur_banniere // 2,
                image=photo_banniere,
                anchor="center"
            )
            zone_banniere._photo_banniere = photo_banniere
            banniere_chargee = True
        except Exception:
            banniere_chargee = False

    couleur_titre = theme["blanc"] if banniere_chargee else theme["texte"]
    couleur_info = theme["blanc"] if banniere_chargee else theme["bleu"]

    if banniere_chargee:
        zone_banniere.create_text(
            23, 137,
            text=t("startup.new_career.title"),
            font=(POLICE, 16, "bold"),
            fill="#000000",
            anchor="sw"
        )
        zone_banniere.create_text(
            23, 166,
            text=f"{avion}   •   {date_affichee}",
            font=(POLICE, 9, "bold"),
            fill="#000000",
            anchor="sw"
        )

    zone_banniere.create_text(
        22, 136,
        text=t("startup.new_career.title"),
        font=(POLICE, 16, "bold"),
        fill=couleur_titre,
        anchor="sw"
    )
    zone_banniere.create_text(
        22, 165,
        text=f"{avion}   •   {date_affichee}",
        font=(POLICE, 9, "bold"),
        fill=couleur_info,
        anchor="sw"
    )

    zone_chargement = tk.Frame(cadre, bg=theme["panneau"])
    zone_chargement.pack(fill="both", expand=True)

    label_etape = tk.Label(
        zone_chargement,
        text=t("startup.new_career.preparing"),
        font=(POLICE, 8),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    )
    label_etape.pack(pady=(8, 7))

    fond_barre = tk.Frame(
        zone_chargement,
        width=550,
        height=14,
        bg=theme["champ"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )
    fond_barre.pack()
    fond_barre.pack_propagate(False)

    barre = tk.Frame(fond_barre, bg=theme["bleu"])
    barre.place(x=0, y=0, width=1, height=12)

    tk.Label(
        zone_chargement,
        text=t("startup.new_career.factory"),
        font=(POLICE, 7),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(pady=(8, 0))

    # --------------------------------------------------------
    # CENTRAGE APRÈS CONSTRUCTION COMPLÈTE
    # --------------------------------------------------------

    popup.update_idletasks()

    # 1. adaptation et position avant affichage. Sur les écrans usuels le
    # facteur reste 1.0 ; sur un très petit écran la fenêtre et ses contrôles
    # sont réduits ensemble.
    adapter_fenetre_simple_ecran(
        popup,
        largeur,
        hauteur,
        parent=fenetre,
        adapter_contenu=True
    )
    geometrie_centree = popup.geometry()

    popup.geometry(
        geometrie_centree
    )

    # 2. réalisation réelle de la Toplevel par Windows
    popup.deiconify()
    popup.update_idletasks()

    # 3. réapplication immédiate après réalisation pour empêcher
    #    Windows/Tk de la replacer en haut à gauche.
    popup.geometry(
        geometrie_centree
    )

    popup.lift()
    popup.update()

    file_resultat = queue.Queue(maxsize=1)

    def travail_chargement():
        try:
            resultat = fonction_chargement()
            file_resultat.put(("ok", resultat, ""))
        except BaseException as erreur:
            file_resultat.put(
                ("erreur", erreur, traceback.format_exc())
            )

    thread_chargement = threading.Thread(
        target=travail_chargement,
        name="chargement-carriere",
        daemon=True
    )
    thread_chargement.start()

    etapes = (
        (0.00, t("startup.new_career.step.read")),
        (0.22, t("startup.new_career.step.db")),
        (0.46, t("startup.new_career.step.standard")),
        (0.70, t("startup.new_career.step.stock")),
        (0.90, t("startup.new_career.step.finish")),
    )

    index_etape = 0
    debut = time.monotonic()
    statut = None
    resultat = None
    erreur_trace = ""

    while True:
        ecoule = time.monotonic() - debut

        if statut is None:
            try:
                statut, resultat, erreur_trace = file_resultat.get_nowait()
            except queue.Empty:
                pass

        termine = statut is not None

        if termine and ecoule >= duree_minimale:
            progression = 1.0
        else:
            progression = min(
                0.94,
                (ecoule / max(0.1, float(duree_minimale))) * 0.94
            )

        while (
            index_etape + 1 < len(etapes)
            and progression >= etapes[index_etape + 1][0]
        ):
            index_etape += 1

        label_etape.configure(text=etapes[index_etape][1])
        barre.place_configure(
            width=max(1, int(548 * progression))
        )

        popup.update_idletasks()
        popup.update()

        if progression >= 1.0:
            break

        time.sleep(0.02)

    label_etape.configure(
        text=t("startup.new_career.step.finish")
    )
    barre.place_configure(width=548)
    popup.update_idletasks()
    popup.update()
    time.sleep(0.12)
    popup.destroy()

    if statut == "erreur":
        raise RuntimeError(
            "Erreur pendant le chargement de la carrière.\n\n"
            + erreur_trace
        ) from resultat

    return resultat


# ============================================================
# INITIALISATION
# ============================================================

# Ordre de démarrage :
# 1. Splash IL-2 Korea
# 2. Sélection / analyse de la carrière
# 3. Initialisation de la base locale
# 4. Interface principale

afficher_splash()


ANCIEN_CHEMIN_CARRIERE_CONFIG = str(
    config.get(
        "carriere_fichier",
        ""
    )
    or ""
)


DONNEES_CARRIERE_IL2 = (
    selectionner_carriere_avant_demarrage()
)

if DONNEES_CARRIERE_IL2 is None:
    try:
        fenetre.destroy()
    except Exception:
        pass

    raise SystemExit


# ------------------------------------------------------------
# APPAREIL DE LA CARRIÈRE
# ------------------------------------------------------------

avion_detecte = DONNEES_CARRIERE_IL2.get("avion")

if avion_detecte is not None and avion_detecte in AVIONS:
    avion_selectionne = avion_detecte
    config["avion"] = avion_detecte
    sauvegarder_config()


# ------------------------------------------------------------
# CHARGEMENT DE LA CARRIÈRE
# ------------------------------------------------------------

def charger_carriere_demarrage():
    """Prépare le backend de carrière sans appel Tkinter."""
    rafraichir_date_carriere_en_memoire()

    nouvelle_carriere_locale = (
        not base_locale_carriere_existe(DONNEES_CARRIERE_IL2)
    )

    migration_base_heritage = configurer_base_locale_carriere(
        DONNEES_CARRIERE_IL2,
        ANCIEN_CHEMIN_CARRIERE_CONFIG
    )

    initialiser_base()

    if nouvelle_carriere_locale and not migration_base_heritage:
        appliquer_valeurs_usine_nouvelle_carriere(
            DONNEES_CARRIERE_IL2
        )

    if migration_base_heritage:
        normaliser_cles_base_migree(
            DONNEES_CARRIERE_IL2
        )

    enregistrer_meta_carriere_locale(
        DONNEES_CARRIERE_IL2
    )

    resultat_synchro = synchroniser_stock_avec_carriere(
        DONNEES_CARRIERE_IL2
    )

    mettre_a_jour_reference_capacite_carriere(
        DONNEES_CARRIERE_IL2
    )

    return {
        "nouvelle_carriere_locale": nouvelle_carriere_locale,
        "migration_base_heritage": migration_base_heritage,
        "resultat_synchro": resultat_synchro,
    }


RESULTATS_CHARGEMENT_CARRIERE = afficher_chargement_carriere(
    DONNEES_CARRIERE_IL2,
    charger_carriere_demarrage,
    duree_minimale=5.0
)

NOUVELLE_CARRIERE_LOCALE = (
    RESULTATS_CHARGEMENT_CARRIERE["nouvelle_carriere_locale"]
)
MIGRATION_BASE_HERITAGE = (
    RESULTATS_CHARGEMENT_CARRIERE["migration_base_heritage"]
)
RESULTAT_SYNCHRO_CARRIERE = (
    RESULTATS_CHARGEMENT_CARRIERE["resultat_synchro"]
)


# ============================================================
# FENETRE PRINCIPALE
# ============================================================

# La fenêtre Windows créée avant le splash devient maintenant
# l'interface principale. Le HWND / bouton de barre des tâches est donc
# conservé au lieu de recréer une nouvelle application Windows.
try:
    fenetre.attributes(
        "-alpha",
        1.0
    )
except Exception:
    pass

fenetre.deiconify()
fenetre.overrideredirect(True)
fenetre.resizable(False, False)

# La fenêtre principale conserve sa base logique 1600x900, mais sa taille
# physique est automatiquement réduite si le moniteur courant est plus petit.
adapter_fenetre_principale_ecran(
    adapter_contenu=False
)


fenetre_options_ouverte = None
fenetre_selection_avion_ouverte = None
fenetre_stock_ouverte = None
fenetre_ajout_emport_ouverte = None

# Surveillance temps réel de la carrière.
surveillance_carriere_active = True
surveillance_carriere_en_cours = False
surveillance_carriere_after_id = None
popup_evolution_en_cours = False

# File thread -> interface.
file_surveillance_carriere = queue.Queue()

# Dernière valeur IL-2 réellement acceptée par le watcher temps réel.
reference_ammo_temps_reel = None


# ============================================================
# DEPLACEMENT
# ============================================================

deplacement = {
    "x": 0,
    "y": 0
}


def debut_deplacement(event):
    deplacement["x"] = (
        event.x_root - fenetre.winfo_x()
    )
    deplacement["y"] = (
        event.y_root - fenetre.winfo_y()
    )


def deplacer(event):
    x = event.x_root - deplacement["x"]
    y = event.y_root - deplacement["y"]

    fenetre.geometry(
        f"+{x}+{y}"
    )


def minimiser():
    fenetre.overrideredirect(False)
    fenetre.iconify()


def restaurer(event=None):
    if fenetre.state() == "normal":
        fenetre.after(
            10,
            lambda: fenetre.overrideredirect(True)
        )


fenetre.bind("<Map>", restaurer)



# ============================================================
# CONTOURS DES FENETRES
# ============================================================

fenetres_avec_contour = []


def rehausser_contour_fenetre(fenetre_cible):
    """
    Replace les 4 traits du contour au premier plan.
    Utile car les grands Frames de contenu peuvent être créés après
    le contour et donc le masquer.
    """
    try:
        if not fenetre_cible.winfo_exists():
            return

        if not hasattr(
            fenetre_cible,
            "_contour_il2"
        ):
            return

        for ligne in fenetre_cible._contour_il2:
            ligne.lift()

    except Exception:
        pass


def ajouter_contour_fenetre(fenetre_cible):
    """
    Ajoute un contour interne de 1 px autour d'une fenêtre custom.

    Le contour reste toujours au premier plan, même si des Frames
    plein écran sont ajoutés ensuite.
    """
    if (
        hasattr(fenetre_cible, "_contour_il2")
        and fenetre_cible._contour_il2
    ):
        rehausser_contour_fenetre(
            fenetre_cible
        )
        return


    haut = tk.Frame(
        fenetre_cible,
        bg=theme["contour_fenetre"],
        height=1,
        borderwidth=0,
        highlightthickness=0
    )

    bas = tk.Frame(
        fenetre_cible,
        bg=theme["contour_fenetre"],
        height=1,
        borderwidth=0,
        highlightthickness=0
    )

    gauche = tk.Frame(
        fenetre_cible,
        bg=theme["contour_fenetre"],
        width=1,
        borderwidth=0,
        highlightthickness=0
    )

    droite = tk.Frame(
        fenetre_cible,
        bg=theme["contour_fenetre"],
        width=1,
        borderwidth=0,
        highlightthickness=0
    )


    # Le contour est placé 1 px à l'intérieur de la fenêtre.
    # Cela évite qu'une partie soit coupée par le bord du Toplevel.
    haut.place(
        x=0,
        y=0,
        relwidth=1,
        height=1
    )

    bas.place(
        x=0,
        rely=1,
        y=-1,
        relwidth=1,
        height=1
    )

    gauche.place(
        x=0,
        y=0,
        width=1,
        relheight=1
    )

    droite.place(
        relx=1,
        x=-1,
        y=0,
        width=1,
        relheight=1
    )


    fenetre_cible._contour_il2 = [
        haut,
        bas,
        gauche,
        droite
    ]


    if fenetre_cible not in fenetres_avec_contour:
        fenetres_avec_contour.append(
            fenetre_cible
        )


    def rehausser_plus_tard(event=None):
        try:
            fenetre_cible.after_idle(
                lambda:
                rehausser_contour_fenetre(
                    fenetre_cible
                )
            )
        except Exception:
            pass


    # Quand la fenêtre change, remappe ou reçoit de nouveaux éléments,
    # on remonte le contour.
    fenetre_cible.bind(
        "<Configure>",
        rehausser_plus_tard,
        add="+"
    )

    fenetre_cible.bind(
        "<Map>",
        rehausser_plus_tard,
        add="+"
    )


    # Plusieurs passages volontaires : certaines fenêtres ajoutent leur
    # contenu après le chrome custom et pourraient sinon recouvrir le bord.
    fenetre_cible.after(
        1,
        lambda:
        rehausser_contour_fenetre(
            fenetre_cible
        )
    )

    fenetre_cible.after(
        30,
        lambda:
        rehausser_contour_fenetre(
            fenetre_cible
        )
    )

    fenetre_cible.after(
        100,
        lambda:
        rehausser_contour_fenetre(
            fenetre_cible
        )
    )


def actualiser_contours_fenetres():
    """
    Met immédiatement à jour la couleur de tous les contours
    lorsque le thème change.
    """
    for fenetre_cible in list(
        fenetres_avec_contour
    ):
        try:
            if not fenetre_cible.winfo_exists():
                fenetres_avec_contour.remove(
                    fenetre_cible
                )
                continue

            for ligne in fenetre_cible._contour_il2:
                ligne.configure(
                    bg=theme["contour_fenetre"]
                )

            rehausser_contour_fenetre(
                fenetre_cible
            )

        except Exception:
            try:
                fenetres_avec_contour.remove(
                    fenetre_cible
                )
            except ValueError:
                pass


# ============================================================
# FENETRES SECONDAIRES / DIALOGUES CUSTOM
# ============================================================

def centrer_fenetre_secondaire(fenetre_secondaire, largeur, hauteur):
    """Centre la fenêtre sur le moniteur où se trouve son parent."""
    parent = getattr(
        fenetre_secondaire,
        "master",
        fenetre
    )

    zone = _zone_travail_moniteur(
        fenetre_secondaire,
        parent=parent
    )

    return _centrer_dans_zone_travail(
        fenetre_secondaire,
        largeur,
        hauteur,
        parent=parent,
        zone_travail=zone,
    )


def ajuster_fenetre_custom_au_contenu(
    fenetre_secondaire,
    marge_x=24,
    marge_y=24
):
    """Dimensionnement fiable des fenêtres custom.

    Le nom de la fonction est conservé pour compatibilité, mais elle ne mesure
    plus le contenu. Chaque fenêtre possède une taille de référence explicite.
    On applique le profil demandé puis, si nécessaire, un seul facteur pour
    tenir dans la zone utile du moniteur. Le même facteur est ensuite appliqué
    au layout.

    Résultat : pas de croissance cumulative, pas de fenêtre géante avec une
    petite zone de contenu, et pas de géométrie différente selon la police
    installée sur la machine.
    """
    del marge_x, marge_y  # conservés uniquement pour l'ancienne signature

    try:
        if not fenetre_secondaire.winfo_exists():
            return

        fenetre_secondaire._adaptation_ecran_en_cours = True

        largeur_base, hauteur_base = getattr(
            fenetre_secondaire,
            "_taille_base_custom",
            (
                max(1, fenetre_secondaire.winfo_width()),
                max(1, fenetre_secondaire.winfo_height()),
            )
        )

        facteur_fenetre = float(facteur_taille_fenetres())
        facteur_police = float(facteur_taille_police())

        largeur_reference = max(
            1,
            int(round(float(largeur_base) * facteur_fenetre))
        )
        hauteur_reference = max(
            1,
            int(round(float(hauteur_base) * facteur_fenetre))
        )

        parent = getattr(
            fenetre_secondaire,
            "master",
            fenetre
        )
        zone = _zone_travail_moniteur(
            fenetre_secondaire,
            parent=parent
        )

        facteur_ecran = _facteur_pour_zone_travail(
            largeur_reference,
            hauteur_reference,
            zone
        )
        facteur_layout = facteur_fenetre * float(facteur_ecran)
        facteur_police_effectif = min(
            facteur_police,
            max(
                FACTEUR_ECRAN_MINIMUM,
                facteur_layout * RATIO_POLICE_MAX_PAR_LAYOUT
            )
        )

        largeur_cible = max(
            240,
            int(round(float(largeur_base) * facteur_layout))
        )
        hauteur_cible = max(
            180,
            int(round(float(hauteur_base) * facteur_layout))
        )

        fenetre_secondaire._facteur_auto_ecran = facteur_ecran
        fenetre_secondaire._facteur_layout_effectif = facteur_layout
        fenetre_secondaire._taille_min_custom = (
            largeur_cible,
            hauteur_cible
        )

        _adapter_mise_en_page_widget_ecran(
            fenetre_secondaire,
            facteur_layout
        )
        _appliquer_taille_police_widget(
            fenetre_secondaire,
            facteur_police_effectif
        )

        _centrer_dans_zone_travail(
            fenetre_secondaire,
            largeur_cible,
            hauteur_cible,
            parent=parent,
            zone_travail=zone,
        )

        fenetre_secondaire._zone_moniteur_adaptative = zone

    except Exception:
        pass
    finally:
        try:
            fenetre_secondaire._adaptation_ecran_en_cours = False
        except Exception:
            pass

def appliquer_chrome_custom(
    fenetre_secondaire,
    titre,
    largeur,
    hauteur,
    commande_fermeture=None
):
    """
    Supprime la barre Windows et crée une barre IL-2 cohérente
    avec le thème actif.
    """
    fenetre_secondaire.overrideredirect(True)
    fenetre_secondaire.resizable(False, False)
    fenetre_secondaire.configure(
        bg=theme["fond"]
    )

    # Une seule taille de référence par fenêtre. Le profil et la taille du
    # moniteur sont appliqués de manière déterministe ; aucun contenu n'est
    # mesuré pour décider de la géométrie.
    fenetre_secondaire._taille_base_custom = (
        int(largeur),
        int(hauteur)
    )

    facteur_fenetre = float(facteur_taille_fenetres())
    zone_initiale = _zone_travail_moniteur(
        fenetre_secondaire,
        parent=getattr(fenetre_secondaire, "master", fenetre)
    )
    largeur_reference = max(1, int(round(float(largeur) * facteur_fenetre)))
    hauteur_reference = max(1, int(round(float(hauteur) * facteur_fenetre)))
    facteur_ecran_initial = _facteur_pour_zone_travail(
        largeur_reference,
        hauteur_reference,
        zone_initiale
    )
    facteur_layout_initial = facteur_fenetre * facteur_ecran_initial
    largeur_affichee = max(240, int(round(float(largeur) * facteur_layout_initial)))
    hauteur_affichee = max(180, int(round(float(hauteur) * facteur_layout_initial)))

    fenetre_secondaire._taille_min_custom = (
        largeur_affichee,
        hauteur_affichee
    )

    _centrer_dans_zone_travail(
        fenetre_secondaire,
        largeur_affichee,
        hauteur_affichee,
        parent=getattr(fenetre_secondaire, "master", fenetre),
        zone_travail=zone_initiale,
    )

    ajouter_contour_fenetre(
        fenetre_secondaire
    )

    barre = tk.Frame(
        fenetre_secondaire,
        height=38,
        bg=theme["barre"]
    )

    barre.pack(
        fill="x",
        side="top"
    )

    barre.pack_propagate(False)

    label_titre = tk.Label(
        barre,
        text=titre.upper(),
        font=(POLICE, 10, "bold"),
        anchor="w",
        padx=14,
        bg=theme["barre"],
        fg=theme["blanc"]
    )

    label_titre.pack(
        side="left",
        fill="both",
        expand=True
    )

    def fermer():
        if commande_fermeture is not None:
            commande_fermeture()
        else:
            fenetre_secondaire.destroy()

    bouton_fermer_local = tk.Button(
        barre,
        text="✕",
        command=fermer,
        font=(POLICE, 11, "bold"),
        relief="flat",
        borderwidth=0,
        cursor="hand2",
        bg=theme["barre"],
        fg=theme["blanc"],
        activebackground=theme["rouge"],
        activeforeground=theme["blanc"]
    )

    bouton_fermer_local.pack(
        side="right",
        fill="y",
        ipadx=12
    )


    fenetre_secondaire.after_idle(
        lambda:
        rehausser_contour_fenetre(
            fenetre_secondaire
        )
    )

    # Une seule passe différée, après construction des widgets, applique le
    # facteur de layout définitif. Aucune mesure de contenu n'intervient.
    fenetre_secondaire.after(
        80,
        lambda f=fenetre_secondaire:
        ajuster_fenetre_custom_au_contenu(
            f
        )
    )

    _installer_suivi_moniteur(
        fenetre_secondaire,
        lambda f=fenetre_secondaire:
        ajuster_fenetre_custom_au_contenu(
            f
        )
    )

    deplacement_local = {
        "x": 0,
        "y": 0
    }

    def debut(event):
        deplacement_local["x"] = (
            event.x_root
            - fenetre_secondaire.winfo_x()
        )

        deplacement_local["y"] = (
            event.y_root
            - fenetre_secondaire.winfo_y()
        )

    def bouger(event):
        x = (
            event.x_root
            - deplacement_local["x"]
        )

        y = (
            event.y_root
            - deplacement_local["y"]
        )

        fenetre_secondaire.geometry(
            f"+{x}+{y}"
        )

    for widget in (
        barre,
        label_titre
    ):
        widget.bind(
            "<Button-1>",
            debut
        )

        widget.bind(
            "<B1-Motion>",
            bouger
        )

    return barre


def dialogue_message_custom(
    titre,
    message,
    type_dialogue="info",
    parent=None
):
    """
    Dialogue custom :
    - info / warning / error -> bouton OK
    - question -> OUI / NON et renvoie True/False
    """
    if parent is None:
        parent = fenetre

    resultat = {
        "valeur": False
    }

    dialogue = tk.Toplevel(
        parent
    )

    largeur = 520

    # La boîte générique ne doit plus supposer que 250 px suffisent
    # quelle que soit la longueur du message.
    lignes_estimees = max(
        1,
        sum(
            max(
                1,
                (
                    len(
                        ligne
                    )
                    // 54
                )
                + 1
            )
            for ligne in str(
                message
            ).split(
                "\n"
            )
        )
    )

    hauteur = max(
        250,
        min(
            640,
            185
            + lignes_estimees
            * 22
        )
    )

    def fermer_non():
        resultat["valeur"] = False
        dialogue.destroy()

    appliquer_chrome_custom(
        dialogue,
        titre,
        largeur,
        hauteur,
        fermer_non
    )

    corps = tk.Frame(
        dialogue,
        bg=theme["panneau"]
    )

    corps.pack(
        fill="both",
        expand=True
    )

    couleur = theme["texte"]

    if type_dialogue == "warning":
        couleur = theme["texte"]

    elif type_dialogue == "error":
        couleur = theme["rouge"]

    tk.Label(
        corps,
        text=message,
        font=(POLICE, 10),
        justify="center",
        wraplength=440,
        bg=theme["panneau"],
        fg=couleur
    ).pack(
        fill="both",
        expand=True,
        padx=30,
        pady=(28, 18)
    )

    zone_boutons = tk.Frame(
        corps,
        bg=theme["panneau"]
    )

    zone_boutons.pack(
        pady=(0, 24)
    )

    if type_dialogue == "question":
        def oui():
            resultat["valeur"] = True
            dialogue.destroy()

        tk.Button(
            zone_boutons,
            text=t("common.yes"),
            command=oui,
            font=(POLICE, 9, "bold"),
            width=10,
            bg=theme["panneau_alt"],
            fg=theme["texte"],
            activebackground=theme["champ"],
            activeforeground=theme["texte"],
            relief="solid",
            borderwidth=1
        ).pack(
            side="left",
            padx=6,
            ipady=5
        )

        tk.Button(
            zone_boutons,
            text=t("common.no"),
            command=fermer_non,
            font=(POLICE, 9, "bold"),
            width=10,
            bg=theme["panneau"],
            fg=theme["texte"],
            activebackground=theme["panneau_alt"],
            activeforeground=theme["texte"],
            relief="solid",
            borderwidth=1
        ).pack(
            side="left",
            padx=6,
            ipady=5
        )

    else:
        tk.Button(
            zone_boutons,
            text=t("common.ok"),
            command=lambda: dialogue.destroy(),
            font=(POLICE, 9, "bold"),
            width=12,
            bg=theme["panneau_alt"],
            fg=theme["texte"],
            activebackground=theme["champ"],
            activeforeground=theme["texte"],
            relief="solid",
            borderwidth=1
        ).pack(
            ipadx=8,
            ipady=5
        )

    dialogue.transient(parent)
    dialogue.grab_set()
    dialogue.focus_force()
    dialogue.wait_window()

    return resultat["valeur"]


# ============================================================
# MISES À JOUR GITHUB
# ============================================================

file_mise_a_jour = queue.Queue()
verification_mise_a_jour_en_cours = False
telechargement_mise_a_jour_en_cours = False
info_mise_a_jour_disponible = None
bouton_mise_a_jour = None

_ui_telechargement_mise_a_jour = {
    "popup": None,
    "label": None,
    "barre": None,
    "pourcentage": None,
}


def _parent_mise_a_jour_valide(parent):
    try:
        if parent is not None and parent.winfo_exists():
            return parent
    except Exception:
        pass

    return fenetre


def actualiser_bouton_mise_a_jour():
    """Met à jour l'apparence du bouton UPDATE de la barre basse."""
    try:
        if (
            bouton_mise_a_jour is None
            or not bouton_mise_a_jour.winfo_exists()
        ):
            return
    except Exception:
        return

    disponible = isinstance(
        info_mise_a_jour_disponible,
        dict
    )

    if disponible:
        bouton_mise_a_jour.configure(
            bg=theme["rouge"],
            fg=theme["blanc"],
            activebackground=theme["rouge"],
            activeforeground=theme["blanc"],
            relief="solid",
            borderwidth=1
        )
    else:
        bouton_mise_a_jour.configure(
            bg=theme["barre"],
            fg=theme["blanc"],
            activebackground=theme["panneau_alt"],
            activeforeground=theme["blanc"],
            relief="flat",
            borderwidth=0
        )


def action_bouton_mise_a_jour():
    """Ouvre l'update connue ou lance une vérification manuelle."""
    if isinstance(
        info_mise_a_jour_disponible,
        dict
    ):
        afficher_dialogue_mise_a_jour(
            info_mise_a_jour_disponible,
            fenetre
        )
        return

    demarrer_verification_mise_a_jour(
        manuelle=True,
        parent=fenetre
    )


def demarrer_verification_mise_a_jour(
    manuelle=False,
    parent=None
):
    global verification_mise_a_jour_en_cours

    if verification_mise_a_jour_en_cours:
        return False

    verification_mise_a_jour_en_cours = True

    def worker():
        try:
            resultat = updater.verifier_derniere_version(
                VERSION_APPLICATION
            )

            file_mise_a_jour.put(
                (
                    "verification_ok",
                    bool(manuelle),
                    parent,
                    resultat
                )
            )
        except Exception as erreur:
            file_mise_a_jour.put(
                (
                    "verification_erreur",
                    bool(manuelle),
                    parent,
                    str(erreur)
                )
            )

    threading.Thread(
        target=worker,
        name="github-update-check",
        daemon=True
    ).start()

    return True


def afficher_dialogue_mise_a_jour(
    info,
    parent=None
):
    parent = _parent_mise_a_jour_valide(parent)

    dialogue = tk.Toplevel(parent)

    appliquer_chrome_custom(
        dialogue,
        t("update.available.title"),
        580,
        390,
        dialogue.destroy
    )

    corps = tk.Frame(
        dialogue,
        bg=theme["panneau"]
    )
    corps.pack(
        fill="both",
        expand=True
    )

    tk.Label(
        corps,
        text=t("update.available.title"),
        font=(POLICE, 16, "bold"),
        bg=theme["panneau"],
        fg=theme["vert"]
    ).pack(
        pady=(28, 12)
    )

    tk.Label(
        corps,
        text=t(
            "update.available.body"
        ).format(
            current=VERSION_APPLICATION,
            latest=info.get(
                "latest_version",
                "?"
            )
        ),
        font=(POLICE, 9),
        justify="center",
        wraplength=490,
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        padx=30,
        pady=(0, 20)
    )

    zone_boutons = tk.Frame(
        corps,
        bg=theme["panneau"]
    )
    zone_boutons.pack(
        pady=(4, 26)
    )

    def telecharger():
        dialogue.destroy()

        demarrer_telechargement_mise_a_jour(
            info,
            parent
        )

    tk.Button(
        zone_boutons,
        text=t("update.available.later"),
        command=dialogue.destroy,
        font=(POLICE, 8, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte"],
        activebackground=theme["champ"],
        activeforeground=theme["texte"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    ).pack(
        side="left",
        padx=6,
        ipadx=16,
        ipady=7
    )

    tk.Button(
        zone_boutons,
        text=t("update.available.download"),
        command=telecharger,
        font=(POLICE, 8, "bold"),
        bg=theme["vert"],
        fg=theme["blanc"],
        activebackground=theme["vert"],
        activeforeground=theme["blanc"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    ).pack(
        side="left",
        padx=6,
        ipadx=14,
        ipady=7
    )

    dialogue.transient(parent)
    dialogue.lift()
    dialogue.focus_force()


def _fermer_popup_telechargement_mise_a_jour():
    popup = _ui_telechargement_mise_a_jour.get("popup")

    try:
        if popup is not None and popup.winfo_exists():
            popup.destroy()
    except Exception:
        pass

    for cle in (
        "popup",
        "label",
        "barre",
        "pourcentage"
    ):
        _ui_telechargement_mise_a_jour[
            cle
        ] = None


def demarrer_telechargement_mise_a_jour(
    info,
    parent=None
):
    global telechargement_mise_a_jour_en_cours

    if telechargement_mise_a_jour_en_cours:
        return

    telechargement_mise_a_jour_en_cours = True
    parent = _parent_mise_a_jour_valide(parent)

    popup = tk.Toplevel(parent)

    appliquer_chrome_custom(
        popup,
        t("update.download.title"),
        560,
        280,
        lambda: None
    )

    corps = tk.Frame(
        popup,
        bg=theme["panneau"]
    )
    corps.pack(
        fill="both",
        expand=True
    )

    label = tk.Label(
        corps,
        text=t("update.download.preparing"),
        font=(POLICE, 10, "bold"),
        justify="center",
        wraplength=470,
        bg=theme["panneau"],
        fg=theme["texte"]
    )
    label.pack(
        padx=25,
        pady=(42, 20)
    )

    fond_barre = tk.Frame(
        corps,
        width=440,
        height=16,
        bg=theme["champ"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )
    fond_barre.pack()
    fond_barre.pack_propagate(False)

    barre = tk.Frame(
        fond_barre,
        bg=theme["vert"]
    )
    barre.place(
        x=0,
        y=0,
        width=1,
        height=14
    )

    pourcentage = tk.Label(
        corps,
        text="0 %",
        font=(POLICE, 8, "bold"),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    )
    pourcentage.pack(
        pady=(12, 20)
    )

    _ui_telechargement_mise_a_jour.update(
        {
            "popup": popup,
            "label": label,
            "barre": barre,
            "pourcentage": pourcentage,
        }
    )

    popup.transient(parent)
    popup.lift()

    def progression(telecharge, total):
        file_mise_a_jour.put(
            (
                "telechargement_progression",
                int(telecharge),
                int(total),
                info
            )
        )

    def worker():
        try:
            chemin = updater.telecharger_installeur(
                info,
                DOSSIER_DONNEES / "updates",
                progression=progression
            )

            file_mise_a_jour.put(
                (
                    "telechargement_ok",
                    str(chemin),
                    info
                )
            )
        except Exception as erreur:
            file_mise_a_jour.put(
                (
                    "telechargement_erreur",
                    str(erreur),
                    info
                )
            )

    threading.Thread(
        target=worker,
        name="github-update-download",
        daemon=True
    ).start()


def traiter_resultats_mise_a_jour():
    global verification_mise_a_jour_en_cours
    global telechargement_mise_a_jour_en_cours
    global info_mise_a_jour_disponible

    try:
        while True:
            evenement = file_mise_a_jour.get_nowait()
            type_evenement = evenement[0]

            if type_evenement == "verification_ok":
                _, manuelle, parent, info = evenement
                verification_mise_a_jour_en_cours = False

                if info.get("status") == "available":
                    info_mise_a_jour_disponible = info
                    actualiser_bouton_mise_a_jour()

                    # La vérification automatique reste discrète :
                    # le bouton UPDATE devient rouge et attend un clic.
                    if manuelle:
                        afficher_dialogue_mise_a_jour(
                            info,
                            parent
                        )

                else:
                    info_mise_a_jour_disponible = None
                    actualiser_bouton_mise_a_jour()

                    if manuelle:
                        dialogue_message_custom(
                            t("update.check.up_to_date.title"),
                            t(
                                "update.check.up_to_date.body"
                            ).format(
                                current=VERSION_APPLICATION,
                                latest=info.get(
                                    "latest_version",
                                    VERSION_APPLICATION
                                )
                            ),
                            "info",
                            _parent_mise_a_jour_valide(parent)
                        )

            elif type_evenement == "verification_erreur":
                _, manuelle, parent, erreur = evenement
                verification_mise_a_jour_en_cours = False

                if manuelle:
                    dialogue_message_custom(
                        t("update.check.error.title"),
                        t(
                            "update.check.error.body"
                        ).format(
                            error=erreur
                        ),
                        "warning",
                        _parent_mise_a_jour_valide(parent)
                    )

            elif type_evenement == "telechargement_progression":
                _, telecharge, total, info = evenement

                label = _ui_telechargement_mise_a_jour.get(
                    "label"
                )
                barre = _ui_telechargement_mise_a_jour.get(
                    "barre"
                )
                pourcentage = _ui_telechargement_mise_a_jour.get(
                    "pourcentage"
                )

                if label is not None:
                    label.configure(
                        text=t(
                            "update.download.body"
                        ).format(
                            version=info.get(
                                "latest_version",
                                ""
                            )
                        )
                    )

                if total > 0:
                    ratio = min(
                        1.0,
                        max(
                            0.0,
                            telecharge / total
                        )
                    )

                    if barre is not None:
                        barre.place_configure(
                            width=max(
                                1,
                                int(
                                    438 * ratio
                                )
                            )
                        )

                    if pourcentage is not None:
                        pourcentage.configure(
                            text=f"{int(ratio * 100)} %"
                        )

                elif pourcentage is not None:
                    pourcentage.configure(
                        text=(
                            f"{telecharge / (1024 * 1024):.1f} MB"
                        )
                    )

            elif type_evenement == "telechargement_ok":
                _, chemin, _ = evenement
                telechargement_mise_a_jour_en_cours = False

                barre = _ui_telechargement_mise_a_jour.get(
                    "barre"
                )
                pourcentage = _ui_telechargement_mise_a_jour.get(
                    "pourcentage"
                )

                if barre is not None:
                    barre.place_configure(
                        width=438
                    )

                if pourcentage is not None:
                    pourcentage.configure(
                        text="100 %"
                    )

                try:
                    updater.lancer_installeur(
                        chemin
                    )
                except Exception as erreur:
                    _fermer_popup_telechargement_mise_a_jour()

                    dialogue_message_custom(
                        t("update.download.error.title"),
                        t(
                            "update.download.error.body"
                        ).format(
                            error=str(erreur)
                        ),
                        "error",
                        fenetre
                    )
                    continue

                fenetre.after(
                    300,
                    fenetre.destroy
                )

            elif type_evenement == "telechargement_erreur":
                _, erreur, _ = evenement
                telechargement_mise_a_jour_en_cours = False

                _fermer_popup_telechargement_mise_a_jour()

                dialogue_message_custom(
                    t("update.download.error.title"),
                    t(
                        "update.download.error.body"
                    ).format(
                        error=erreur
                    ),
                    "error",
                    fenetre
                )

    except queue.Empty:
        pass

    finally:
        try:
            fenetre.after(
                250,
                traiter_resultats_mise_a_jour
            )
        except Exception:
            pass



def afficher_popup_evolution_carriere():
    global popup_evolution_en_cours

    """
    Affiche le delta détecté entre le dernier snapshot IL-2
    et la carrière actuellement chargée.
    """

    if popup_evolution_en_cours:
        return
    resultat = RESULTAT_SYNCHRO_CARRIERE

    if not resultat:
        return

    type_changement = resultat.get(
        "type_changement",
        "aucun"
    )

    if type_changement == "aucun":
        return


    popup_evolution_en_cours = True


    popup = tk.Toplevel(
        fenetre
    )

    def fermer_popup_evolution():
        global popup_evolution_en_cours

        popup_evolution_en_cours = False

        try:
            if popup.winfo_exists():
                popup.destroy()
        except Exception:
            pass


    appliquer_chrome_custom(
        popup,
        t("stock_evolution.window"),
        610,
        500,
        fermer_popup_evolution
    )


    corps = tk.Frame(
        popup,
        bg=theme["panneau"]
    )

    corps.pack(
        fill="both",
        expand=True
    )


    ancienne = resultat.get(
        "ancienne_valeur"
    )

    nouvelle = int(
        resultat.get(
            "nouvelle_valeur",
            0
        )
    )

    delta = int(
        resultat.get(
            "delta",
            0
        )
    )


    if type_changement == "initialisation":
        titre = (
            "STOCK DE CARRIÈRE INITIALISÉ"
        )

        resume = (
            f"IL-2 : {nouvelle} unités de munitions\\n"
            "Le stock concret a été généré pour cette carrière."
        )

        couleur = theme[
            "vert"
        ]

    elif type_changement == "appareil_change":
        titre = (
            "APPAREIL DE CARRIÈRE MODIFIÉ"
        )

        resume = (
            f"{ancienne} → {nouvelle} unités IL-2\\n"
            "Le stock a été reconstruit pour le nouvel appareil."
        )

        couleur = theme[
            "bleu"
        ]

    elif type_changement == "diminution_reference":
        titre = (
            "CONSOMMATION IL-2 DÉTECTÉE"
        )

        resume = (
            f"{ancienne} → {nouvelle} unités IL-2"
            f"   ({delta})\n"
            "Le stock détaillé n'a pas été modifié."
        )

        couleur = theme[
            "rouge"
        ]

    else:
        signe = (
            "+"
            if delta > 0
            else ""
        )

        titre = (
            "LE STOCK DE MUNITIONS A ÉVOLUÉ"
        )

        resume = (
            f"{ancienne} → {nouvelle} unités IL-2"
            f"   ({signe}{delta})"
        )

        couleur = (
            theme["vert"]
            if delta > 0
            else theme["rouge"]
        )


    tk.Label(
        corps,
        text=titre,
        font=(POLICE, 15, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(24, 6)
    )


    tk.Label(
        corps,
        text=resume,
        font=(POLICE, 11, "bold"),
        justify="center",
        bg=theme["panneau"],
        fg=couleur
    ).pack(
        pady=(0, 16)
    )


    tk.Frame(
        corps,
        height=1,
        bg=theme["separateur"]
    ).pack(
        fill="x",
        padx=24
    )


    tk.Label(
        corps,
        text=t("stock_evolution.title"),
        font=(POLICE, 8, "bold"),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(14, 8)
    )


    zone_liste = tk.Frame(
        corps,
        bg=theme["panneau"]
    )

    zone_liste.pack(
        fill="both",
        expand=True,
        padx=30
    )


    changements = resultat.get(
        "changements",
        {}
    )


    if not changements:
        texte_aucun_changement = (
            "AUCUNE MODIFICATION DU STOCK DÉTAILLÉ"
            if type_changement == "diminution_reference"
            else "AUCUNE MODIFICATION CONCRÈTE À AFFICHER"
        )

        tk.Label(
            zone_liste,
            text=texte_aucun_changement,
            font=(POLICE, 9, "bold"),
            bg=theme["panneau"],
            fg=theme["texte_faible"]
        ).pack(
            pady=(32, 8)
        )

        if type_changement == "diminution_reference":
            tk.Label(
                zone_liste,
                text=t("stock_evolution.abstract_notice"),
                font=(POLICE, 8),
                justify="center",
                bg=theme["panneau"],
                fg=theme["texte_faible"]
            ).pack(
                pady=(0, 20)
            )

    else:
        ordre = trier_munitions_logiquement(
            list(
                changements.keys()
            )
        )

        for nom in ordre:
            valeur = int(
                changements[
                    nom
                ]
            )

            ligne = tk.Frame(
                zone_liste,
                height=32,
                bg=theme["panneau"]
            )

            ligne.pack(
                fill="x",
                pady=1
            )

            ligne.pack_propagate(
                False
            )


            categorie = categorie_affichage_munition(
                nom
            )

            couleur_ligne = couleur_munition_stock(
                nom,
                0
            )


            tk.Frame(
                ligne,
                width=5,
                bg=couleur_ligne
            ).pack(
                side="left",
                fill="y"
            )


            tk.Label(
                ligne,
                text=nom,
                font=(POLICE, 8),
                anchor="w",
                bg=theme["panneau"],
                fg=theme["texte"]
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=(9, 5)
            )


            signe = (
                "+"
                if valeur > 0
                else ""
            )


            tk.Label(
                ligne,
                text=(
                    f"{signe}{valeur}"
                ),
                font=(POLICE, 10, "bold"),
                width=8,
                anchor="e",
                bg=theme["panneau"],
                fg=(
                    theme["vert"]
                    if valeur > 0
                    else theme["rouge"]
                )
            ).pack(
                side="right",
                padx=5
            )


    tk.Button(
        corps,
        text=t("common.continue"),
        command=fermer_popup_evolution,
        font=(POLICE, 9, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte"],
        activebackground=theme["champ"],
        activeforeground=theme["texte"],
        relief="solid",
        borderwidth=1
    ).pack(
        pady=18,
        ipadx=20,
        ipady=6
    )


    popup.transient(
        fenetre
    )

    # IMPORTANT :
    # Ce popup est volontairement NON MODAL.
    # Un grab_set() pendant un callback de surveillance périodique peut
    # laisser Tkinter bloqué si une autre fenêtre est détruite/recréée.
    #
    # On se contente donc de placer la notification au-dessus sans
    # empêcher l'utilisateur de continuer à manipuler l'application.
    try:
        popup.lift()
        popup.attributes(
            "-topmost",
            True
        )

        popup.after(
            250,
            lambda:
            popup.attributes(
                "-topmost",
                False
            )
            if popup.winfo_exists()
            else None
        )
    except Exception:
        pass


def dialogue_saisie_custom(
    titre,
    message,
    parent=None
):
    if parent is None:
        parent = fenetre

    resultat = {
        "texte": None
    }

    dialogue = tk.Toplevel(
        parent
    )

    largeur = 520
    hauteur = 270

    def fermer():
        resultat["texte"] = None
        dialogue.destroy()

    appliquer_chrome_custom(
        dialogue,
        titre,
        largeur,
        hauteur,
        fermer
    )

    corps = tk.Frame(
        dialogue,
        bg=theme["panneau"]
    )

    corps.pack(
        fill="both",
        expand=True
    )

    tk.Label(
        corps,
        text=message,
        font=(POLICE, 10),
        justify="center",
        wraplength=440,
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        padx=25,
        pady=(28, 14)
    )

    champ = tk.Entry(
        corps,
        font=(POLICE, 11, "bold"),
        justify="center",
        bg=theme["champ"],
        fg=theme["champ_texte"],
        insertbackground=theme["champ_texte"],
        relief="solid",
        borderwidth=1
    )

    champ.pack(
        padx=55,
        fill="x",
        ipady=6
    )

    zone_boutons = tk.Frame(
        corps,
        bg=theme["panneau"]
    )

    zone_boutons.pack(
        pady=22
    )

    def valider():
        valeur = champ.get().strip()

        if not valeur:
            return

        resultat["texte"] = valeur
        dialogue.destroy()

    tk.Button(
        zone_boutons,
        text=t("common.validate"),
        command=valider,
        font=(POLICE, 9, "bold"),
        width=12,
        bg=theme["panneau_alt"],
        fg=theme["texte"],
        activebackground=theme["champ"],
        activeforeground=theme["texte"],
        relief="solid",
        borderwidth=1
    ).pack(
        side="left",
        padx=6,
        ipady=5
    )

    tk.Button(
        zone_boutons,
        text=t("common.cancel"),
        command=fermer,
        font=(POLICE, 9, "bold"),
        width=12,
        bg=theme["panneau"],
        fg=theme["texte"],
        activebackground=theme["panneau_alt"],
        activeforeground=theme["texte"],
        relief="solid",
        borderwidth=1
    ).pack(
        side="left",
        padx=6,
        ipady=5
    )

    champ.bind(
        "<Return>",
        lambda event:
        valider()
    )

    dialogue.transient(parent)
    dialogue.grab_set()
    dialogue.after(
        80,
        champ.focus_force
    )
    dialogue.wait_window()

    return resultat["texte"]


# Contour fin de la fenêtre principale.
ajouter_contour_fenetre(
    fenetre
)


# ============================================================
# LISTES DE WIDGETS DU THEME
# ============================================================

widgets_fond = []
widgets_panneau = []
widgets_panneau_alt = []
widgets_barre = []
widgets_texte_faible = []
widgets_bordure = []
widgets_separateur = []
widgets_champ = []
widgets_bouton = []
widgets_barre_bouton = []


def creer_separateur(parent):
    ligne = tk.Frame(
        parent,
        height=1,
        bg=theme["separateur"]
    )

    widgets_separateur.append(ligne)
    return ligne


def bouton_style(parent, texte, commande):
    bouton = tk.Button(
        parent,
        text=texte,
        command=commande,
        font=POLICE_PETIT,
        fg=theme["texte"],
        bg=theme["panneau"],
        activeforeground=theme["texte"],
        activebackground=theme["panneau_alt"],
        relief="solid",
        borderwidth=1,
        highlightthickness=0,
        cursor="hand2"
    )

    widgets_bouton.append(bouton)
    return bouton




# ============================================================
# INTEGRATION WINDOWS / BARRE DES TACHES
# ============================================================

def forcer_presence_barre_des_taches(fenetre_cible):
    """
    Force Windows à considérer la fenêtre principale borderless
    comme une vraie fenêtre d'application.

    La fenêtre conserve overrideredirect(True) et notre chrome custom.
    """
    if os.name != "nt":
        return

    try:
        fenetre_cible.update_idletasks()

        # winfo_id() retourne la fenêtre enfant Tk.
        # GetParent permet de récupérer la vraie fenêtre de niveau supérieur
        # gérée par Windows.
        hwnd_tk = int(
            fenetre_cible.winfo_id()
        )

        hwnd = ctypes.windll.user32.GetParent(
            hwnd_tk
        )

        if not hwnd:
            hwnd = hwnd_tk

        GWL_EXSTYLE = -20

        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_APPWINDOW = 0x00040000

        style = ctypes.windll.user32.GetWindowLongW(
            hwnd,
            GWL_EXSTYLE
        )

        style &= ~WS_EX_TOOLWINDOW
        style |= WS_EX_APPWINDOW

        ctypes.windll.user32.SetWindowLongW(
            hwnd,
            GWL_EXSTYLE,
            style
        )

        # Demande à Windows de recalculer le style de la fenêtre.
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOZORDER = 0x0004
        SWP_FRAMECHANGED = 0x0020

        ctypes.windll.user32.SetWindowPos(
            hwnd,
            0,
            0,
            0,
            0,
            0,
            (
                SWP_NOMOVE
                | SWP_NOSIZE
                | SWP_NOZORDER
                | SWP_FRAMECHANGED
            )
        )

        # Le cycle withdraw/deiconify force Windows à créer/rafraîchir
        # le bouton de barre des tâches.
        fenetre_cible.withdraw()

        fenetre_cible.after(
            30,
            fenetre_cible.deiconify
        )

    except Exception as erreur:
        # Le correctif de barre des tâches ne doit jamais faire planter
        # l'application. On garde simplement la fenêtre telle quelle.
        print(
            "Correctif barre des tâches ignoré :",
            erreur
        )


# Force l'application principale à apparaître dans la barre des tâches Windows.
fenetre.after(
    250,
    lambda:
    forcer_presence_barre_des_taches(
        fenetre
    )
)


# ============================================================
# BARRE HAUTE
# ============================================================

barre_haut = tk.Frame(fenetre)

barre_haut.place(
    x=0,
    y=0,
    width=LARGEUR_FENETRE,
    height=HAUTEUR_BARRE_HAUT
)

widgets_barre.append(barre_haut)


label_titre_app = tk.Label(
    barre_haut,
    text=t("app.title"),
    font=(POLICE, 17, "bold")
)

label_titre_app.place(
    x=34,
    y=16
)

widgets_barre.append(label_titre_app)


nom_escadrille = str(
    (DONNEES_CARRIERE_IL2 or {}).get(
        "nom_escadrille",
        ""
    )
    or ""
).strip()

if not nom_escadrille:
    nom_escadrille = t("main.generic_squadron")

label_escadrille = tk.Label(
    barre_haut,
    text=f"({nom_escadrille})",
    font=(POLICE, 9, "bold"),
    anchor="e"
)

label_escadrille.place(
    x=1185,
    y=21,
    width=265
)

widgets_barre.append(label_escadrille)


bouton_min = tk.Button(
    barre_haut,
    text="—",
    command=minimiser,
    font=(POLICE, 13, "bold"),
    relief="flat",
    borderwidth=0
)

bouton_min.place(
    x=1500,
    y=0,
    width=45,
    height=HAUTEUR_BARRE_HAUT
)

widgets_barre_bouton.append(bouton_min)


bouton_fermer = tk.Button(
    barre_haut,
    text="✕",
    command=fenetre.destroy,
    font=(POLICE, 12, "bold"),
    relief="flat",
    borderwidth=0
)

bouton_fermer.place(
    x=1545,
    y=0,
    width=55,
    height=HAUTEUR_BARRE_HAUT
)

widgets_barre_bouton.append(bouton_fermer)


for widget in [
    barre_haut,
    label_titre_app
]:
    widget.bind(
        "<Button-1>",
        debut_deplacement
    )
    widget.bind(
        "<B1-Motion>",
        deplacer
    )


# ============================================================
# GRAND TITRE
# ============================================================

label_grand_titre = tk.Label(
    fenetre,
    text=t("main.title"),
    font=POLICE_TITRE
)

label_grand_titre.place(
    x=0,
    y=77,
    width=LARGEUR_FENETRE,
    height=40
)

widgets_fond.append(label_grand_titre)


# ============================================================
# COLONNE GAUCHE
# ============================================================

cadre_gauche = tk.Frame(fenetre)

cadre_gauche.place(
    x=25,
    y=130,
    width=390,
    height=685
)

widgets_fond.append(cadre_gauche)


# ============================================================
# APPAREIL
# ============================================================

cadre_appareil = tk.Frame(
    cadre_gauche,
    highlightthickness=1
)

cadre_appareil.place(
    x=0,
    y=0,
    width=390,
    height=300
)

widgets_panneau.append(cadre_appareil)
widgets_bordure.append(cadre_appareil)


label_appareil_titre = tk.Label(
    cadre_appareil,
    text=t("main.aircraft.title"),
    font=POLICE_SECTION
)

label_appareil_titre.place(
    x=20,
    y=15
)

widgets_panneau.append(label_appareil_titre)


cadre_image_avion = tk.Frame(
    cadre_appareil,
    highlightthickness=1
)

cadre_image_avion.place(
    x=20,
    y=43,
    width=350,
    height=125
)


label_image_avion = tk.Label(
    cadre_image_avion
)

label_image_avion.place(
    x=1,
    y=1,
    width=346,
    height=121
)


image_avion_principale = None


def actualiser_image_avion():
    global image_avion_principale

    chemin = AVIONS[
        avion_selectionne
    ]["image"]

    if not chemin.exists():
        label_image_avion.configure(
            image="",
            text=t("main.aircraft.image_unavailable"),
            font=POLICE_PETIT,
            fg=theme["texte_faible"],
            bg=theme["champ"]
        )

        image_avion_principale = None
        return

    try:
        image_avion_principale = creer_photoimage_cache(
            chemin,
            338,
            113,
            mode="contain"
        )

        label_image_avion.configure(
            image=image_avion_principale,
            text="",
            bg=theme["champ"]
        )

    except Exception:
        label_image_avion.configure(
            image="",
            text=t("main.aircraft.image_error"),
            font=POLICE_PETIT,
            fg=theme["rouge"],
            bg=theme["champ"]
        )


bouton_selection_avion = tk.Button(
    cadre_appareil,
    text="",
    font=(POLICE, 11, "bold"),
    anchor="center",
    padx=8,
    relief="solid",
    borderwidth=1,
    cursor="hand2"
)

bouton_selection_avion.place(
    x=20,
    y=180,
    width=350,
    height=42
)

widgets_panneau_alt.append(
    bouton_selection_avion
)


creer_separateur(
    cadre_appareil
).place(
    x=20,
    y=236,
    width=350
)


# ============================================================
# GESTION DE LA MOLETTE SUR LES LISTES SCROLLABLES
# ============================================================

def defiler_canvas_avec_molette(canvas, event):
    """
    Défile un Canvas avec la molette Windows.
    Le retour 'break' évite qu'un autre widget traite le même événement.
    """
    if event.delta == 0:
        return "break"

    pas = -1 if event.delta > 0 else 1

    canvas.yview_scroll(
        pas,
        "units"
    )

    return "break"


def lier_molette_recursivement(widget, canvas):
    """
    Applique la molette au Canvas même lorsque la souris se trouve
    au-dessus d'un Label, d'une icône, d'un Entry ou d'un Frame interne.
    """
    try:
        widget.bind(
            "<MouseWheel>",
            lambda event, c=canvas:
            defiler_canvas_avec_molette(c, event)
        )
    except tk.TclError:
        pass

    for enfant in widget.winfo_children():
        lier_molette_recursivement(
            enfant,
            canvas
        )


# ============================================================
# STOCK DE LA BASE AERIENNE
# ============================================================

cadre_stock = tk.Frame(
    cadre_gauche,
    highlightthickness=1
)

cadre_stock.place(
    x=0,
    y=315,
    width=390,
    height=370
)

widgets_panneau.append(cadre_stock)
widgets_bordure.append(cadre_stock)


label_stock_titre = tk.Label(
    cadre_stock,
    text=t("main.stock.title"),
    font=POLICE_SECTION
)

label_stock_titre.place(
    x=0,
    y=22,
    width=390
)

widgets_panneau.append(label_stock_titre)


creer_separateur(
    cadre_stock
).place(
    x=25,
    y=58,
    width=340
)


label_stock_description = tk.Label(
    cadre_stock,
    text=t("main.stock.description"),
    font=(POLICE, 9),
    justify="center"
)

label_stock_description.place(
    x=25,
    y=95,
    width=340,
    height=55
)

widgets_texte_faible.append(
    label_stock_description
)



def ouvrir_rapports_carriere():
    _debut_performance_ui = time.perf_counter()
    rapports = charger_rapports_carriere()

    fenetre_rapport = tk.Toplevel(
        fenetre
    )

    fenetre_rapport.after_idle(
        lambda debut=_debut_performance_ui:
        journaliser_performance_ui(
            'Rapports carrière',
            debut
        )
    )

    appliquer_chrome_custom(
        fenetre_rapport,
        t("reports.window"),
        900,
        720,
        fenetre_rapport.destroy
    )

    entete = tk.Frame(
        fenetre_rapport,
        height=86,
        bg=theme["barre"]
    )

    entete.pack(
        fill="x"
    )

    entete.pack_propagate(
        False
    )

    tk.Label(
        entete,
        text=t("reports.title"),
        font=(POLICE, 19, "bold"),
        bg=theme["barre"],
        fg=theme["blanc"]
    ).pack(
        pady=(16, 2)
    )

    tk.Label(
        entete,
        text=t("reports.subtitle"),
        font=(POLICE, 8, "bold"),
        bg=theme["barre"],
        fg=theme["texte_faible"]
    ).pack()

    zone = tk.Frame(
        fenetre_rapport,
        bg=theme["fond"]
    )

    zone.pack(
        fill="both",
        expand=True,
        padx=18,
        pady=18
    )

    canvas = tk.Canvas(
        zone,
        highlightthickness=0,
        bg=theme["fond"]
    )

    canvas.pack(
        side="left",
        fill="both",
        expand=True
    )

    scrollbar = tk.Scrollbar(
        zone,
        orient="vertical",
        command=canvas.yview
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    canvas.configure(
        yscrollcommand=scrollbar.set
    )

    contenu = tk.Frame(
        canvas,
        bg=theme["fond"]
    )

    fenetre_canvas = canvas.create_window(
        (0, 0),
        window=contenu,
        anchor="nw"
    )

    def ajuster_scroll(event=None):
        canvas.configure(
            scrollregion=canvas.bbox(
                "all"
            )
        )

        canvas.itemconfigure(
            fenetre_canvas,
            width=canvas.winfo_width()
        )

    contenu.bind(
        "<Configure>",
        ajuster_scroll
    )

    canvas.bind(
        "<Configure>",
        ajuster_scroll
    )

    if not rapports:
        tk.Label(
            contenu,
            text=t("reports.none"),
            font=(POLICE, 11, "bold"),
            bg=theme["fond"],
            fg=theme["texte_faible"]
        ).pack(
            pady=80
        )

    def reconstruire_liste():
        for enfant in contenu.winfo_children():
            enfant.destroy()

        rapports_actuels = charger_rapports_carriere()

        if not rapports_actuels:
            tk.Label(
                contenu,
                text=t("reports.none"),
                font=(POLICE, 11, "bold"),
                bg=theme["fond"],
                fg=theme["texte_faible"]
            ).pack(
                pady=80
            )

            return

        for rapport in rapports_actuels:
            cadre = tk.Frame(
                contenu,
                height=118,
                bg=theme["panneau"],
                highlightbackground=theme["bordure"],
                highlightthickness=1
            )

            cadre.pack(
                fill="x",
                padx=4,
                pady=5
            )

            cadre.pack_propagate(
                False
            )

            valide = rapport[
                "valide"
            ]

            delta = rapport[
                "delta"
            ]

            type_changement = rapport[
                "type_changement"
            ]

            if type_changement == "augmentation":
                titre = t("reports.type.supply")

                couleur = theme[
                    "vert"
                ]

            elif type_changement == "diminution_reference":
                titre = t("reports.type.consumption")

                couleur = theme[
                    "rouge"
                ]

            elif type_changement == "initialisation":
                titre = t("reports.type.initial")

                couleur = theme[
                    "bleu"
                ]

            elif type_changement == "livraison_urgente":
                titre = t("reports.type.emergency")

                couleur = COULEUR_OR_COMMANDEMENT_ACTIF

            else:
                titre = t("reports.type.other")

                couleur = theme[
                    "bleu"
                ]

            tk.Frame(
                cadre,
                width=6,
                bg=couleur
            ).pack(
                side="left",
                fill="y"
            )

            zone_texte = tk.Frame(
                cadre,
                bg=theme["panneau"]
            )

            zone_texte.pack(
                side="left",
                fill="both",
                expand=True,
                padx=(14, 8),
                pady=10
            )

            tk.Label(
                zone_texte,
                text=titre,
                font=(POLICE, 10, "bold"),
                anchor="w",
                bg=theme["panneau"],
                fg=theme["texte"]
            ).pack(
                fill="x"
            )

            tk.Label(
                zone_texte,
                text=t(
                    "reports.date",
                    date=formater_date_jeu_rapport(rapport["date_jeu"])
                ),
                font=(POLICE, 8, "bold"),
                anchor="w",
                bg=theme["panneau"],
                fg=theme["texte_faible"]
            ).pack(
                fill="x",
                pady=(2, 6)
            )

            ancienne = rapport[
                "ancienne_valeur"
            ]

            nouvelle = rapport[
                "nouvelle_valeur"
            ]

            signe = (
                "+"
                if delta > 0
                else ""
            )

            texte_valeur_rapport = (
                t(
                    "reports.local_stock",
                    old=ancienne, new=nouvelle, delta=f"{signe}{delta}"
                )
                if type_changement == "livraison_urgente"
                else t(
                    "reports.il2_units",
                    old=ancienne, new=nouvelle, delta=f"{signe}{delta}"
                )
            )

            tk.Label(
                zone_texte,
                text=texte_valeur_rapport,
                font=(POLICE, 9, "bold"),
                anchor="w",
                bg=theme["panneau"],
                fg=couleur
            ).pack(
                fill="x"
            )

            details = rapport[
                "details"
            ]

            if (
                type_changement == "augmentation"
                and details
            ):
                morceaux = []

                for nom in trier_munitions_logiquement(
                    list(
                        details.keys()
                    )
                ):
                    valeur = details[
                        nom
                    ]

                    if isinstance(
                        valeur,
                        dict
                    ):
                        quantite = int(
                            valeur.get(
                                "delta",
                                0
                            )
                        )
                    else:
                        quantite = int(
                            valeur
                        )

                    if quantite > 0:
                        morceaux.append(
                            f"+{quantite} {t_munition(nom)}"
                        )

                texte_details = "  •  ".join(
                    morceaux[:3]
                )

                if len(
                    morceaux
                ) > 3:
                    texte_details += t(
                        "reports.more",
                        count=len(morceaux) - 3
                    )

            elif type_changement == "diminution_reference":
                texte_details = t("reports.detail.unchanged")

            elif (
                type_changement == "livraison_urgente"
                and details
            ):
                texte_details = t(
                    "reports.detail.emergency",
                    qty=int(details.get("quantite", delta)),
                    munition=t_munition(details.get("munition", "munition")),
                    size=t_taille_livraison(details.get("taille", ""))
                )

            else:
                texte_details = ""

            if texte_details:
                tk.Label(
                    zone_texte,
                    text=texte_details,
                    font=(POLICE, 7),
                    anchor="w",
                    bg=theme["panneau"],
                    fg=theme["texte_faible"]
                ).pack(
                    fill="x",
                    pady=(6, 0)
                )

            zone_validation = tk.Frame(
                cadre,
                width=128,
                bg=theme["panneau"]
            )

            zone_validation.pack(
                side="right",
                fill="y"
            )

            zone_validation.pack_propagate(
                False
            )

            def valider(
                identifiant=rapport["id"]
            ):
                valider_rapport_carriere(
                    identifiant
                )

                reconstruire_liste()

            bouton = tk.Button(
                zone_validation,
                text="✓",
                command=valider,
                font=(POLICE, 18, "bold"),
                bg=(
                    theme["vert"]
                    if valide
                    else theme["panneau_alt"]
                ),
                fg=(
                    theme["blanc"]
                    if valide
                    else theme["texte_faible"]
                ),
                activebackground=theme["vert"],
                activeforeground=theme["blanc"],
                relief="solid",
                borderwidth=1,
                state=(
                    "disabled"
                    if valide
                    else "normal"
                ),
                cursor=(
                    "arrow"
                    if valide
                    else "hand2"
                )
            )

            bouton.place(
                x=12,
                y=34,
                width=44,
                height=44
            )


            def supprimer(
                identifiant=rapport["id"]
            ):
                supprimer_rapport_carriere(
                    identifiant
                )

                reconstruire_liste()


            bouton_supprimer = tk.Button(
                zone_validation,
                text="✕",
                command=supprimer,
                font=(POLICE, 14, "bold"),
                bg=theme["panneau_alt"],
                fg=theme["rouge"],
                activebackground=theme["rouge"],
                activeforeground=theme["blanc"],
                relief="solid",
                borderwidth=1,
                cursor="hand2"
            )

            bouton_supprimer.place(
                x=68,
                y=34,
                width=44,
                height=44
            )

        ajuster_scroll()

    reconstruire_liste()

    lier_molette_recursivement(
        contenu,
        canvas
    )


    zone_bas = tk.Frame(
        fenetre_rapport,
        height=62,
        bg=theme["fond"]
    )

    zone_bas.pack(
        fill="x",
        padx=18,
        pady=(0, 14)
    )

    zone_bas.pack_propagate(
        False
    )


    def effacer_tout():
        rapports_actuels = charger_rapports_carriere()

        if not rapports_actuels:
            return

        confirmer = dialogue_message_custom(
            t("reports.delete.title"),
            t("reports.delete.body"),
            "question",
            fenetre_rapport
        )

        # dialogue_message_custom peut être purement informatif selon
        # la version actuelle ; on effectue donc la suppression après
        # l'action utilisateur sur le bouton dédié.
        supprimer_tous_les_rapports_carriere()

        reconstruire_liste()


    bouton_effacer_tout = tk.Button(
        zone_bas,
        text=t("reports.delete_all"),
        command=effacer_tout,
        font=(POLICE, 9, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["rouge"],
        activebackground=theme["rouge"],
        activeforeground=theme["blanc"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    )

    bouton_effacer_tout.pack(
        side="right",
        ipadx=16,
        ipady=7
    )


def creer_donut_image_global(
    valeurs,
    couleurs,
    taille=300,
    trou=0.48
):
    """
    Génère un donut antialiasé avec Pillow.

    Fonction globale afin d'être utilisable aussi bien dans la page Stock
    que dans la fenêtre de consultation mensuelle.
    """
    cle_cache = (
        "global",
        tuple(round(float(v), 6) for v in valeurs),
        tuple(str(c) for c in couleurs),
        int(taille),
        round(float(trou), 4),
        theme["panneau"],
    )
    image_cachee = _CACHE_DONUTS_PIL.get(cle_cache)
    if image_cachee is not None:
        return image_cachee.copy()

    facteur = 4

    taille_hd = (
        int(
            taille
        )
        * facteur
    )

    marge = (
        10
        * facteur
    )

    image_hd = Image.new(
        "RGBA",
        (
            taille_hd,
            taille_hd
        ),
        (
            0,
            0,
            0,
            0
        )
    )

    dessin = ImageDraw.Draw(
        image_hd
    )

    boite = (
        marge,
        marge,
        taille_hd - marge,
        taille_hd - marge
    )

    total = sum(
        max(
            0.0,
            float(
                valeur
            )
        )
        for valeur in valeurs
    )

    if total <= 0:
        total = 1.0

    angle = -90.0

    for valeur, couleur in zip(
        valeurs,
        couleurs
    ):
        valeur = max(
            0.0,
            float(
                valeur
            )
        )

        if valeur <= 0:
            continue

        angle_fin = (
            angle
            + (
                valeur
                / total
                * 360.0
            )
        )

        dessin.pieslice(
            boite,
            start=angle,
            end=angle_fin,
            fill=couleur
        )

        angle = angle_fin

    rayon_trou = int(
        (
            taille_hd
            * float(
                trou
            )
        )
        / 2
    )

    centre = (
        taille_hd
        // 2
    )

    dessin.ellipse(
        (
            centre - rayon_trou,
            centre - rayon_trou,
            centre + rayon_trou,
            centre + rayon_trou
        ),
        fill=theme[
            "panneau"
        ]
    )

    image_finale = image_hd.resize(
        (
            int(
                taille
            ),
            int(
                taille
            )
        ),
        Image.Resampling.LANCZOS
    )
    _CACHE_DONUTS_PIL[cle_cache] = image_finale.copy()
    return image_finale



COULEUR_OR_COMMANDEMENT = "#b99a4a"
COULEUR_OR_COMMANDEMENT_ACTIF = "#cfb45c"

# Économie du Haut Commandement.
POINTS_COMMANDEMENT_DEPART = 1
COUT_BOOST_15 = 10
COUT_BOOST_30 = 25
COUT_LIVRAISON_PETITE = 8
COUT_LIVRAISON_GRANDE = 15
COUT_DIRECTIVE_REPARTITION = 28

GAIN_POINTS_JOURNALIER_DEFAUT_X10 = 10
GAINS_POINTS_JOURNALIERS_ADMIN_X10 = (
    1,
    5,
    10,
    20,
    30,
)

# Références UI faibles : nettoyées automatiquement si les fenêtres ferment.
labels_points_commandement_ouverts = []
labels_gain_commandement_ouverts = []


def extraire_date_complete_carriere(
    donnees_carriere
):
    texte = str(
        donnees_carriere.get(
            "date_jeu",
            ""
        )
        or ""
    )

    for format_source in (
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d"
    ):
        try:
            return datetime.strptime(
                texte,
                format_source
            )
        except ValueError:
            pass

    return None


def mode_admin_actif():
    """
    Mode ADMIN global au logiciel.

    Il est stocké dans config.json et ne dépend d'aucune carrière.
    """
    return bool(
        config.get(
            "mode_admin",
            False
        )
    )


def definir_mode_admin(
    actif
):
    config[
        "mode_admin"
    ] = bool(
        actif
    )

    try:
        sauvegarder_config()
        return True

    except Exception:
        return False


def mode_developpeur_actif():
    """
    Alias de compatibilité avec les anciens appels internes.
    Toutes les anciennes fonctions développeur utilisent maintenant
    le MODE ADMIN global.
    """
    return mode_admin_actif()


def definir_mode_developpeur(
    actif
):
    return definir_mode_admin(
        actif
    )



def formater_points_commandement(
    valeur
):
    """
    52.0 -> "52"
    52.5 -> "52,5"
    0.1  -> "0,1"
    """
    valeur_x10 = int(
        round(
            float(
                valeur
            )
            * 10
        )
    )

    if valeur_x10 % 10 == 0:
        return str(
            valeur_x10
            // 10
        )

    return (
        f"{valeur_x10 / 10:.1f}"
        .replace(
            ".",
            ","
        )
    )


def obtenir_gain_points_journalier():
    try:
        gain_x10 = local_db.lire_gain_points_journalier_x10(
            FICHIER_BASE
        )

        return (
            float(
                gain_x10
            )
            / 10.0
        )

    except Exception:
        return 1.0


def texte_gain_points_journalier():
    gain = obtenir_gain_points_journalier()

    return t(
        "hc.daily_gain",
        gain=formater_points_commandement(gain)
    )


def actualiser_points_commandement_journaliers(
    donnees_carriere=None
):
    """
    Crédite les points gagnés selon les jours réellement écoulés dans
    la carrière IL-2.

    Première utilisation d'une ancienne carrière :
    la date courante devient simplement la référence de départ.
    Il n'y a aucune rétroactivité.
    """
    if donnees_carriere is None:
        donnees_carriere = DONNEES_CARRIERE_IL2

    date_carriere = extraire_date_complete_carriere(
        donnees_carriere
    )

    if date_carriere is None:
        date_carriere = obtenir_date_reference_commandement()

    return local_db.actualiser_points_commandement_journaliers(
        FICHIER_BASE,
        date_carriere.date().toordinal()
    )


def obtenir_points_commandement(
    actualiser=True
):
    try:
        if actualiser:
            actualiser_points_commandement_journaliers()

        points_x10 = local_db.lire_points_commandement_x10(
            FICHIER_BASE
        )

        return (
            float(
                points_x10
            )
            / 10.0
        )

    except Exception:
        return float(
            POINTS_COMMANDEMENT_DEPART
        )


def actualiser_affichage_points_commandement_ouvert():
    """
    Met à jour les éventuelles fenêtres de répartition déjà ouvertes.
    Appelée depuis le thread Tkinter.
    """
    points = obtenir_points_commandement(
        actualiser=False
    )

    gain_texte = texte_gain_points_journalier()

    admin = mode_developpeur_actif()

    labels_points_valides = []

    for label in labels_points_commandement_ouverts:
        try:
            if label.winfo_exists():
                label.configure(
                    text=(
                        t("hc.admin.short")
                        if admin
                        else formater_points_commandement(
                            points
                        )
                    ),
                    fg=(
                        theme["vert"]
                        if admin
                        else COULEUR_OR_COMMANDEMENT_ACTIF
                    )
                )

                labels_points_valides.append(
                    label
                )

        except Exception:
            pass

    labels_points_commandement_ouverts[:] = (
        labels_points_valides
    )

    labels_gain_valides = []

    for label in labels_gain_commandement_ouverts:
        try:
            if label.winfo_exists():
                label.configure(
                    text=gain_texte
                )

                labels_gain_valides.append(
                    label
                )

        except Exception:
            pass

    labels_gain_commandement_ouverts[:] = (
        labels_gain_valides
    )


def points_commandement_suffisants(
    cout
):
    if mode_developpeur_actif():
        return True

    return (
        obtenir_points_commandement()
        >= float(
            cout
        )
    )


def debiter_points_commandement_transaction(
    curseur,
    cout
):
    """
    Débite le solde en dixièmes de point dans la transaction courante.

    En mode Admin :
    - aucun débit ;
    - succès systématique.
    """
    return local_db.debiter_points_commandement_transaction(
        curseur,
        cout,
        gratuit=mode_developpeur_actif()
    )


def obtenir_date_reference_commandement():
    """
    Date unique de référence pour toute la logique du Haut Commandement.

    Règle depuis v0.9.51.7 :
    la DATE affichée dans l'interface principale est la référence.

    Ce champ est lui-même verrouillé et alimenté par career.currentDate dans
    la base de carrière IL-2. Il ne peut donc plus diverger de la campagne.
    """
    try:
        champ = globals().get(
            "champ_date"
        )

        if champ is not None:
            texte = str(
                champ.get()
                or ""
            ).strip()

            return datetime.strptime(
                texte,
                "%d.%m.%Y"
            )

    except Exception:
        pass

    try:
        date_carriere = extraire_date_complete_carriere(
            DONNEES_CARRIERE_IL2
        )

        if date_carriere is not None:
            return date_carriere

    except Exception:
        pass

    return datetime(
        1951,
        4,
        9
    )


def obtenir_annee_mois_reference_commandement():
    date_reference = obtenir_date_reference_commandement()

    return (
        int(
            date_reference.year
        ),
        int(
            date_reference.month
        )
    )


def periode_commandement_est_passee(
    annee,
    mois
):
    """
    Une demande peut viser le mois de référence de l'interface ou n'importe
    quel mois futur. Jamais un mois antérieur à cette date de référence.
    """
    annee_actuelle, mois_actuel = (
        obtenir_annee_mois_reference_commandement()
    )

    return (
        (
            int(
                annee
            ),
            int(
                mois
            )
        )
        < (
            int(
                annee_actuelle
            ),
            int(
                mois_actuel
            )
        )
    )


def mois_suivant_commandement(
    annee_reference=None,
    mois_reference=None
):
    """
    Retourne le mois suivant une période donnée.

    Sans argument, utilise la DATE de l'interface principale.
    Avec année/mois, utilise explicitement la période ciblée dans la fenêtre
    du Haut Commandement.
    """
    if (
        annee_reference is None
        or mois_reference is None
    ):
        (
            annee_reference,
            mois_reference
        ) = obtenir_annee_mois_reference_commandement()

    annee = int(
        annee_reference
    )

    mois = int(
        mois_reference
    )

    if mois >= 12:
        return (
            annee + 1,
            1
        )

    return (
        annee,
        mois + 1
    )


def mois_suivant_carriere():
    """
    Alias historique conservé pour compatibilité interne.

    Depuis v0.9.51.3 il utilise la date de l'interface, pas une relecture
    indépendante de career.currentDate.
    """
    return mois_suivant_commandement()


def lire_evenement_directive_standard_exact(
    annee,
    mois,
    avion
):
    """
    Événement programmé exactement pour le mois donné.
    Utile pour permettre de corriger une directive déjà payée avant
    son entrée en vigueur sans redépenser les points déjà payés.
    """
    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        curseur = connexion.cursor()

        ligne = curseur.execute(
            """
            SELECT
                id,
                mode,
                cout,
                date_creation
            FROM directives_standard_commandement
            WHERE
                avion = ?
                AND annee_effet = ?
                AND mois_effet = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                str(
                    avion
                ),
                int(
                    annee
                ),
                int(
                    mois
                )
            )
        ).fetchone()

        if ligne is None:
            connexion.close()
            return None

        resultat = {
            "id": int(
                ligne[0]
            ),
            "mode": str(
                ligne[1]
            ),
            "cout": int(
                ligne[2]
            ),
            "date_creation": str(
                ligne[3]
                or ""
            ),
            "priorites": {}
        }

        if resultat[
            "mode"
        ] == "CUSTOM":
            priorites = curseur.execute(
                """
                SELECT
                    munition,
                    niveau
                FROM directives_standard_priorites
                WHERE directive_id = ?
                """,
                (
                    resultat[
                        "id"
                    ],
                )
            ).fetchall()

            resultat[
                "priorites"
            ] = {
                str(
                    munition
                ): str(
                    niveau
                )
                for munition, niveau
                in priorites
            }

        connexion.close()

        return resultat

    except sqlite3.Error:
        return None


def numero_directive_standard(
    identifiant_directive,
    avion
):
    """
    Numéro lisible d'une directive CUSTOM pour l'appareil.

    Les événements BASE (retour au STANDARD historique) ne consomment
    pas de numéro.
    """
    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        lignes = connexion.execute(
            """
            SELECT id
            FROM directives_standard_commandement
            WHERE
                avion = ?
                AND mode = 'CUSTOM'
            ORDER BY
                annee_effet ASC,
                mois_effet ASC,
                id ASC
            """,
            (
                str(
                    avion
                ),
            )
        ).fetchall()

        connexion.close()

        for index, ligne in enumerate(
            lignes,
            start=1
        ):
            if int(
                ligne[
                    0
                ]
            ) == int(
                identifiant_directive
            ):
                return index

    except sqlite3.Error:
        try:
            connexion.close()
        except Exception:
            pass

    return None


def formater_date_historique_commandement(valeur, format_source="%Y-%m-%d %H:%M:%S"):
    """Retourne une date courte et robuste pour l'historique du Haut Commandement."""
    texte = str(valeur or "").strip()
    if not texte:
        return "--/--/----"

    formats = [
        format_source,
        "%Y-%m-%d %H:%M:%S",
        "%Y.%m.%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y.%m.%d",
    ]

    for fmt in dict.fromkeys(formats):
        try:
            return datetime.strptime(texte, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue

    return texte


def lister_historique_commandement_simplifie(
    annee,
    mois,
    avion,
    limite=7
):
    """
    Historique compact du Haut Commandement jusqu'à la période consultée.

    Événements :
    - directives ;
    - retours au STANDARD ;
    - boosts ;
    - livraisons urgentes.
    """
    evenements = []

    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        curseur = connexion.cursor()

        directives = curseur.execute(
            """
            SELECT
                id,
                annee_effet,
                mois_effet,
                mode,
                date_creation
            FROM directives_standard_commandement
            WHERE
                avion = ?
                AND (
                    annee_effet < ?
                    OR (
                        annee_effet = ?
                        AND mois_effet <= ?
                    )
                )
            ORDER BY
                annee_effet ASC,
                mois_effet ASC,
                id ASC
            """,
            (
                str(
                    avion
                ),
                int(
                    annee
                ),
                int(
                    annee
                ),
                int(
                    mois
                )
            )
        ).fetchall()

        numero_custom = {}
        compteur = 0

        for ligne in directives:
            if str(
                ligne[
                    3
                ]
            ) == "CUSTOM":
                compteur += 1
                numero_custom[
                    int(
                        ligne[
                            0
                        ]
                    )
                ] = compteur

        for ligne in directives:
            identifiant = int(
                ligne[
                    0
                ]
            )
            annee_effet = int(
                ligne[
                    1
                ]
            )
            mois_effet = int(
                ligne[
                    2
                ]
            )
            mode = str(
                ligne[
                    3
                ]
            )
            date_action = formater_date_historique_commandement(
                ligne[4]
            )

            periode = (
                f"{t_mois(mois_effet)} "
                f"{annee_effet}"
            )

            if mode == "CUSTOM":
                numero = numero_custom.get(
                    identifiant,
                    "?"
                )

                texte = (
                    t("hc.history.directive", number=numero, period=periode)
                )
            else:
                texte = (
                    t("hc.history.standard", period=periode)
                )

            evenements.append(
                {
                    "tri": (
                        annee_effet,
                        mois_effet,
                        31,
                        30,
                        identifiant
                    ),
                    "texte": f"[{date_action}] {texte}"
                }
            )

        boosts = curseur.execute(
            """
            SELECT
                rowid,
                annee,
                mois,
                munition,
                boost_pourcent,
                date_demande
            FROM boosts_commandement
            WHERE
                avion = ?
                AND (
                    annee < ?
                    OR (
                        annee = ?
                        AND mois <= ?
                    )
                )
            """,
            (
                str(
                    avion
                ),
                int(
                    annee
                ),
                int(
                    annee
                ),
                int(
                    mois
                )
            )
        ).fetchall()

        for ligne in boosts:
            identifiant = int(
                ligne[
                    0
                ]
            )
            annee_boost = int(
                ligne[
                    1
                ]
            )
            mois_boost = int(
                ligne[
                    2
                ]
            )
            munition = str(
                ligne[
                    3
                ]
            )
            boost = float(
                ligne[
                    4
                ]
            )
            date_action = formater_date_historique_commandement(
                ligne[5]
            )

            periode = (
                f"{t_mois(mois_boost)} "
                f"{annee_boost}"
            )

            evenements.append(
                {
                    "tri": (
                        annee_boost,
                        mois_boost,
                        20,
                        20,
                        identifiant
                    ),
                    "texte": (
                        f"[{date_action}] "
                        + t("hc.history.boost", boost=f"{boost:.0f}", munition=t_munition(munition), period=periode)
                    )
                }
            )

        livraisons = curseur.execute(
            """
            SELECT
                id,
                date_demande_jeu,
                munition,
                taille,
                statut
            FROM livraisons_urgentes
            WHERE avion = ?
            ORDER BY id
            """,
            (
                str(
                    avion
                ),
            )
        ).fetchall()

        connexion.close()

        for ligne in livraisons:
            identifiant = int(
                ligne[
                    0
                ]
            )
            date_texte = str(
                ligne[
                    1
                ]
                or ""
            )

            try:
                date_demande = datetime.strptime(
                    date_texte,
                    "%Y.%m.%d %H:%M:%S"
                )
            except ValueError:
                continue

            if (
                date_demande.year,
                date_demande.month
            ) > (
                int(
                    annee
                ),
                int(
                    mois
                )
            ):
                continue

            munition = str(
                ligne[
                    2
                ]
            )
            taille = str(
                ligne[
                    3
                ]
            )
            statut = str(
                ligne[
                    4
                ]
                or ""
            ).upper()

            statut_affiche = t_statut_livraison(
                statut
            )

            evenements.append(
                {
                    "tri": (
                        date_demande.year,
                        date_demande.month,
                        date_demande.day,
                        10,
                        identifiant
                    ),
                    "texte": (
                        f"[{date_demande.strftime('%d/%m/%Y')}] "
                        + t(
                            "hc.history.delivery",
                            size=t_taille_livraison(taille).lower(),
                            munition=t_munition(munition),
                            status=statut_affiche
                        )
                    )
                }
            )

    except sqlite3.Error:
        try:
            connexion.close()
        except Exception:
            pass

        return []

    evenements.sort(
        key=lambda element:
        element[
            "tri"
        ],
        reverse=True
    )

    return [
        element[
            "texte"
        ]
        for element in evenements[
            :max(
                1,
                int(
                    limite
                )
            )
        ]
    ]


def description_directive_standard(
    annee,
    mois,
    avion
):
    directive = lire_directive_standard_applicable(
        annee,
        mois,
        avion
    )

    if directive is None:
        return None

    if directive[
        "mode"
    ] == "BASE":
        return {
            "mode": "BASE",
            "texte": (
                t("hc.standard_restored")
            ),
            "annee_effet": directive[
                "annee_effet"
            ],
            "mois_effet": directive[
                "mois_effet"
            ]
        }

    numero = numero_directive_standard(
        directive[
            "id"
        ],
        avion
    )

    return {
        "mode": "CUSTOM",
        "id": directive[
            "id"
        ],
        "numero": numero,
        "texte": (
            t("hc.directive.active_text", number=numero)
            if numero is not None
            else t("hc.directive.active_generic")
        ),
        "annee_effet": directive[
            "annee_effet"
        ],
        "mois_effet": directive[
            "mois_effet"
        ]
    }


def enregistrer_directive_standard_commandement(
    avion,
    annee_effet,
    mois_effet,
    priorites
):
    """
    Nouvelle directive : 28 points.

    Si une directive CUSTOM a déjà été payée pour EXACTEMENT le même mois
    d'effet, elle peut être corrigée gratuitement avant son entrée en vigueur.
    """
    compatibles = trier_munitions_logiquement(
        AVIONS_EMPORTS.get(
            avion,
            []
        )
    )

    priorites = {
        munition: priorites.get(
            munition,
            lire_standard_mensuel_munition(
                annee_effet,
                mois_effet,
                avion,
                munition
            )[
                "niveau"
            ]
        )
        for munition in compatibles
    }

    erreurs = verifier_limites_niveaux(
        priorites
    )

    if erreurs:
        return (
            False,
            t("hc.error.directive_quota")
        )

    evenement_exact = lire_evenement_directive_standard_exact(
        annee_effet,
        mois_effet,
        avion
    )

    cout = (
        0
        if (
            evenement_exact is not None
            and evenement_exact[
                "mode"
            ] == "CUSTOM"
            and evenement_exact[
                "cout"
            ] > 0
        )
        else COUT_DIRECTIVE_REPARTITION
    )

    if not points_commandement_suffisants(
        cout
    ):
        return (
            False,
            (
                t("hc.error.insufficient_points", cost=cout)
            )
        )

    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    try:
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        succes_debit, _ = debiter_points_commandement_transaction(
            curseur,
            cout
        )

        if not succes_debit:
            connexion.rollback()
            connexion.close()

            return (
                False,
                t("hc.error.insufficient_points", cost=cout)
            )

        if evenement_exact is not None:
            identifiant = evenement_exact[
                "id"
            ]

            curseur.execute(
                """
                UPDATE directives_standard_commandement
                SET
                    mode = 'CUSTOM',
                    cout = ?,
                    date_creation = ?
                WHERE id = ?
                """,
                (
                    max(
                        0,
                        int(
                            evenement_exact[
                                "cout"
                            ]
                        )
                    ),
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    identifiant
                )
            )

            curseur.execute(
                """
                DELETE FROM directives_standard_priorites
                WHERE directive_id = ?
                """,
                (
                    identifiant,
                )
            )

        else:
            curseur.execute(
                """
                INSERT INTO directives_standard_commandement (
                    avion,
                    annee_effet,
                    mois_effet,
                    mode,
                    cout,
                    date_creation
                )
                VALUES (?, ?, ?, 'CUSTOM', ?, ?)
                """,
                (
                    avion,
                    int(
                        annee_effet
                    ),
                    int(
                        mois_effet
                    ),
                    COUT_DIRECTIVE_REPARTITION,
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )
            )

            identifiant = curseur.lastrowid

        for munition, niveau in priorites.items():
            curseur.execute(
                """
                INSERT INTO directives_standard_priorites (
                    directive_id,
                    munition,
                    niveau
                )
                VALUES (?, ?, ?)
                """,
                (
                    int(
                        identifiant
                    ),
                    str(
                        munition
                    ),
                    str(
                        niveau
                    )
                )
            )

        connexion.commit()
        connexion.close()

        return (
            True,
            {
                "cout": cout,
                "annee_effet": int(
                    annee_effet
                ),
                "mois_effet": int(
                    mois_effet
                )
            }
        )

    except sqlite3.Error as erreur:
        connexion.rollback()
        connexion.close()

        return (
            False,
            str(
                erreur
            )
        )


def programmer_retablissement_standard(
    avion,
    annee_effet,
    mois_effet
):
    """
    Programme gratuitement le retour aux valeurs historiques de base
    à partir du mois d'effet.

    Aucun remboursement de points.
    """
    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    try:
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        evenement_exact = lire_evenement_directive_standard_exact(
            annee_effet,
            mois_effet,
            avion
        )

        if evenement_exact is not None:
            identifiant = evenement_exact[
                "id"
            ]

            curseur.execute(
                """
                UPDATE directives_standard_commandement
                SET
                    mode = 'BASE',
                    cout = 0,
                    date_creation = ?
                WHERE id = ?
                """,
                (
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    identifiant
                )
            )

            curseur.execute(
                """
                DELETE FROM directives_standard_priorites
                WHERE directive_id = ?
                """,
                (
                    identifiant,
                )
            )

        else:
            curseur.execute(
                """
                INSERT INTO directives_standard_commandement (
                    avion,
                    annee_effet,
                    mois_effet,
                    mode,
                    cout,
                    date_creation
                )
                VALUES (?, ?, ?, 'BASE', 0, ?)
                """,
                (
                    avion,
                    int(
                        annee_effet
                    ),
                    int(
                        mois_effet
                    ),
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )
            )

        connexion.commit()
        connexion.close()

        return (
            True,
            "STANDARD historique programmé."
        )

    except sqlite3.Error as erreur:
        connexion.rollback()
        connexion.close()

        return (
            False,
            str(
                erreur
            )
        )



def lister_boosts_commandement(
    annee,
    mois,
    avion
):
    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        curseur = connexion.cursor()

        lignes = curseur.execute(
            """
            SELECT
                munition,
                boost_pourcent,
                cout_total,
                date_demande
            FROM boosts_commandement
            WHERE
                annee = ?
                AND mois = ?
                AND avion = ?
            ORDER BY munition COLLATE NOCASE
            """,
            (
                int(
                    annee
                ),
                int(
                    mois
                ),
                str(
                    avion
                )
            )
        ).fetchall()

        connexion.close()

        return [
            {
                "munition": str(
                    munition
                ),
                "boost_pourcent": float(
                    boost
                ),
                "cout_total": int(
                    cout
                ),
                "date_demande": str(
                    date_demande
                    or ""
                )
            }
            for (
                munition,
                boost,
                cout,
                date_demande
            ) in lignes
        ]

    except sqlite3.Error:
        return []


def cout_boost_commandement(
    boost_pourcent
):
    if float(
        boost_pourcent
    ) >= 30.0:
        return COUT_BOOST_30

    return COUT_BOOST_15


def appliquer_boost_commandement(
    annee,
    mois,
    avion,
    munition,
    boost_pourcent
):
    """
    Ajoute un bonus indépendant au poids du modèle.

    Le preset n'est jamais modifié.
    +15 % = coût total 10 pts
    +30 % = coût total 25 pts

    Une munition ne peut recevoir qu'UN seul boost pendant un même mois.
    """
    if periode_commandement_est_passee(
        annee,
        mois
    ):
        return (
            False,
            t("hc.error.past_month")
        )

    if munition not in AVIONS_EMPORTS.get(
        avion,
        []
    ):
        return (
            False,
            t("hc.error.incompatible")
        )

    boost_pourcent = float(
        boost_pourcent
    )

    if boost_pourcent not in (
        15.0,
        30.0
    ):
        return (
            False,
            t("hc.error.invalid_boost")
        )

    actuel = lire_boost_commandement(
        annee,
        mois,
        avion,
        munition
    )

    boost_actuel = float(
        actuel[
            "boost_pourcent"
        ]
    )

    if boost_actuel > 0:
        return (
            False,
            (
                t("hc.error.already_boosted")
            )
        )

    cout_cible = cout_boost_commandement(
        boost_pourcent
    )

    cout_a_payer = cout_cible

    if not points_commandement_suffisants(
        cout_a_payer
    ):
        return (
            False,
            t("hc.error.insufficient_points", cost=cout_a_payer)
        )

    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    try:
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        succes_debit, _ = debiter_points_commandement_transaction(
            curseur,
            cout_a_payer
        )

        if not succes_debit:
            connexion.rollback()
            connexion.close()

            return (
                False,
                t("hc.error.insufficient_points", cost=cout_a_payer)
            )

        curseur.execute(
            """
            INSERT INTO boosts_commandement (
                annee,
                mois,
                avion,
                munition,
                boost_pourcent,
                cout_total,
                date_demande
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(
                annee,
                mois,
                avion,
                munition
            )
            DO UPDATE SET
                boost_pourcent = excluded.boost_pourcent,
                cout_total = excluded.cout_total,
                date_demande = excluded.date_demande
            """,
            (
                int(
                    annee
                ),
                int(
                    mois
                ),
                str(
                    avion
                ),
                str(
                    munition
                ),
                boost_pourcent,
                cout_cible,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )

        connexion.commit()
        connexion.close()

        return (
            True,
            {
                "boost_pourcent": boost_pourcent,
                "cout": cout_a_payer
            }
        )

    except sqlite3.Error as erreur:
        connexion.rollback()
        connexion.close()

        return (
            False,
            str(
                erreur
            )
        )


def appliquer_boost_au_poids(
    poids,
    annee,
    mois,
    avion,
    munition
):
    """
    Compatibilité historique.

    Depuis v0.9.35, un boost du haut commandement n'altère PLUS le poids
    utilisé pour normaliser le ravitaillement IL-2.

    Le boost est un cadeau logistique indépendant :
    +15 % = +15 points de pourcentage du budget IL-2 reçu,
    sans retirer quoi que ce soit aux autres munitions.
    """
    return max(
        0.0,
        float(
            poids
        )
    )


def lister_livraisons_urgentes_en_transit():
    try:
        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        curseur = connexion.cursor()

        lignes = curseur.execute(
            """
            SELECT
                id,
                date_demande_jeu,
                date_arrivee_jeu,
                avion,
                munition,
                taille,
                quantite_min,
                quantite_max,
                cout
            FROM livraisons_urgentes
            WHERE statut = 'EN_TRANSIT'
            ORDER BY date_arrivee_jeu, id
            """
        ).fetchall()

        connexion.close()

        return [
            {
                "id": int(
                    ligne[0]
                ),
                "date_demande_jeu": str(
                    ligne[1]
                ),
                "date_arrivee_jeu": str(
                    ligne[2]
                ),
                "avion": str(
                    ligne[3]
                ),
                "munition": str(
                    ligne[4]
                ),
                "taille": str(
                    ligne[5]
                ),
                "quantite_min": int(
                    ligne[6]
                ),
                "quantite_max": int(
                    ligne[7]
                ),
                "cout": int(
                    ligne[8]
                )
            }
            for ligne in lignes
        ]

    except sqlite3.Error:
        return []



def livraison_urgente_en_transit():
    livraisons = lister_livraisons_urgentes_en_transit()

    if not livraisons:
        return None

    return livraisons[0]



def fourchette_livraison_urgente(
    avion,
    munition,
    taille
):
    """
    Fourchettes gameplay-logistiques propres à la munition ET à l'avion.

    Elles représentent un petit lot exceptionnel transportable rapidement,
    pas un ravitaillement mensuel complet.
    """
    petite_grande = {
        # USAF - roquettes
        'Roquette aérienne semi-perforante à haute vitesse HVAR 5"': {
            "PETITE": (25, 40),
            "GRANDE": (60, 85)
        },
        'Roquette aérienne à haute vitesse HVAR 5"': {
            "PETITE": (30, 50),
            "GRANDE": (70, 100)
        },
        'Roquette ATAR 6,5"': {
            "PETITE": (15, 25),
            "GRANDE": (35, 50)
        },
        'Roquette Tiny Tim 12"': {
            "PETITE": (3, 6),
            "GRANDE": (8, 12)
        },

        # USAF - bombes
        "AN-M57A1 250 lb": {
            "PETITE": (10, 18),
            "GRANDE": (25, 35)
        },
        "AN-M64A1 500 lb": {
            "PETITE": (6, 12),
            "GRANDE": (15, 25)
        },
        "AN-M65A1 1000 lb": {
            "PETITE": (3, 6),
            "GRANDE": (8, 14)
        },
        "AN-M88 220 lb à fragmentation": {
            "PETITE": (10, 18),
            "GRANDE": (24, 34)
        },
        "M26A2 500 lb à sous-munitions": {
            "PETITE": (5, 9),
            "GRANDE": (12, 20)
        },
        "M29A1 500 lb à sous-munitions": {
            "PETITE": (5, 9),
            "GRANDE": (12, 20)
        },
        "Bombe éclairante à parachute AN-M26A1": {
            "PETITE": (3, 6),
            "GRANDE": (8, 12)
        },

        # Napalm
        "Réservoir de napalm 110 gal": {
            "PETITE": (5, 9),
            "GRANDE": (12, 20)
        },

        # Réservoirs US
        "Réservoir largable 75 gal": {
            "PETITE": (8, 12),
            "GRANDE": (18, 28)
        },
        "Réservoir largable 110 gal": {
            "PETITE": (8, 12),
            "GRANDE": (18, 28)
        },
        "Réservoir largable 120 gal": {
            "PETITE": (7, 11),
            "GRANDE": (16, 24)
        },
        "Réservoir largable 165 gal": {
            "PETITE": (6, 10),
            "GRANDE": (14, 22)
        },
        "Réservoir largable 230 gal": {
            "PETITE": (5, 9),
            "GRANDE": (12, 18)
        },
        "Réservoir largable 245 gal": {
            "PETITE": (5, 9),
            "GRANDE": (12, 18)
        },
        "Réservoir largable 265 gal": {
            "PETITE": (5, 8),
            "GRANDE": (11, 17)
        },

        # IL-10 / soviétiques
        "M-13UK 132 mm": {
            "PETITE": (20, 35),
            "GRANDE": (45, 70)
        },
        "M-8 82 mm": {
            "PETITE": (30, 50),
            "GRANDE": (70, 100)
        },
        "PTAB-10-2.5": {
            "PETITE": (15, 25),
            "GRANDE": (35, 55)
        },
        "PTAB-2,5-1,5": {
            "PETITE": (20, 30),
            "GRANDE": (45, 65)
        },
        "SAB-100-55": {
            "PETITE": (4, 8),
            "GRANDE": (10, 16)
        },
        "AO-10sc": {
            "PETITE": (15, 25),
            "GRANDE": (35, 50)
        },
        "AO-2,5sc": {
            "PETITE": (20, 35),
            "GRANDE": (45, 70)
        },
        "AO-25sl": {
            "PETITE": (10, 18),
            "GRANDE": (25, 35)
        },
        "FAB-50sc": {
            "PETITE": (18, 30),
            "GRANDE": (40, 60)
        },
        "FAB-100sc": {
            "PETITE": (12, 20),
            "GRANDE": (28, 42)
        },
        "FAB-250 M43": {
            "PETITE": (7, 12),
            "GRANDE": (16, 26)
        },
        "Réservoir largable 250 L": {
            "PETITE": (8, 12),
            "GRANDE": (18, 26)
        }
    }

    plages = petite_grande.get(
        munition
    )

    if plages is None:
        categorie = categorie_affichage_munition(
            munition
        )

        if categorie == "Roquettes":
            plages = {
                "PETITE": (20, 35),
                "GRANDE": (45, 70)
            }
        elif categorie == "Bombes":
            plages = {
                "PETITE": (6, 12),
                "GRANDE": (15, 25)
            }
        elif categorie == "Réservoirs":
            plages = {
                "PETITE": (6, 10),
                "GRANDE": (14, 22)
            }
        elif categorie == "Napalm":
            plages = {
                "PETITE": (5, 9),
                "GRANDE": (12, 20)
            }
        else:
            plages = {
                "PETITE": (4, 8),
                "GRANDE": (10, 16)
            }

    minimum, maximum = plages.get(
        taille,
        plages[
            "PETITE"
        ]
    )

    # Ajustement léger selon l'appareil réellement utilisé dans la carrière.
    # Il évite qu'un F-86 ou un MiG reçoive les mêmes lots qu'un appareil
    # d'attaque dont l'emport courant est beaucoup plus important.
    facteur = {
        "F-51D": 1.00,
        "F-80C-10": 0.90,
        "F-84E": 1.05,
        "F-86A-5": 0.80,
        "IL-10": 1.00,
        "MiG-15bis": 0.70,
        "Yak-9P": 0.75,
        "La-11": 0.75
    }.get(
        avion,
        1.0
    )

    minimum = max(
        1,
        int(
            round(
                minimum
                * facteur
            )
        )
    )

    maximum = max(
        minimum,
        int(
            round(
                maximum
                * facteur
            )
        )
    )

    return (
        minimum,
        maximum
    )


def cout_livraison_urgente(
    taille
):
    return (
        COUT_LIVRAISON_PETITE
        if taille == "PETITE"
        else COUT_LIVRAISON_GRANDE
    )


def creer_livraison_urgente(
    avion,
    munition,
    taille,
    annee_cible=None,
    mois_cible=None
):
    if taille not in (
        "PETITE",
        "GRANDE"
    ):
        return (
            False,
            t("hc.error.invalid_delivery_size")
        )

    if munition not in AVIONS_EMPORTS.get(
        avion,
        []
    ):
        return (
            False,
            t("hc.error.incompatible")
        )

    # Le Haut Commandement utilise la date affichée dans l'interface
    # principale comme référence temporelle unique.
    date_actuelle = obtenir_date_reference_commandement()

    if annee_cible is None or mois_cible is None:
        annee_cible = date_actuelle.year
        mois_cible = date_actuelle.month

    annee_cible = int(
        annee_cible
    )

    mois_cible = int(
        mois_cible
    )

    if periode_commandement_est_passee(
        annee_cible,
        mois_cible
    ):
        return (
            False,
            t("hc.error.past_delivery")
        )

    if (
        annee_cible,
        mois_cible
    ) == (
        date_actuelle.year,
        date_actuelle.month
    ):
        date_demande = date_actuelle
    else:
        # Une demande anticipée pour un mois futur est placée au tout début
        # de ce mois. La livraison arrivera donc 2 à 3 jours plus tard.
        date_demande = datetime(
            annee_cible,
            mois_cible,
            1,
            8,
            0,
            0
        )

    cout = cout_livraison_urgente(
        taille
    )

    if not points_commandement_suffisants(
        cout
    ):
        return (
            False,
            t("hc.error.insufficient_points", cost=cout)
        )

    minimum, maximum = fourchette_livraison_urgente(
        avion,
        munition,
        taille
    )

    quantite_reelle = random.randint(
        minimum,
        maximum
    )

    delai_jours = random.randint(
        2,
        3
    )

    date_arrivee = (
        date_demande
        + timedelta(
            days=delai_jours
        )
    )

    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    try:
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        succes_debit, _ = debiter_points_commandement_transaction(
            curseur,
            cout
        )

        if not succes_debit:
            connexion.rollback()
            connexion.close()

            return (
                False,
                t("hc.error.insufficient_points", cost=cout)
            )

        curseur.execute(
            """
            INSERT INTO livraisons_urgentes (
                date_demande_jeu,
                date_arrivee_jeu,
                avion,
                munition,
                taille,
                quantite_min,
                quantite_max,
                quantite_reelle,
                cout,
                statut,
                date_reception_locale
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'EN_TRANSIT', '')
            """,
            (
                date_demande.strftime(
                    "%Y.%m.%d %H:%M:%S"
                ),
                date_arrivee.strftime(
                    "%Y.%m.%d %H:%M:%S"
                ),
                avion,
                munition,
                taille,
                int(
                    minimum
                ),
                int(
                    maximum
                ),
                int(
                    quantite_reelle
                ),
                int(
                    cout
                )
            )
        )

        connexion.commit()
        connexion.close()

    except sqlite3.Error as erreur:
        connexion.rollback()
        connexion.close()

        return (
            False,
            str(
                erreur
            )
        )

    return (
        True,
        {
            "taille": taille,
            "munition": munition,
            "minimum": minimum,
            "maximum": maximum,
            "cout": cout,
            "delai_jours": delai_jours,
            "date_demande": date_demande,
            "date_arrivee": date_arrivee
        }
    )



def enregistrer_rapport_livraison_urgente(
    date_jeu,
    munition,
    ancien_stock,
    nouveau_stock,
    quantite,
    taille
):
    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    curseur = connexion.cursor()

    curseur.execute(
        """
        INSERT INTO rapports_carriere (
            date_jeu,
            date_locale,
            type_changement,
            ancienne_valeur,
            nouvelle_valeur,
            delta,
            details,
            valide
        )
        VALUES (?, ?, 'livraison_urgente', ?, ?, ?, ?, 0)
        """,
        (
            str(
                date_jeu
            ),
            datetime.now().strftime(
                "%d.%m.%Y - %H:%M:%S"
            ),
            int(
                ancien_stock
            ),
            int(
                nouveau_stock
            ),
            int(
                quantite
            ),
            json.dumps(
                {
                    "munition": munition,
                    "quantite": int(
                        quantite
                    ),
                    "taille": taille,
                    "impact_ammo_qty": 0
                },
                ensure_ascii=False
            )
        )
    )

    connexion.commit()
    connexion.close()

    actualiser_badge_rapports()


def traiter_livraisons_urgentes(
    donnees_carriere
):
    """
    Appelé après chaque lecture de la carrière.

    Une livraison arrivée :
    - ajoute uniquement au stock concret local ;
    - ne modifie jamais ammoQty ;
    - ne modifie jamais la référence de synchronisation IL-2.
    """
    date_jeu = extraire_date_complete_carriere(
        donnees_carriere
    )

    if date_jeu is None:
        return False

    connexion = sqlite3.connect(
        FICHIER_BASE
    )

    try:
        connexion.execute(
            "BEGIN IMMEDIATE"
        )

        curseur = connexion.cursor()

        lignes = curseur.execute(
            """
            SELECT
                id,
                date_arrivee_jeu,
                avion,
                munition,
                taille,
                quantite_reelle
            FROM livraisons_urgentes
            WHERE statut = 'EN_TRANSIT'
            ORDER BY id
            """
        ).fetchall()

        livraisons_recue = []

        for (
            identifiant,
            date_arrivee_texte,
            avion,
            munition,
            taille,
            quantite_reelle
        ) in lignes:
            try:
                date_arrivee = datetime.strptime(
                    str(
                        date_arrivee_texte
                    ),
                    "%Y.%m.%d %H:%M:%S"
                )
            except ValueError:
                continue

            if date_jeu < date_arrivee:
                continue

            ligne_stock = curseur.execute(
                """
                SELECT stock
                FROM munitions
                WHERE nom = ?
                LIMIT 1
                """,
                (
                    munition,
                )
            ).fetchone()

            ancien_stock = (
                int(
                    ligne_stock[0]
                )
                if ligne_stock is not None
                else 0
            )

            nouveau_stock = (
                ancien_stock
                + int(
                    quantite_reelle
                )
            )

            if ligne_stock is None:
                curseur.execute(
                    """
                    INSERT INTO munitions (
                        nom,
                        stock
                    )
                    VALUES (?, ?)
                    """,
                    (
                        munition,
                        nouveau_stock
                    )
                )
            else:
                curseur.execute(
                    """
                    UPDATE munitions
                    SET stock = ?
                    WHERE nom = ?
                    """,
                    (
                        nouveau_stock,
                        munition
                    )
                )

            curseur.execute(
                """
                UPDATE livraisons_urgentes
                SET
                    statut = 'LIVREE',
                    date_reception_locale = ?
                WHERE id = ?
                """,
                (
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    int(
                        identifiant
                    )
                )
            )

            livraisons_recue.append(
                (
                    munition,
                    ancien_stock,
                    nouveau_stock,
                    int(
                        quantite_reelle
                    ),
                    taille
                )
            )

        connexion.commit()
        connexion.close()

    except sqlite3.Error as erreur:
        connexion.rollback()
        connexion.close()

        print(
            "Livraison urgente impossible :",
            erreur
        )

        return False

    for (
        munition,
        ancien_stock,
        nouveau_stock,
        quantite,
        taille
    ) in livraisons_recue:
        enregistrer_rapport_livraison_urgente(
            donnees_carriere.get(
                "date_jeu",
                ""
            ),
            munition,
            ancien_stock,
            nouveau_stock,
            quantite,
            taille
        )

    return bool(
        livraisons_recue
    )



def calculer_apercu_repartition_mensuelle(
    annee,
    mois,
    avion=None,
    modele=None
):
    """
    Calcule la répartition théorique du prochain ravitaillement.

    La répartition DE BASE est normalisée à 100 % selon le modèle.

    Les boosts du haut commandement sont ensuite ajoutés en POINTS
    DE POURCENTAGE, sans renormaliser le reste.

    Exemple :
    - part normale HVAR : 7 %
    - boost : +15 %
    - part effective affichée : 22 %

    Le total effectif peut donc dépasser 100 %, ce qui représente
    volontairement du matériel supplémentaire offert par le commandement.
    """
    if avion is None:
        avion = DONNEES_CARRIERE_IL2.get(
            "avion",
            avion_selectionne
        )

    if modele is None:
        modele = cle_modele_repartition_actif()

    compatibles = trier_munitions_logiquement(
        AVIONS_EMPORTS.get(
            avion,
            []
        )
    )

    if modele == "STANDARD":
        quantites = dict(
            QUANTITES_STANDARD_NIVEAUX
        )
    else:
        quantites = obtenir_quantites_niveaux_periode(
            modele,
            int(
                annee
            ),
            int(
                mois
            )
        )

    lignes = []
    total_poids_base = 0.0

    for munition in compatibles:
        if modele == "STANDARD":
            niveau = niveau_standard_effectif_avec_directive(
                int(
                    annee
                ),
                int(
                    mois
                ),
                avion,
                munition
            )

            poids_base = float(
                quantites.get(
                    niveau,
                    0.0
                )
            )

        else:
            niveau = lire_niveau_munition_periode(
                modele,
                int(
                    annee
                ),
                int(
                    mois
                ),
                avion,
                munition
            )

            poids_base = float(
                quantites.get(
                    niveau,
                    0.0
                )
            )

        poids_base = max(
            0.0,
            poids_base
        )

        boost = float(
            lire_boost_commandement(
                annee,
                mois,
                avion,
                munition
            )[
                "boost_pourcent"
            ]
        )

        lignes.append(
            {
                "munition": munition,
                "niveau": niveau,
                "poids_base": poids_base,
                "boost_pourcent": boost,
                "pourcentage_base": 0.0,
                "pourcentage": 0.0
            }
        )

        total_poids_base += poids_base

    if total_poids_base > 0:
        for ligne in lignes:
            base = (
                ligne[
                    "poids_base"
                ]
                / total_poids_base
                * 100.0
            )

            ligne[
                "pourcentage_base"
            ] = base

            ligne[
                "pourcentage"
            ] = (
                base
                + ligne[
                    "boost_pourcent"
                ]
            )

    return lignes



def ouvrir_consultation_repartition_stock():
    _debut_performance_ui = time.perf_counter()
    """
    Consultation mensuelle + panneau Haut commandement volontairement simple.

    La période initiale suit la DATE affichée dans l'interface principale.

    Exemple :
    interface = 13.04.1951 -> ouverture sur AVRIL 1951.

    La base IL-2 reste la source de vérité de la carrière, mais le Haut
    Commandement utilise volontairement cette date d'interface comme
    référence temporelle unique.
    """
    avion = DONNEES_CARRIERE_IL2.get(
        "avion",
        avion_selectionne
    )

    # Le Haut Commandement suit la date affichée dans l'interface principale.
    annee_initiale, mois_initial = (
        obtenir_annee_mois_reference_commandement()
    )

    fenetre_repartition = tk.Toplevel(
        fenetre
    )

    fenetre_repartition.after_idle(
        lambda debut=_debut_performance_ui:
        journaliser_performance_ui(
            'Répartition prévisionnelle',
            debut
        )
    )

    appliquer_chrome_custom(
        fenetre_repartition,
        t("forecast.window"),
        1940,
        960,
        fenetre_repartition.destroy
    )

    corps = tk.Frame(
        fenetre_repartition,
        bg=theme["fond"]
    )

    corps.pack(
        fill="both",
        expand=True
    )

    entete = tk.Frame(
        corps,
        height=105,
        bg=theme["barre"]
    )

    entete.pack(
        fill="x"
    )

    entete.pack_propagate(
        False
    )

    tk.Label(
        entete,
        text=t("forecast.title"),
        font=(POLICE, 17, "bold"),
        bg=theme["barre"],
        fg=theme["blanc"]
    ).pack(
        pady=(13, 2)
    )

    tk.Label(
        entete,
        text=t("forecast.subtitle", aircraft=avion),
        font=(POLICE, 8, "bold"),
        bg=theme["barre"],
        fg=theme["texte_faible"]
    ).pack()

    tk.Label(
        entete,
        text=t("forecast.description"),
        font=(POLICE, 8),
        bg=theme["barre"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(4, 0)
    )

    # ========================================================
    # BARRE PERIODE
    # ========================================================

    barre = tk.Frame(
        corps,
        bg=theme["panneau"]
    )

    barre.pack(
        fill="x",
        padx=18,
        pady=(10, 8)
    )

    # Barre réellement responsive : aucune coordonnée x/largeur fixe.
    # Chaque groupe conserve sa place et la zone d'information absorbe
    # simplement l'espace supplémentaire.
    barre.grid_columnconfigure(0, weight=3)
    barre.grid_columnconfigure(1, weight=1)
    barre.grid_columnconfigure(2, weight=2)
    barre.grid_columnconfigure(3, weight=3)
    barre.grid_columnconfigure(4, weight=7)

    tk.Label(
        barre,
        text=t("forecast.active_model"),
        font=(POLICE, 7, "bold"),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).grid(row=0, column=0, sticky="ew", padx=(12, 6), pady=(5, 2))

    label_modele = tk.Label(
        barre,
        text=nom_affiche_modele_actif(),
        font=(POLICE, 10, "bold"),
        bg=theme["champ"],
        fg=theme["texte"],
        relief="solid",
        borderwidth=1
    )
    label_modele.grid(row=1, column=0, sticky="ew", padx=(12, 6), pady=(0, 10), ipady=8)

    variable_annee = tk.IntVar(value=annee_initiale)
    variable_mois = tk.StringVar(value=t_mois(mois_initial))

    tk.Label(
        barre,
        text=t("common.year"),
        font=(POLICE, 7, "bold"),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).grid(row=0, column=1, sticky="ew", padx=6, pady=(5, 2))

    spin_annee = tk.Spinbox(
        barre,
        from_=1950,
        to=1953,
        wrap=True,
        textvariable=variable_annee,
        justify="center",
        font=(POLICE, 10, "bold"),
        bg=theme["champ"],
        fg=theme["champ_texte"],
        buttonbackground=theme["panneau_alt"],
        relief="solid",
        borderwidth=1
    )
    spin_annee.grid(row=1, column=1, sticky="ew", padx=6, pady=(0, 10), ipady=7)

    tk.Label(
        barre,
        text=t("common.month"),
        font=(POLICE, 7, "bold"),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).grid(row=0, column=2, sticky="ew", padx=6, pady=(5, 2))

    spin_mois = tk.Spinbox(
        barre,
        values=tuple(t_mois(numero) for numero in range(1, 13)),
        wrap=True,
        state="readonly",
        textvariable=variable_mois,
        justify="center",
        font=(POLICE, 9, "bold"),
        bg=theme["champ"],
        fg=theme["champ_texte"],
        readonlybackground=theme["champ"],
        buttonbackground=theme["panneau_alt"],
        relief="solid",
        borderwidth=1
    )
    spin_mois.grid(row=1, column=2, sticky="ew", padx=6, pady=(0, 10), ipady=7)

    # --------------------------------------------------------
    # CORRECTIF DATE DE CARRIERE
    # --------------------------------------------------------
    variable_annee.set(int(annee_initiale))
    positionner_spinbox_mois(spin_mois, variable_mois, mois_initial)

    bouton_urgence = tk.Button(
        barre,
        text=t("forecast.request"),
        font=(POLICE, 8, "bold"),
        bg=COULEUR_OR_COMMANDEMENT,
        fg="#171914",
        activebackground=COULEUR_OR_COMMANDEMENT_ACTIF,
        activeforeground="#171914",
        disabledforeground="#5a5548",
        relief="solid",
        borderwidth=1,
        cursor="hand2",
        anchor="center",
        justify="center",
        padx=4,
        pady=0
    )
    bouton_urgence.grid(row=1, column=3, sticky="ew", padx=6, pady=(0, 10), ipady=7)

    # Le statut peut grandir/rétrécir sans pousser les autres commandes.
    label_info = tk.Label(
        barre,
        text="",
        font=(POLICE, 8, "bold"),
        anchor="e",
        justify="right",
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    )
    label_info.grid(row=0, column=4, rowspan=2, sticky="nsew", padx=(10, 12), pady=(5, 10))

    # ========================================================
    # ZONE 3 COLONNES
    # ========================================================

    zone_principale = tk.Frame(
        corps,
        bg=theme["fond"]
    )

    zone_principale.pack(
        fill="both",
        expand=True,
        padx=18,
        pady=(0, 14)
    )

    # Layout réellement responsive : les trois panneaux occupent toujours
    # toute la largeur disponible. Les proportions restent stables et les
    # contenus internes gèrent eux-mêmes leur scroll quand l'écran est petit.
    zone_principale.grid_rowconfigure(0, weight=1)
    zone_principale.grid_columnconfigure(0, weight=30, uniform="forecast_cols")
    zone_principale.grid_columnconfigure(1, weight=30, uniform="forecast_cols")
    zone_principale.grid_columnconfigure(2, weight=40, uniform="forecast_cols")

    # -----------------------
    # GAUCHE
    # -----------------------

    panneau_gauche = tk.Frame(
        zone_principale,
        bg=theme["panneau"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    panneau_gauche.grid(
        row=0,
        column=0,
        sticky="nsew"
    )

    tk.Label(
        panneau_gauche,
        text=t("model.importance"),
        font=(POLICE, 10, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(12, 3)
    )

    tk.Label(
        panneau_gauche,
        text=t("forecast.list_header"),
        font=(POLICE, 7),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 8)
    )

    # Bandeau de directive unique.
    cadre_directive_active = tk.Frame(
        panneau_gauche,
        bg=theme["panneau_alt"],
        highlightbackground=COULEUR_OR_COMMANDEMENT_ACTIF,
        highlightthickness=1
    )

    label_directive_active = tk.Label(
        cadre_directive_active,
        text="",
        font=(POLICE, 12, "bold"),
        anchor="w",
        bg=theme["panneau_alt"],
        fg=COULEUR_OR_COMMANDEMENT_ACTIF
    )

    label_directive_active.pack(
        fill="x",
        padx=14,
        pady=(9, 1)
    )

    label_directive_active_periode = tk.Label(
        cadre_directive_active,
        text="",
        font=(POLICE, 8, "bold"),
        anchor="w",
        bg=theme["panneau_alt"],
        fg=theme["texte_faible"]
    )

    label_directive_active_periode.pack(
        fill="x",
        padx=14,
        pady=(0, 9)
    )

    zone_liste = tk.Frame(
        panneau_gauche,
        bg=theme["panneau"]
    )

    zone_liste.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=(0, 10)
    )

    scroll_liste = tk.Scrollbar(
        zone_liste,
        orient="vertical"
    )

    scroll_liste.pack(
        side="right",
        fill="y"
    )

    canvas_liste = tk.Canvas(
        zone_liste,
        bg=theme["panneau"],
        highlightthickness=0,
        yscrollcommand=scroll_liste.set
    )

    canvas_liste.pack(
        side="left",
        fill="both",
        expand=True
    )

    scroll_liste.configure(
        command=canvas_liste.yview
    )

    contenu_liste = tk.Frame(
        canvas_liste,
        bg=theme["panneau"]
    )

    item_liste = canvas_liste.create_window(
        0,
        0,
        window=contenu_liste,
        anchor="nw"
    )

    contenu_liste.bind(
        "<Configure>",
        lambda event:
        canvas_liste.configure(
            scrollregion=(
                canvas_liste.bbox(
                    "all"
                )
                or (
                    0,
                    0,
                    1,
                    1
                )
            )
        )
    )

    canvas_liste.bind(
        "<Configure>",
        lambda event:
        canvas_liste.itemconfig(
            item_liste,
            width=event.width
        )
    )

    # -----------------------
    # CENTRE
    # -----------------------

    panneau_centre = tk.Frame(
        zone_principale,
        bg=theme["panneau"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    panneau_centre.grid(
        row=0,
        column=1,
        sticky="nsew",
        padx=(9, 0)
    )

    tk.Label(
        panneau_centre,
        text=t("forecast.estimated"),
        font=(POLICE, 10, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(12, 2)
    )

    label_periode_centre = tk.Label(
        panneau_centre,
        text="",
        font=(POLICE, 8),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    )

    label_periode_centre.pack(
        pady=(0, 4)
    )

    canvas_donut = tk.Canvas(
        panneau_centre,
        width=420,
        height=420,
        bg=theme["panneau"],
        highlightthickness=0
    )

    canvas_donut.pack(
        fill="both",
        expand=True,
        padx=18,
        pady=(8, 0)
    )

    tk.Label(
        panneau_centre,
        text=t("forecast.bonus_note"),
        font=(POLICE, 8),
        justify="center",
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(6, 0)
    )

    # -----------------------
    # HAUT COMMANDEMENT
    # -----------------------

    panneau_commandement = tk.Frame(
        zone_principale,
        bg=theme["panneau"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    panneau_commandement.grid(
        row=0,
        column=2,
        sticky="nsew",
        padx=(9, 0)
    )

    tk.Label(
        panneau_commandement,
        text=t("hc.title"),
        font=(POLICE, 11, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(12, 3)
    )

    tk.Label(
        panneau_commandement,
        text=t("hc.subtitle"),
        font=(POLICE, 8, "bold"),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 10)
    )

    cadre_points = tk.Frame(
        panneau_commandement,
        bg=theme["panneau_alt"],
        highlightbackground=COULEUR_OR_COMMANDEMENT,
        highlightthickness=1
    )

    cadre_points.pack(
        fill="x",
        padx=14,
        pady=(0, 12)
    )

    tk.Label(
        cadre_points,
        text=t("hc.balance"),
        font=(POLICE, 8, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(8, 1)
    )

    label_points = tk.Label(
        cadre_points,
        text="50",
        font=(POLICE, 27, "bold"),
        bg=theme["panneau_alt"],
        fg=COULEUR_OR_COMMANDEMENT_ACTIF
    )

    label_points.pack()

    labels_points_commandement_ouverts.append(
        label_points
    )

    label_gain_points = tk.Label(
        cadre_points,
        text=texte_gain_points_journalier(),
        font=(POLICE, 7, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["vert"]
    )

    label_gain_points.pack(
        pady=(0, 3)
    )

    labels_gain_commandement_ouverts.append(
        label_gain_points
    )

    tk.Label(
        cadre_points,
        text=t(
            "hc.costs",
            boost15=COUT_BOOST_15,
            boost30=COUT_BOOST_30,
            small=COUT_LIVRAISON_PETITE,
            large=COUT_LIVRAISON_GRANDE,
            directive=COUT_DIRECTIVE_REPARTITION
        ),
        font=(POLICE, 7, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(1, 8)
    )

    label_mode_admin = tk.Label(
        cadre_points,
        text="",
        font=(POLICE, 7, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["vert"]
    )

    label_mode_admin.pack(
        fill="x",
        padx=10,
        pady=(0, 7),
        ipady=3
    )

    visibilite_modificateurs_active = tk.BooleanVar(
        value=True
    )

    bouton_visibilite_modificateurs = tk.Button(
        cadre_points,
        text=t("forecast.modifiers.on"),
        font=(POLICE, 7, "bold"),
        bg=COULEUR_OR_COMMANDEMENT,
        fg=theme["barre"],
        activebackground=COULEUR_OR_COMMANDEMENT_ACTIF,
        activeforeground=theme["barre"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    )

    bouton_visibilite_modificateurs.pack(
        fill="x",
        padx=10,
        pady=(0, 9),
        ipady=5
    )

    cadre_transit = tk.Frame(
        panneau_commandement,
        bg=theme["panneau"]
    )

    cadre_transit.pack(
        fill="both",
        expand=True,
        padx=14,
        pady=(0, 12)
    )

    label_transit = tk.Label(
        cadre_transit,
        text="",
        font=(POLICE, 8),
        justify="left",
        anchor="nw",
        wraplength=420,
        bg=theme["panneau"],
        fg=theme["texte"]
    )

    label_transit.pack(
        fill="both",
        expand=True
    )

    panneau_commandement.bind(
        "<Configure>",
        lambda event: label_transit.configure(
            wraplength=max(220, event.width - 40)
        ),
        add="+"
    )

    # ========================================================
    # HELPERS UI
    # ========================================================

    def mois_numero():
        texte = str(
            variable_mois.get()
            or ""
        ).strip()

        for numero, nom in MOIS_FRANCAIS.items():
            if (
                nom.casefold() == texte.casefold()
                or t_mois(numero).casefold() == texte.casefold()
            ):
                return int(
                    numero
                )

        return int(
            mois_initial
        )

    def periode_affichee_est_actuelle():
        annee_actuelle, mois_actuel = (
            obtenir_annee_mois_reference_commandement()
        )

        try:
            annee_affichee = int(
                variable_annee.get()
            )
        except Exception:
            annee_affichee = annee_initiale

        return (
            annee_affichee == annee_actuelle
            and mois_numero() == mois_actuel
        )

    def ouvrir_demande_commandement():
        try:
            annee_cible = int(
                variable_annee.get()
            )
        except Exception:
            annee_cible = int(
                annee_initiale
            )

        mois_cible = mois_numero()

        if periode_commandement_est_passee(
            annee_cible,
            mois_cible
        ):
            dialogue_message_custom(
                t("hc.period.past_title"),
                t("hc.period.past_body"),
                "info",
                fenetre_repartition
            )
            return

        # La fenêtre de requête reste consultable même lorsque le joueur
        # n'a pas assez de points. Chaque action gère ensuite son propre
        # coût et son état activé/désactivé.
        points = obtenir_points_commandement()

        dialogue = tk.Toplevel(
            fenetre_repartition
        )

        appliquer_chrome_custom(
            dialogue,
            t("hc.request.window"),
            1180,
            720,
            dialogue.destroy
        )

        fond = tk.Frame(
            dialogue,
            bg=theme["fond"]
        )

        fond.pack(
            fill="both",
            expand=True
        )

        tk.Label(
            fond,
            text=t("hc.request.title"),
            font=(POLICE, 15, "bold"),
            bg=theme["fond"],
            fg=theme["texte"]
        ).pack(
            pady=(16, 3)
        )

        tk.Label(
            fond,
            text=t(
                "hc.request.summary",
                aircraft=avion,
                period=f"{t_mois(mois_cible)} {annee_cible}",
                points=(
                    t("hc.admin.short")
                    if mode_developpeur_actif()
                    else t(
                        "hc.points.available",
                        points=formater_points_commandement(points)
                    )
                )
            ),
            font=(POLICE, 8, "bold"),
            bg=theme["fond"],
            fg=COULEUR_OR_COMMANDEMENT_ACTIF
        ).pack(
            pady=(0, 5)
        )

        tk.Label(
            fond,
            text=t("hc.request.help"),
            font=(POLICE, 8),
            bg=theme["fond"],
            fg=theme["texte_faible"]
        ).pack(
            pady=(0, 12)
        )

        zone = tk.Frame(
            fond,
            bg=theme["fond"]
        )

        zone.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 16)
        )

        # ----------------------------------------------------
        # GAUCHE : MUNITIONS
        # ----------------------------------------------------

        panneau_munitions = tk.Frame(
            zone,
            width=585,
            bg=theme["panneau"],
            highlightbackground=theme["bordure"],
            highlightthickness=1
        )

        panneau_munitions.pack(
            side="left",
            fill="both"
        )

        panneau_munitions.pack_propagate(
            False
        )

        tk.Label(
            panneau_munitions,
            text=t("common.ammunition"),
            font=(POLICE, 9, "bold"),
            bg=theme["panneau"],
            fg=theme["texte"]
        ).pack(
            pady=(10, 6)
        )

        cadre_scroll = tk.Frame(
            panneau_munitions,
            bg=theme["panneau"]
        )

        cadre_scroll.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10)
        )

        canvas = tk.Canvas(
            cadre_scroll,
            bg=theme["panneau"],
            highlightthickness=0
        )

        canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar = tk.Scrollbar(
            cadre_scroll,
            orient="vertical",
            command=canvas.yview
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        canvas.configure(
            yscrollcommand=scrollbar.set
        )

        contenu = tk.Frame(
            canvas,
            bg=theme["panneau"]
        )

        item = canvas.create_window(
            0,
            0,
            window=contenu,
            anchor="nw"
        )

        contenu.bind(
            "<Configure>",
            lambda event:
            canvas.configure(
                scrollregion=(
                    canvas.bbox(
                        "all"
                    )
                    or (
                        0,
                        0,
                        1,
                        1
                    )
                )
            )
        )

        canvas.bind(
            "<Configure>",
            lambda event:
            canvas.itemconfig(
                item,
                width=event.width
            )
        )

        selection = tk.StringVar(
            value=""
        )

        boutons_munitions = {}

        # ----------------------------------------------------
        # DROITE : TROIS ACTIONS
        # ----------------------------------------------------

        panneau_actions = tk.Frame(
            zone,
            width=545,
            bg=theme["panneau"],
            highlightbackground=theme["bordure"],
            highlightthickness=1
        )

        panneau_actions.pack(
            side="left",
            fill="both",
            padx=(10, 0)
        )

        panneau_actions.pack_propagate(
            False
        )

        tk.Label(
            panneau_actions,
            text=t("hc.action"),
            font=(POLICE, 9, "bold"),
            bg=theme["panneau"],
            fg=theme["texte"]
        ).pack(
            pady=(10, 4)
        )

        label_selection = tk.Label(
            panneau_actions,
            text=t("hc.select_ammo"),
            font=(POLICE, 8),
            bg=theme["panneau"],
            fg=theme["texte_faible"],
            wraplength=480
        )

        label_selection.pack(
            pady=(0, 10)
        )

        bouton_boost_15 = tk.Button(
            panneau_actions,
            text=t("hc.boost15", cost=COUT_BOOST_15),
            font=(POLICE, 9, "bold"),
            bg=theme["panneau_alt"],
            fg=theme["texte"],
            activebackground=COULEUR_OR_COMMANDEMENT,
            activeforeground=theme["barre"],
            relief="solid",
            borderwidth=1,
            state="disabled",
            cursor="arrow"
        )

        bouton_boost_15.pack(
            fill="x",
            padx=18,
            pady=(5, 7),
            ipady=12
        )

        bouton_boost_30 = tk.Button(
            panneau_actions,
            text=t("hc.boost30", cost=COUT_BOOST_30),
            font=(POLICE, 9, "bold"),
            bg=theme["panneau_alt"],
            fg=theme["texte"],
            activebackground=COULEUR_OR_COMMANDEMENT,
            activeforeground=theme["barre"],
            relief="solid",
            borderwidth=1,
            state="disabled",
            cursor="arrow"
        )

        bouton_boost_30.pack(
            fill="x",
            padx=18,
            pady=7,
            ipady=12
        )

        cadre_urgence = tk.Frame(
            panneau_actions,
            bg=theme["panneau_alt"],
            highlightbackground=COULEUR_OR_COMMANDEMENT,
            highlightthickness=1
        )

        cadre_urgence.pack(
            fill="x",
            padx=18,
            pady=7
        )

        tk.Label(
            cadre_urgence,
            text=t("hc.emergency.title"),
            font=(POLICE, 9, "bold"),
            bg=theme["panneau_alt"],
            fg=theme["texte"]
        ).pack(
            pady=(9, 2)
        )

        tk.Label(
            cadre_urgence,
            text=t("hc.emergency.subtitle"),
            font=(POLICE, 7),
            bg=theme["panneau_alt"],
            fg=theme["texte_faible"]
        ).pack(
            pady=(0, 7)
        )

        bouton_petite = tk.Button(
            cadre_urgence,
            text=t("delivery.small"),
            font=(POLICE, 8, "bold"),
            bg=theme["champ"],
            fg=theme["texte"],
            activebackground=COULEUR_OR_COMMANDEMENT,
            activeforeground=theme["barre"],
            relief="solid",
            borderwidth=1,
            state="disabled",
            cursor="arrow"
        )

        bouton_petite.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(10, 4),
            pady=(0, 10),
            ipady=8
        )

        bouton_grande = tk.Button(
            cadre_urgence,
            text=t("delivery.large"),
            font=(POLICE, 8, "bold"),
            bg=theme["champ"],
            fg=theme["texte"],
            activebackground=COULEUR_OR_COMMANDEMENT,
            activeforeground=theme["barre"],
            relief="solid",
            borderwidth=1,
            state="disabled",
            cursor="arrow"
        )

        bouton_grande.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(4, 10),
            pady=(0, 10),
            ipady=8
        )

        cadre_directive = tk.Frame(
            panneau_actions,
            bg=theme["panneau_alt"],
            highlightbackground=theme["bordure"],
            highlightthickness=1
        )

        cadre_directive.pack(
            fill="x",
            padx=18,
            pady=7
        )

        tk.Label(
            cadre_directive,
            text=t("hc.directive.title"),
            font=(POLICE, 9, "bold"),
            bg=theme["panneau_alt"],
            fg=theme["texte"]
        ).pack(
            pady=(9, 2)
        )

        tk.Label(
            cadre_directive,
            text=t("hc.directive.description"),
            font=(POLICE, 7),
            wraplength=470,
            justify="center",
            bg=theme["panneau_alt"],
            fg=theme["texte_faible"]
        ).pack(
            padx=10,
            pady=(0, 7)
        )

        bouton_directive = tk.Button(
            cadre_directive,
            text=t(
                "hc.directive.edit",
                cost=COUT_DIRECTIVE_REPARTITION
            ),
            font=(POLICE, 8, "bold"),
            bg=COULEUR_OR_COMMANDEMENT,
            fg=theme["barre"],
            activebackground=COULEUR_OR_COMMANDEMENT_ACTIF,
            activeforeground=theme["barre"],
            relief="solid",
            borderwidth=1,
            cursor="hand2"
        )

        bouton_directive.pack(
            fill="x",
            padx=10,
            pady=(0, 10),
            ipady=7
        )


        annee_directive_initiale, mois_directive_initial = (
            mois_suivant_commandement(
                annee_cible,
                mois_cible
            )
        )

        evenement_directive_initial = (
            lire_evenement_directive_standard_exact(
                annee_directive_initiale,
                mois_directive_initial,
                avion
            )
        )

        directive_initialement_gratuite = (
            evenement_directive_initial is not None
            and evenement_directive_initial[
                "mode"
            ] == "CUSTOM"
            and evenement_directive_initial[
                "cout"
            ] > 0
        )

        bouton_directive.configure(
            state=(
                "normal"
                if (
                    directive_initialement_gratuite
                    or mode_developpeur_actif()
                    or obtenir_points_commandement() >= COUT_DIRECTIVE_REPARTITION
                )
                else "disabled"
            ),
            cursor=(
                "hand2"
                if (
                    directive_initialement_gratuite
                    or mode_developpeur_actif()
                    or obtenir_points_commandement() >= COUT_DIRECTIVE_REPARTITION
                )
                else "arrow"
            )
        )


        label_note = tk.Label(
            panneau_actions,
            text=t("hc.boost.note"),
            font=(POLICE, 7),
            justify="center",
            bg=theme["panneau"],
            fg=theme["texte_faible"]
        )

        label_note.pack(
            pady=(10, 0)
        )

        def ouvrir_editeur_directive_standard():
            annee_effet, mois_effet = (
                mois_suivant_commandement(
                    annee_cible,
                    mois_cible
                )
            )

            compatibles_directive = (
                trier_munitions_logiquement(
                    AVIONS_EMPORTS.get(
                        avion,
                        []
                    )
                )
            )

            evenement_exact = (
                lire_evenement_directive_standard_exact(
                    annee_effet,
                    mois_effet,
                    avion
                )
            )

            # On part de la configuration réellement applicable au mois suivant
            # la période ciblée : historique ou directive permanente précédente.
            priorites = {
                munition:
                niveau_standard_effectif_avec_directive(
                    annee_effet,
                    mois_effet,
                    avion,
                    munition
                )
                for munition in compatibles_directive
            }

            editeur = tk.Toplevel(
                dialogue
            )

            appliquer_chrome_custom(
                editeur,
                t("hc.directive.window"),
                1280,
                820,
                editeur.destroy
            )

            fond_editeur = tk.Frame(
                editeur,
                bg=theme["fond"]
            )

            fond_editeur.pack(
                fill="both",
                expand=True
            )

            tk.Label(
                fond_editeur,
                text=t("hc.directive.editor_title"),
                font=(POLICE, 15, "bold"),
                bg=theme["fond"],
                fg=theme["texte"]
            ).pack(
                pady=(17, 3)
            )

            tk.Label(
                fond_editeur,
                text=t(
                    "hc.directive.effect",
                    aircraft=avion,
                    period=f"{t_mois(mois_effet)} {annee_effet}"
                ),
                font=(POLICE, 8, "bold"),
                bg=theme["fond"],
                fg=COULEUR_OR_COMMANDEMENT_ACTIF
            ).pack(
                pady=(0, 4)
            )

            tk.Label(
                fond_editeur,
                text=t("hc.directive.persistence"),
                font=(POLICE, 8),
                bg=theme["fond"],
                fg=theme["texte_faible"]
            ).pack(
                pady=(0, 12)
            )

            zone_principale_directive = tk.Frame(
                fond_editeur,
                bg=theme["panneau"],
                highlightbackground=theme["bordure"],
                highlightthickness=1
            )

            zone_principale_directive.pack(
                fill="both",
                expand=True,
                padx=18,
                pady=(0, 10)
            )

            entete_liste = tk.Frame(
                zone_principale_directive,
                height=38,
                bg=theme["panneau_alt"]
            )

            entete_liste.pack(
                fill="x"
            )

            entete_liste.pack_propagate(
                False
            )

            tk.Label(
                entete_liste,
                text=t("common.ammunition"),
                font=(POLICE, 8, "bold"),
                anchor="w",
                bg=theme["panneau_alt"],
                fg=theme["texte_faible"]
            ).place(
                x=18,
                y=0,
                width=700,
                height=38
            )

            label_quota = tk.Label(
                entete_liste,
                text="",
                font=(POLICE, 8, "bold"),
                anchor="e",
                bg=theme["panneau_alt"],
                fg=theme["texte_faible"]
            )

            label_quota.place(
                x=730,
                y=0,
                width=500,
                height=38
            )

            cadre_scroll_directive = tk.Frame(
                zone_principale_directive,
                bg=theme["panneau"]
            )

            cadre_scroll_directive.pack(
                fill="both",
                expand=True,
                padx=8,
                pady=8
            )

            canvas_directive = tk.Canvas(
                cadre_scroll_directive,
                bg=theme["panneau"],
                highlightthickness=0
            )

            canvas_directive.pack(
                side="left",
                fill="both",
                expand=True
            )

            scroll_directive = tk.Scrollbar(
                cadre_scroll_directive,
                orient="vertical",
                command=canvas_directive.yview
            )

            scroll_directive.pack(
                side="right",
                fill="y"
            )

            canvas_directive.configure(
                yscrollcommand=scroll_directive.set
            )

            contenu_directive = tk.Frame(
                canvas_directive,
                bg=theme["panneau"]
            )

            item_directive = canvas_directive.create_window(
                0,
                0,
                window=contenu_directive,
                anchor="nw"
            )

            contenu_directive.bind(
                "<Configure>",
                lambda event:
                canvas_directive.configure(
                    scrollregion=(
                        canvas_directive.bbox(
                            "all"
                        )
                        or (
                            0,
                            0,
                            1,
                            1
                        )
                    )
                )
            )

            canvas_directive.bind(
                "<Configure>",
                lambda event:
                canvas_directive.itemconfig(
                    item_directive,
                    width=event.width
                )
            )

            variables_directive = {
                munition: tk.StringVar(
                    value=priorites[
                        munition
                    ]
                )
                for munition in compatibles_directive
            }

            boutons_directive = {}

            couleurs_niveaux_directive = {
                "TRÈS ÉLEVÉE": "#b75b55",
                "ÉLEVÉE": "#b98548",
                "NORMALE": theme["bleu"],
                "FAIBLE": theme["vert"],
                "TRÈS FAIBLE": "#7f8379",
                "INDISPONIBLE": theme["bordure"]
            }

            def affectations_directive():
                return {
                    munition: variable.get()
                    for munition, variable
                    in variables_directive.items()
                }

            def rafraichir_directive():
                affectations = affectations_directive()

                compteurs = compter_affectations_par_niveau(
                    affectations
                )

                label_quota.configure(
                    text=t(
                        "hc.directive.quota",
                        critical=compteurs.get("TRÈS ÉLEVÉE", 0),
                        strong=compteurs.get("ÉLEVÉE", 0)
                    )
                )

                for munition, bouton in boutons_directive.items():
                    niveau = variables_directive[
                        munition
                    ].get()

                    fond_niveau = couleurs_niveaux_directive.get(
                        niveau,
                        theme["panneau_alt"]
                    )

                    bouton.configure(
                        text=nom_affiche_niveau_repartition(
                            niveau
                        ),
                        bg=fond_niveau,
                        fg=theme["blanc"],
                        activebackground=fond_niveau,
                        activeforeground=theme["blanc"]
                    )

            def cycle_directive(
                munition
            ):
                variable = variables_directive[
                    munition
                ]

                affectations = affectations_directive()

                try:
                    index_depart = list(
                        NIVEAUX_REPARTITION
                    ).index(
                        variable.get()
                    )
                except ValueError:
                    index_depart = -1

                for decalage in range(
                    1,
                    len(
                        NIVEAUX_REPARTITION
                    )
                    + 1
                ):
                    candidat = NIVEAUX_REPARTITION[
                        (
                            index_depart
                            + decalage
                        )
                        % len(
                            NIVEAUX_REPARTITION
                        )
                    ]

                    if niveau_repartition_disponible(
                        candidat,
                        affectations,
                        ignorer_munition=munition
                    ):
                        variable.set(
                            candidat
                        )
                        break

                rafraichir_directive()

            for munition in compatibles_directive:
                ligne_directive = tk.Frame(
                    contenu_directive,
                    height=54,
                    bg=theme["panneau"],
                    highlightbackground=theme["separateur"],
                    highlightthickness=1
                )

                ligne_directive.pack(
                    fill="x",
                    pady=2
                )

                ligne_directive.pack_propagate(
                    False
                )

                tk.Label(
                    ligne_directive,
                    text=t_munition(munition),
                    font=(POLICE, 8, "bold"),
                    anchor="w",
                    bg=theme["panneau"],
                    fg=theme["texte"]
                ).place(
                    x=14,
                    y=0,
                    width=720,
                    height=54
                )

                niveau = variables_directive[
                    munition
                ].get()

                fond_niveau = couleurs_niveaux_directive.get(
                    niveau,
                    theme["panneau_alt"]
                )

                bouton_niveau = tk.Button(
                    ligne_directive,
                    text=nom_affiche_niveau_repartition(
                        niveau
                    ),
                    command=lambda m=munition:
                    cycle_directive(
                        m
                    ),
                    font=(POLICE, 8, "bold"),
                    bg=fond_niveau,
                    fg=theme["blanc"],
                    activebackground=fond_niveau,
                    activeforeground=theme["blanc"],
                    relief="solid",
                    borderwidth=1,
                    cursor="hand2"
                )

                bouton_niveau.place(
                    x=785,
                    y=8,
                    width=390,
                    height=38
                )

                boutons_directive[
                    munition
                ] = bouton_niveau

            zone_actions_directive = tk.Frame(
                fond_editeur,
                height=72,
                bg=theme["fond"]
            )

            zone_actions_directive.pack(
                fill="x",
                padx=18,
                pady=(0, 14)
            )

            zone_actions_directive.pack_propagate(
                False
            )

            def sauvegarder_directive():
                affectations = affectations_directive()

                erreurs = verifier_limites_niveaux(
                    affectations
                )

                if erreurs:
                    dialogue_message_custom(
                        t("hc.directive.invalid_title"),
                        t("hc.directive.invalid_body"),
                        "info",
                        editeur
                    )
                    return

                succes, resultat = enregistrer_directive_standard_commandement(
                    avion,
                    annee_effet,
                    mois_effet,
                    affectations
                )

                if not succes:
                    dialogue_message_custom(
                        t("hc.directive.refused"),
                        str(
                            resultat
                        ),
                        "info",
                        editeur
                    )
                    return

                editeur.destroy()
                dialogue.destroy()
                rafraichir()

                cout = int(
                    resultat[
                        "cout"
                    ]
                )

                dialogue_message_custom(
                    t("hc.directive.saved"),
                    t(
                        "hc.directive.saved_body",
                        period=f"{t_mois(mois_effet)} {annee_effet}",
                        cost=(
                            t("hc.cost.admin")
                            if mode_developpeur_actif()
                            else t("hc.cost.points", cost=COUT_DIRECTIVE_REPARTITION)
                        ),
                        correction=(
                            t("hc.directive.correction_free")
                            if cout <= 0
                            else ""
                        )
                    ),
                    "info",
                    fenetre_repartition
                )

            def retablir_standard():
                confirmer = dialogue_message_custom(
                    t("hc.directive.restore_title"),
                    t(
                        "hc.directive.restore_body",
                        period=f"{t_mois(mois_effet)} {annee_effet}"
                    ),
                    "question",
                    editeur
                )

                if not confirmer:
                    return

                succes, message = programmer_retablissement_standard(
                    avion,
                    annee_effet,
                    mois_effet
                )

                if not succes:
                    dialogue_message_custom(
                        t("hc.directive.reset_fail"),
                        str(
                            message
                        ),
                        "error",
                        editeur
                    )
                    return

                editeur.destroy()
                dialogue.destroy()
                rafraichir()

                dialogue_message_custom(
                    t("hc.directive.restored_title"),
                    t("hc.directive.restored_body", period=f"{t_mois(mois_effet)} {annee_effet}"),
                    "info",
                    fenetre_repartition
                )

            bouton_reset = tk.Button(
                zone_actions_directive,
                text=t("hc.directive.restore_button"),
                command=retablir_standard,
                font=(POLICE, 8, "bold"),
                bg=theme["panneau_alt"],
                fg=theme["texte"],
                activebackground=theme["bleu"],
                activeforeground=theme["blanc"],
                relief="solid",
                borderwidth=1,
                cursor="hand2"
            )

            bouton_reset.pack(
                side="left",
                fill="y",
                ipadx=20
            )

            cout_texte = (
                "CORRIGER LA DIRECTIVE"
                if (
                    evenement_exact is not None
                    and evenement_exact[
                        "mode"
                    ] == "CUSTOM"
                    and evenement_exact[
                        "cout"
                    ] > 0
                )
                else (
                    f"ENVOYER LA DIRECTIVE  •  "
                    f"{COUT_DIRECTIVE_REPARTITION} POINTS"
                )
            )

            bouton_sauver = tk.Button(
                zone_actions_directive,
                text=cout_texte,
                command=sauvegarder_directive,
                font=(POLICE, 9, "bold"),
                bg=COULEUR_OR_COMMANDEMENT,
                fg=theme["barre"],
                activebackground=COULEUR_OR_COMMANDEMENT_ACTIF,
                activeforeground=theme["barre"],
                relief="solid",
                borderwidth=1,
                cursor="hand2"
            )

            bouton_sauver.pack(
                side="right",
                fill="y",
                ipadx=24
            )

            lier_molette_recursivement(
                contenu_directive,
                canvas_directive
            )

            rafraichir_directive()


        bouton_directive.configure(
            command=ouvrir_editeur_directive_standard
        )


        def effectuer_boost(
            valeur
        ):
            munition = selection.get()

            if not munition:
                return

            cout_prevu = cout_boost_commandement(
                valeur
            )

            texte_cout = (
                t("hc.cost.admin")
                if mode_developpeur_actif()
                else t("hc.cost.points", cost=cout_prevu)
            )

            confirmer = dialogue_message_custom(
                t("hc.confirm.request_title"),
                t(
                    "hc.confirm.request_body",
                    munition=t_munition(munition),
                    period=f"{t_mois(mois_cible)} {annee_cible}",
                    value=f"{valeur:.0f}",
                    cost=texte_cout
                ),
                "question",
                dialogue
            )

            if not confirmer:
                return

            succes, resultat = appliquer_boost_commandement(
                annee_cible,
                mois_cible,
                avion,
                munition,
                valeur
            )

            if not succes:
                dialogue_message_custom(
                    t("hc.request.denied"),
                    str(
                        resultat
                    ),
                    "info",
                    dialogue
                )
                return

            dialogue.destroy()
            rafraichir()

            dialogue_message_custom(
                t("hc.request.approved"),
                t(
                    "hc.request.approved_body",
                    munition=t_munition(munition),
                    value=f"{valeur:.0f}",
                    cost=(
                        t("hc.cost.admin")
                        if mode_developpeur_actif()
                        else t("hc.cost.points", cost=resultat["cout"])
                    )
                ),
                "info",
                fenetre_repartition
            )

        def effectuer_urgence(
            taille
        ):
            munition = selection.get()

            if not munition:
                return

            minimum, maximum = fourchette_livraison_urgente(
                avion,
                munition,
                taille
            )

            cout_prevu = cout_livraison_urgente(
                taille
            )

            texte_cout = (
                t("hc.cost.admin") if mode_developpeur_actif()
                else t("hc.cost.points", cost=cout_prevu)
            )

            confirmer = dialogue_message_custom(
                t("hc.confirm.delivery_title"),
                t(
                    "hc.confirm.delivery_body",
                    munition=t_munition(munition),
                    period=f"{t_mois(mois_cible)} {annee_cible}",
                    size=t_taille_livraison(taille),
                    minimum=minimum, maximum=maximum, cost=texte_cout
                ),
                "question",
                dialogue
            )

            if not confirmer:
                return

            succes, resultat = creer_livraison_urgente(
                avion,
                munition,
                taille,
                annee_cible=annee_cible,
                mois_cible=mois_cible
            )

            if not succes:
                dialogue_message_custom(
                    t("hc.request.denied"),
                    str(
                        resultat
                    ),
                    "info",
                    dialogue
                )
                return

            dialogue.destroy()
            rafraichir()

            dialogue_message_custom(
                t("hc.delivery.scheduled"),
                t(
                    "hc.delivery.scheduled_body",
                    munition=t_munition(munition),
                    size=t_taille_livraison(taille).lower(),
                    minimum=resultat["minimum"], maximum=resultat["maximum"],
                    cost=(
                        t("hc.cost.admin") if mode_developpeur_actif()
                        else t("hc.cost.points", cost=resultat["cout"])
                    ),
                    arrival=resultat["date_arrivee"].strftime("%d.%m.%Y")
                ),
                "info",
                fenetre_repartition
            )

        def actualiser_actions():
            munition = selection.get()

            if not munition:
                return

            stock = lire_stock_unitaire(
                munition
            )

            boost = lire_boost_commandement(
                annee_cible,
                mois_cible,
                avion,
                munition
            )[
                "boost_pourcent"
            ]

            label_selection.configure(
                text=(
                    f"{t_munition(munition)}\n"
                    + t("common.stock") + f" : {stock}"
                    + (
                        "  •  " + t("hc.current_boost", boost=f"{boost:.0f}")
                        if boost > 0 else ""
                    )
                ),
                fg=theme["texte"]
            )

            points_actuels = obtenir_points_commandement()

            annee_directive, mois_directive = (
                mois_suivant_commandement(
                    annee_cible,
                    mois_cible
                )
            )

            evenement_directive_deja_paye = (
                lire_evenement_directive_standard_exact(
                    annee_directive,
                    mois_directive,
                    avion
                )
            )

            directive_gratuite_a_corriger = (
                evenement_directive_deja_paye is not None
                and evenement_directive_deja_paye[
                    "mode"
                ] == "CUSTOM"
                and evenement_directive_deja_paye[
                    "cout"
                ] > 0
            )

            bouton_directive.configure(
                state=(
                    "normal"
                    if (
                        directive_gratuite_a_corriger
                        or mode_developpeur_actif()
                        or points_actuels >= COUT_DIRECTIVE_REPARTITION
                    )
                    else "disabled"
                ),
                cursor=(
                    "hand2"
                    if (
                        directive_gratuite_a_corriger
                        or mode_developpeur_actif()
                        or points_actuels >= COUT_DIRECTIVE_REPARTITION
                    )
                    else "arrow"
                ),
                text=(
                    t("hc.directive.correct_programmed")
                    if directive_gratuite_a_corriger
                    else t("hc.directive.edit", cost=COUT_DIRECTIVE_REPARTITION)
                )
            )

            boost_deja_utilise = (
                boost > 0
            )

            bouton_boost_15.configure(
                state=(
                    "normal"
                    if (
                        not boost_deja_utilise
                        and (
                            mode_developpeur_actif()
                            or points_actuels >= COUT_BOOST_15
                        )
                    )
                    else "disabled"
                ),
                cursor=(
                    "hand2"
                    if (
                        not boost_deja_utilise
                        and (
                            mode_developpeur_actif()
                            or points_actuels >= COUT_BOOST_15
                        )
                    )
                    else "arrow"
                ),
                text=(
                    t(
                        "hc.boost15",
                        cost=(
                            t("hc.already_prioritized")
                            if boost_deja_utilise
                            else COUT_BOOST_15
                        )
                    )
                ),
                command=lambda:
                effectuer_boost(
                    15.0
                )
            )

            bouton_boost_30.configure(
                state=(
                    "normal"
                    if (
                        not boost_deja_utilise
                        and (
                            mode_developpeur_actif()
                            or points_actuels >= COUT_BOOST_30
                        )
                    )
                    else "disabled"
                ),
                cursor=(
                    "hand2"
                    if (
                        not boost_deja_utilise
                        and (
                            mode_developpeur_actif()
                            or points_actuels >= COUT_BOOST_30
                        )
                    )
                    else "arrow"
                ),
                text=(
                    t(
                        "hc.boost30",
                        cost=(
                            t("hc.already_prioritized")
                            if boost_deja_utilise
                            else COUT_BOOST_30
                        )
                    )
                ),
                command=lambda:
                effectuer_boost(
                    30.0
                )
            )

            petite = fourchette_livraison_urgente(
                avion,
                munition,
                "PETITE"
            )

            grande = fourchette_livraison_urgente(
                avion,
                munition,
                "GRANDE"
            )

            bouton_petite.configure(
                text=t(
                    "hc.delivery.button",
                    size=t("delivery.small"),
                    minimum=petite[0], maximum=petite[1],
                    cost=COUT_LIVRAISON_PETITE
                ),
                state=(
                    "normal"
                    if (
                        mode_developpeur_actif()
                        or points_actuels >= COUT_LIVRAISON_PETITE
                    )
                    else "disabled"
                ),
                cursor=(
                    "hand2"
                    if (
                        mode_developpeur_actif()
                        or points_actuels >= COUT_LIVRAISON_PETITE
                    )
                    else "arrow"
                ),
                command=lambda:
                effectuer_urgence(
                    "PETITE"
                )
            )

            bouton_grande.configure(
                text=t(
                    "hc.delivery.button",
                    size=t("delivery.large"),
                    minimum=grande[0], maximum=grande[1],
                    cost=COUT_LIVRAISON_GRANDE
                ),
                state=(
                    "normal"
                    if (
                        mode_developpeur_actif()
                        or points_actuels >= COUT_LIVRAISON_GRANDE
                    )
                    else "disabled"
                ),
                cursor=(
                    "hand2"
                    if (
                        mode_developpeur_actif()
                        or points_actuels >= COUT_LIVRAISON_GRANDE
                    )
                    else "arrow"
                ),
                command=lambda:
                effectuer_urgence(
                    "GRANDE"
                )
            )

        def selectionner_munition(
            munition
        ):
            selection.set(
                munition
            )

            for nom, bouton in boutons_munitions.items():
                bouton.configure(
                    bg=(
                        theme["bleu"]
                        if nom == munition
                        else theme["panneau_alt"]
                    ),
                    fg=(
                        theme["blanc"]
                        if nom == munition
                        else theme["texte"]
                    )
                )

            actualiser_actions()

        for munition in trier_munitions_logiquement(
            AVIONS_EMPORTS.get(
                avion,
                []
            )
        ):
            stock = lire_stock_unitaire(
                munition
            )

            boost = lire_boost_commandement(
                annee_cible,
                mois_cible,
                avion,
                munition
            )[
                "boost_pourcent"
            ]

            texte = (
                f"{t_munition(munition)}    •    {t('common.stock')} : {stock}"
                + (
                    f"    •    +{boost:.0f} %"
                    if boost > 0
                    else ""
                )
            )

            bouton = tk.Button(
                contenu,
                text=texte,
                font=(POLICE, 8, "bold"),
                anchor="w",
                bg=theme["panneau_alt"],
                fg=theme["texte"],
                activebackground=theme["bleu"],
                activeforeground=theme["blanc"],
                relief="solid",
                borderwidth=1,
                cursor="hand2",
                command=lambda m=munition:
                selectionner_munition(
                    m
                )
            )

            bouton.pack(
                fill="x",
                pady=2,
                ipady=7
            )

            boutons_munitions[
                munition
            ] = bouton

        lier_molette_recursivement(
            contenu,
            canvas
        )



    bouton_urgence.configure(
        command=ouvrir_demande_commandement
    )

    def basculer_visibilite_modificateurs():
        visibilite_modificateurs_active.set(
            not visibilite_modificateurs_active.get()
        )

        rafraichir()


    bouton_visibilite_modificateurs.configure(
        command=basculer_visibilite_modificateurs
    )


    # ========================================================
    # RAFRAICHISSEMENT
    # ========================================================

    def rafraichir():
        try:
            annee = int(
                variable_annee.get()
            )
        except Exception:
            annee = int(
                annee_initiale
            )

        mois = mois_numero()

        modele = cle_modele_repartition_actif()

        label_modele.configure(
            text=nom_affiche_modele_actif()
        )

        lignes = calculer_apercu_repartition_mensuelle(
            annee,
            mois,
            avion=avion,
            modele=modele
        )

        afficher_modificateurs = bool(
            visibilite_modificateurs_active.get()
        )

        # Comparaison visuelle uniquement.
        # OFF n'altère ni la DB, ni les boosts, ni les livraisons, ni le moteur réel.
        if not afficher_modificateurs:
            for ligne_apercu in lignes:
                ligne_apercu[
                    "pourcentage"
                ] = float(
                    ligne_apercu.get(
                        "pourcentage_base",
                        ligne_apercu.get(
                            "pourcentage",
                            0.0
                        )
                    )
                )

        bouton_visibilite_modificateurs.configure(
            text=(
                t("forecast.modifiers.on")
                if afficher_modificateurs
                else t("forecast.modifiers.off")
            ),
            bg=(
                COULEUR_OR_COMMANDEMENT
                if afficher_modificateurs
                else theme["champ"]
            ),
            fg=(
                theme["barre"]
                if afficher_modificateurs
                else theme["texte_faible"]
            )
        )

        boosts_mois_lignes = lister_boosts_commandement(
            annee,
            mois,
            avion
        )

        boosts_par_munition = (
            {
                ligne_boost[
                    "munition"
                ]: float(
                    ligne_boost[
                        "boost_pourcent"
                    ]
                )
                for ligne_boost in boosts_mois_lignes
            }
            if afficher_modificateurs
            else {}
        )

        # Livraisons urgentes EN TRANSIT appartenant au mois affiché.
        # Plusieurs livraisons de la même munition sont regroupées afin
        # d'afficher une seule plage claire dans la liste principale.
        livraisons_par_munition = {}

        livraisons_visuelles = (
            lister_livraisons_urgentes_en_transit()
            if afficher_modificateurs
            else []
        )

        for livraison in livraisons_visuelles:
            try:
                date_demande_livraison = datetime.strptime(
                    livraison[
                        "date_demande_jeu"
                    ],
                    "%Y.%m.%d %H:%M:%S"
                )
            except ValueError:
                continue

            if (
                date_demande_livraison.year,
                date_demande_livraison.month
            ) != (
                int(
                    annee
                ),
                int(
                    mois
                )
            ):
                continue

            nom_munition_livree = livraison[
                "munition"
            ]

            entree = livraisons_par_munition.setdefault(
                nom_munition_livree,
                {
                    "minimum": 0,
                    "maximum": 0,
                    "nombre": 0
                }
            )

            entree[
                "minimum"
            ] += int(
                livraison[
                    "quantite_min"
                ]
            )

            entree[
                "maximum"
            ] += int(
                livraison[
                    "quantite_max"
                ]
            )

            entree[
                "nombre"
            ] += 1

        for enfant in contenu_liste.winfo_children():
            enfant.destroy()

        couleurs_par_munition = {}
        compteurs = {
            "Bombes": 0,
            "Roquettes": 0,
            "Réservoirs": 0,
            "Napalm": 0,
            "Spécial": 0
        }

        for ligne in lignes:
            munition = ligne[
                "munition"
            ]

            categorie = categorie_affichage_munition(
                munition
            )

            index_couleur = compteurs.get(
                categorie,
                0
            )

            couleur = couleur_munition_stock(
                munition,
                index_couleur
            )

            compteurs[
                categorie
            ] = (
                index_couleur
                + 1
            )

            couleurs_par_munition[
                munition
            ] = couleur

        for ligne in lignes:
            munition = ligne[
                "munition"
            ]

            niveau = ligne[
                "niveau"
            ]

            pourcentage = ligne[
                "pourcentage"
            ]

            pourcentage_base = float(
                ligne.get(
                    "pourcentage_base",
                    pourcentage
                )
            )

            boost_munition = boosts_par_munition.get(
                munition,
                0.0
            )

            livraison_munition = livraisons_par_munition.get(
                munition
            )

            # Ligne responsive : la colonne centrale absorbe toute la largeur
            # disponible et la valeur reste toujours visible à droite.
            ligne_ui = tk.Frame(
                contenu_liste,
                bg=theme["panneau"]
            )
            ligne_ui.pack(fill="x", pady=2)
            ligne_ui.grid_columnconfigure(0, minsize=5)
            ligne_ui.grid_columnconfigure(1, weight=1)
            ligne_ui.grid_columnconfigure(2, weight=0, minsize=78)

            tk.Frame(
                ligne_ui,
                width=5,
                bg=couleurs_par_munition[munition]
            ).grid(row=0, column=0, rowspan=3, sticky="ns")

            tk.Label(
                ligne_ui,
                text=t_munition(munition),
                font=(POLICE, 8, "bold"),
                anchor="w",
                justify="left",
                bg=theme["panneau"],
                fg=theme["texte"]
            ).grid(row=0, column=1, sticky="ew", padx=(11, 6), pady=(5, 0))

            tk.Label(
                ligne_ui,
                text=f"{pourcentage:.1f} %",
                font=(POLICE, 11, "bold"),
                anchor="e",
                bg=theme["panneau"],
                fg=(
                    COULEUR_OR_COMMANDEMENT_ACTIF
                    if boost_munition > 0
                    else theme["texte"]
                )
            ).grid(row=0, column=2, sticky="e", padx=(4, 10), pady=(3, 0))

            tk.Label(
                ligne_ui,
                text=nom_affiche_niveau_repartition(niveau),
                font=(POLICE, 7, "bold"),
                anchor="w",
                bg=theme["panneau"],
                fg=theme["texte_faible"]
            ).grid(row=1, column=1, sticky="w", padx=(11, 6), pady=(0, 4))

            if boost_munition > 0:
                tk.Label(
                    ligne_ui,
                    text=t("forecast.base_share", value=f"{pourcentage_base:.1f}"),
                    font=(POLICE, 7, "bold"),
                    anchor="e",
                    bg=theme["panneau"],
                    fg=theme["texte_faible"]
                ).grid(row=1, column=2, sticky="e", padx=(4, 10), pady=(0, 4))

            textes_commandement_munition = []

            if boost_munition > 0:
                textes_commandement_munition.append(f"★  +{boost_munition:.0f} %")

            if livraison_munition is not None:
                plage_livraison = (
                    f"{livraison_munition['minimum']}"
                    f"–{livraison_munition['maximum']}"
                )
                if livraison_munition["nombre"] > 1:
                    texte_livraison = t(
                        "hc.delivery.in_progress.many",
                        count=livraison_munition["nombre"],
                        range=plage_livraison
                    )
                else:
                    texte_livraison = t(
                        "hc.delivery.in_progress.one",
                        range=plage_livraison
                    )
                textes_commandement_munition.append(texte_livraison)

            if textes_commandement_munition:
                tk.Label(
                    ligne_ui,
                    text="    ".join(textes_commandement_munition),
                    font=(POLICE, 7, "bold"),
                    anchor="w",
                    justify="left",
                    bg=theme["panneau"],
                    fg=COULEUR_OR_COMMANDEMENT_ACTIF
                ).grid(
                    row=2,
                    column=1,
                    columnspan=2,
                    sticky="ew",
                    padx=(11, 10),
                    pady=(0, 5)
                )

        valeurs = [
            ligne[
                "pourcentage"
            ]
            for ligne in lignes
            if ligne[
                "pourcentage"
            ] > 0
        ]

        couleurs = [
            couleurs_par_munition[
                ligne[
                    "munition"
                ]
            ]
            for ligne in lignes
            if ligne[
                "pourcentage"
            ] > 0
        ]

        canvas_donut.delete(
            "all"
        )

        canvas_donut.update_idletasks()
        largeur_donut = max(260, canvas_donut.winfo_width())
        hauteur_donut = max(260, canvas_donut.winfo_height())
        taille_donut = max(220, min(480, largeur_donut - 24, hauteur_donut - 24))
        centre_x = largeur_donut // 2
        centre_y = hauteur_donut // 2

        image = creer_donut_image_global(
            valeurs,
            couleurs,
            taille=taille_donut,
            trou=0.50
        )

        photo = ImageTk.PhotoImage(
            image
        )

        canvas_donut.photo_repartition = photo

        canvas_donut.create_image(
            centre_x,
            centre_y,
            image=photo,
            anchor="center"
        )

        actifs = sum(
            1
            for ligne in lignes
            if ligne[
                "pourcentage"
            ] > 0
        )

        canvas_donut.create_text(
            centre_x,
            centre_y - 22,
            text=str(
                actifs
            ),
            font=(POLICE, 23, "bold"),
            fill=theme["texte"]
        )

        canvas_donut.create_text(
            centre_x,
            centre_y + 18,
            text=t("forecast.donut"),
            font=(POLICE, 7, "bold"),
            fill=theme["texte_faible"]
        )

        periode = (
            f"{t_mois(mois)} {annee}"
        )

        label_periode_centre.configure(
            text=periode
        )

        label_info.configure(
            text=(
                f"{periode}  •  "
                + (
                    t("forecast.period_standard")
                    if modele == "STANDARD"
                    else t("forecast.period_custom")
                )
            )
        )

        points = obtenir_points_commandement()

        dev_actif = mode_developpeur_actif()

        label_points.configure(
            text=(
                t("hc.admin.short")
                if dev_actif
                else formater_points_commandement(
                    points
                )
            ),
            fg=(
                COULEUR_OR_COMMANDEMENT_ACTIF
                if not dev_actif
                else theme["vert"]
            )
        )

        label_gain_points.configure(
            text=texte_gain_points_journalier()
        )

        label_mode_admin.configure(
            text=(
                t("hc.admin")
                if dev_actif
                else ""
            )
        )

        livraisons_transit = (
            lister_livraisons_urgentes_en_transit()
            if afficher_modificateurs
            else []
        )

        periode_passee = periode_commandement_est_passee(
            annee,
            mois
        )

        bouton_urgence.configure(
            state=(
                "normal"
                if (
                    not periode_passee
                    and (
                        dev_actif
                        or points >= COUT_LIVRAISON_PETITE
                    )
                )
                else "disabled"
            ),
            cursor=(
                "hand2"
                if (
                    not periode_passee
                    and (
                        dev_actif
                        or points >= COUT_LIVRAISON_PETITE
                    )
                )
                else "arrow"
            )
        )

        boosts_mois = (
            lister_boosts_commandement(
                annee,
                mois,
                avion
            )
            if afficher_modificateurs
            else []
        )

        directive_affichee = description_directive_standard(
            annee,
            mois,
            avion
        )

        # ----------------------------------------------------
        # BANDEAU DIRECTIVE UNIQUE
        # ----------------------------------------------------
        if (
            modele == "STANDARD"
            and directive_affichee is not None
            and directive_affichee[
                "mode"
            ] == "CUSTOM"
        ):
            numero_directive = directive_affichee.get(
                "numero"
            )

            label_directive_active.configure(
                text=(
                    t("hc.directive.number", number=numero_directive)
                    if numero_directive is not None
                    else t("hc.directive.active")
                )
            )

            label_directive_active_periode.configure(
                text=t(
                    "hc.directive.since",
                    period=(
                        f"{t_mois(directive_affichee['mois_effet'])} "
                        f"{directive_affichee['annee_effet']}"
                    )
                )
            )

            if not cadre_directive_active.winfo_manager():
                cadre_directive_active.pack(
                    fill="x",
                    padx=10,
                    pady=(0, 8),
                    before=zone_liste
                )

        else:
            if cadre_directive_active.winfo_manager():
                cadre_directive_active.pack_forget()

        historique_commandement = (
            lister_historique_commandement_simplifie(
                annee,
                mois,
                avion,
                limite=7
            )
        )

        # ----------------------------------------------------
        # EXPLICATION FIXE DU HAUT COMMANDEMENT
        # ----------------------------------------------------
        # Cette zone explique le rôle du système. Les actions elles-mêmes
        # sont consignées dans l'historique juste en dessous.
        texte_explication_commandement = t("hc.explanation")

        label_transit.configure(
            text=texte_explication_commandement,
            fg=theme["texte"]
        )

        # ----------------------------------------------------
        # HISTORIQUE SIMPLIFIÉ DU HAUT COMMANDEMENT
        # ----------------------------------------------------
        texte_courant = str(
            label_transit.cget(
                "text"
            )
            or ""
        ).rstrip()

        bloc_historique = [
            "",
            "────────────────────────",
            t("hc.history.title")
        ]

        if historique_commandement:
            bloc_historique.extend(
                historique_commandement
            )
        else:
            bloc_historique.append(
                t("hc.history.none")
            )

        label_transit.configure(
            text=(
                texte_courant
                + "\n"
                + "\n".join(
                    bloc_historique
                )
            )
        )

        canvas_liste.configure(
            scrollregion=(
                canvas_liste.bbox(
                    "all"
                )
                or (
                    0,
                    0,
                    1,
                    1
                )
            )
        )


    spin_annee.configure(
        command=rafraichir
    )

    spin_mois.configure(
        command=rafraichir
    )

    spin_annee.bind(
        "<Return>",
        lambda event:
        rafraichir()
    )

    spin_annee.bind(
        "<FocusOut>",
        lambda event:
        rafraichir()
    )

    lier_molette_recursivement(
        contenu_liste,
        canvas_liste
    )

    # Une seconde synchronisation avant le tout premier rafraîchissement
    # garantit que les callbacks du Spinbox n'ont pas remis JANVIER.
    variable_annee.set(
        int(
            annee_initiale
        )
    )

    positionner_spinbox_mois(
        spin_mois,
        variable_mois,
        mois_initial
    )

    rafraichir()

    fenetre_repartition.update_idletasks()

    rehausser_contour_fenetre(
        fenetre_repartition
    )


def ouvrir_stock_base():
    _debut_performance_ui = time.perf_counter()
    global fenetre_stock_ouverte

    if (
        fenetre_stock_ouverte is not None
        and fenetre_stock_ouverte.winfo_exists()
    ):
        fenetre_stock_ouverte.lift()
        fenetre_stock_ouverte.focus_force()
        return


    fenetre_stock = tk.Toplevel(
        fenetre
    )

    fenetre_stock.after_idle(
        lambda debut=_debut_performance_ui:
        journaliser_performance_ui(
            'Stock base aérienne',
            debut
        )
    )

    fenetre_stock_ouverte = fenetre_stock


    def fermer_stock():
        global fenetre_stock_ouverte

        try:
            fenetre_stock.unbind_all(
                "<MouseWheel>"
            )
        except Exception:
            pass

        fenetre_stock_ouverte = None
        fenetre_stock.destroy()


    appliquer_chrome_custom(
        fenetre_stock,
        "",
        1480,
        840,
        fermer_stock
    )


    # ========================================================
    # ENTETE
    # ========================================================

    entete = tk.Frame(
        fenetre_stock,
        height=82,
        bg=theme["barre"]
    )

    entete.pack(
        fill="x"
    )

    entete.pack_propagate(
        False
    )


    tk.Label(
        entete,
        text=t("stock.window.title"),
        font=(POLICE, 20, "bold"),
        bg=theme["barre"],
        fg=theme["blanc"]
    ).pack(
        pady=(16, 2)
    )


    tk.Label(
        entete,
        text=t(
            "stock.window.subtitle",
            aircraft=avion_selectionne,
            qty=DONNEES_CARRIERE_IL2.get("ammo_qty", 0)
        ),
        font=(POLICE, 9, "bold"),
        bg=theme["barre"],
        fg=theme["blanc"]
    ).pack()


    zone_principale = tk.Frame(
        fenetre_stock,
        bg=theme["fond"]
    )

    zone_principale.pack(
        fill="both",
        expand=True,
        padx=16,
        pady=16
    )

    # Trois colonnes fluides : inventaire / capacité / répartition.
    zone_principale.grid_rowconfigure(0, weight=1)
    zone_principale.grid_columnconfigure(0, weight=34, minsize=300)
    zone_principale.grid_columnconfigure(1, weight=28, minsize=260)
    zone_principale.grid_columnconfigure(2, weight=38, minsize=320)


    # ========================================================
    # DONNEES DU STOCK
    # ========================================================

    emports_compatibles = trier_munitions_logiquement(
        AVIONS_EMPORTS.get(
            avion_selectionne,
            []
        )
    )

    stock_visible = [
        (nom, stock)
        for nom, stock in lire_stock(
            emports_compatibles
        )
        if stock > 0
    ]


    # ========================================================
    # COLONNE 1 — MUNITIONS DISPONIBLES
    # ========================================================

    panneau_inventaire = tk.Frame(
        zone_principale,
        bg=theme["panneau"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    panneau_inventaire.grid(
        row=0,
        column=0,
        sticky="nsew"
    )


    tk.Label(
        panneau_inventaire,
        text=t("stock.inventory.title"),
        font=(POLICE, 12, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(18, 4)
    )


    tk.Label(
        panneau_inventaire,
        text=t(
            "stock.inventory.subtitle",
            aircraft=avion_selectionne
        ),
        font=(POLICE, 8),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 14)
    )


    tk.Frame(
        panneau_inventaire,
        height=1,
        bg=theme["separateur"]
    ).pack(
        fill="x",
        padx=18
    )


    zone_inventaire = tk.Frame(
        panneau_inventaire,
        bg=theme["panneau"]
    )

    zone_inventaire.pack(
        fill="both",
        expand=True,
        padx=12,
        pady=(12, 14)
    )


    scroll_inventaire = tk.Scrollbar(
        zone_inventaire,
        orient="vertical"
    )

    scroll_inventaire.pack(
        side="right",
        fill="y"
    )


    canvas_inventaire = tk.Canvas(
        zone_inventaire,
        bg=theme["panneau"],
        highlightthickness=0,
        borderwidth=0,
        yscrollcommand=scroll_inventaire.set
    )

    canvas_inventaire.pack(
        side="left",
        fill="both",
        expand=True
    )


    scroll_inventaire.configure(
        command=canvas_inventaire.yview
    )


    contenu_inventaire = tk.Frame(
        canvas_inventaire,
        bg=theme["panneau"]
    )


    item_inventaire = canvas_inventaire.create_window(
        0,
        0,
        anchor="nw",
        window=contenu_inventaire
    )


    contenu_inventaire.bind(
        "<Configure>",
        lambda event:
        canvas_inventaire.configure(
            scrollregion=(
                canvas_inventaire.bbox(
                    "all"
                )
                or (0, 0, 1, 1)
            )
        )
    )


    canvas_inventaire.bind(
        "<Configure>",
        lambda event:
        canvas_inventaire.itemconfig(
            item_inventaire,
            width=event.width
        )
    )


    if not stock_visible:
        tk.Label(
            contenu_inventaire,
            text=t(
                "stock.inventory.none",
                aircraft=avion_selectionne
            ),
            font=(POLICE, 11, "bold"),
            justify="center",
            bg=theme["panneau"],
            fg=theme["texte_faible"]
        ).pack(
            fill="x",
            pady=150
        )


    index_categorie = {
        "Bombes": 0,
        "Roquettes": 0,
        "Réservoirs": 0,
        "Napalm": 0,
        "Spécial": 0
    }


    for nom, stock in stock_visible:
        categorie = categorie_affichage_munition(
            nom
        )

        couleur = couleur_munition_stock(
            nom,
            index_categorie[
                categorie
            ]
        )

        index_categorie[
            categorie
        ] += 1


        ligne = tk.Frame(
            contenu_inventaire,
            height=66,
            bg=theme["panneau"]
        )

        ligne.pack(
            fill="x",
            padx=3,
            pady=1
        )

        ligne.pack_propagate(
            False
        )


        # Marqueur de famille / nuance
        indicateur = tk.Frame(
            ligne,
            width=5,
            height=64,
            bg=couleur
        )

        indicateur.pack(
            side="left",
            fill="y"
        )


        zone_icone = tk.Frame(
            ligne,
            width=52,
            height=64,
            bg=theme["panneau"]
        )

        zone_icone.pack(
            side="left"
        )

        zone_icone.pack_propagate(
            False
        )


        photo = creer_icone_munition(
            nom,
            taille=38
        )


        label_icone = tk.Label(
            zone_icone,
            image=photo if photo else "",
            bg=theme["panneau"]
        )

        label_icone.image = photo

        label_icone.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )


        zone_texte = tk.Frame(
            ligne,
            bg=theme["panneau"]
        )

        zone_texte.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(4, 8)
        )


        tk.Label(
            zone_texte,
            text=t_munition(nom),
            font=(POLICE, 9, "bold"),
            anchor="w",
            justify="left",
            wraplength=285,
            bg=theme["panneau"],
            fg=theme["texte"]
        ).pack(
            anchor="w",
            pady=(9, 0)
        )


        tk.Label(
            zone_texte,
            text=t_categorie(categorie),
            font=(POLICE, 7),
            anchor="w",
            bg=theme["panneau"],
            fg=theme["texte_faible"]
        ).pack(
            anchor="w",
            pady=(2, 0)
        )


        tk.Label(
            ligne,
            text=str(stock),
            font=(POLICE, 13, "bold"),
            width=7,
            anchor="center",
            bg=theme["panneau_alt"],
            fg=theme["texte"]
        ).pack(
            side="right",
            padx=(5, 8),
            ipady=7
        )


        tk.Frame(
            contenu_inventaire,
            height=1,
            bg=theme["separateur"]
        ).pack(
            fill="x",
            padx=6
        )


    def defiler_inventaire(event):
        return defiler_canvas_avec_molette(
            canvas_inventaire,
            event
        )


    canvas_inventaire.bind(
        "<Enter>",
        lambda event:
        fenetre_stock.bind_all(
            "<MouseWheel>",
            defiler_inventaire
        )
    )

    canvas_inventaire.bind(
        "<Leave>",
        lambda event:
        fenetre_stock.unbind_all(
            "<MouseWheel>"
        )
    )

    contenu_inventaire.bind(
        "<Enter>",
        lambda event:
        fenetre_stock.bind_all(
            "<MouseWheel>",
            defiler_inventaire
        )
    )

    contenu_inventaire.bind(
        "<Leave>",
        lambda event:
        fenetre_stock.unbind_all(
            "<MouseWheel>"
        )
    )


    lier_molette_recursivement(
        contenu_inventaire,
        canvas_inventaire
    )


    # ========================================================
    # DONNEES NIVEAU DE STOCK IL-2
    # ========================================================
    #
    # Le donut central ne représente plus la capacité fictive de 7500.
    #
    # 100 % = plus haute valeur ammoQty jamais observée
    #         pour cette carrière.
    #
    # Exemple :
    # référence = 1680
    # actuel     = 840
    # => 50 % restant.
    # ========================================================

    stock_il2_actuel = max(
        0,
        int(
            DONNEES_CARRIERE_IL2.get(
                "ammo_qty",
                0
            )
        )
    )

    reference_stock_il2 = max(
        1,
        int(
            lire_reference_capacite_carriere(
                DONNEES_CARRIERE_IL2
            )
        )
    )

    # Sécurité : une valeur supérieure au maximum connu devient
    # immédiatement la nouvelle référence.
    if stock_il2_actuel > reference_stock_il2:
        reference_stock_il2 = (
            mettre_a_jour_reference_capacite_carriere(
                DONNEES_CARRIERE_IL2
            )
        )

    stock_il2_consomme = max(
        0,
        reference_stock_il2
        - stock_il2_actuel
    )


    # ========================================================
    # OUTIL : DONUT PILLOW ANTIALIASE
    # ========================================================

    def creer_donut_image(
        valeurs,
        couleurs,
        taille=300,
        trou=0.48
    ):
        cle_cache = (
            "stock_base",
            tuple(round(float(v), 6) for v in valeurs),
            tuple(str(c) for c in couleurs),
            int(taille),
            round(float(trou), 4),
            theme["panneau"],
            theme["bordure"],
        )
        image_cachee = _CACHE_DONUTS_PIL.get(cle_cache)
        if image_cachee is not None:
            return image_cachee.copy()

        facteur = 4
        taille_hd = (
            taille
            * facteur
        )

        marge = (
            10
            * facteur
        )

        image_hd = Image.new(
            "RGBA",
            (
                taille_hd,
                taille_hd
            ),
            (
                0,
                0,
                0,
                0
            )
        )

        dessin = ImageDraw.Draw(
            image_hd
        )

        boite = (
            marge,
            marge,
            taille_hd - marge,
            taille_hd - marge
        )

        total = sum(
            max(
                0.0,
                float(v)
            )
            for v in valeurs
        )

        if total <= 0:
            total = 1.0

        angle = -90.0


        for valeur, couleur in zip(
            valeurs,
            couleurs
        ):
            valeur = max(
                0.0,
                float(valeur)
            )

            if valeur <= 0:
                continue

            etendue = (
                360.0
                * valeur
                / total
            )

            dessin.pieslice(
                boite,
                start=angle,
                end=angle + etendue,
                fill=couleur
            )

            angle += etendue


        centre = (
            taille_hd // 2
        )

        rayon_exterieur = (
            taille_hd // 2
            - marge
        )

        rayon_interieur = int(
            rayon_exterieur
            * trou
        )


        dessin.ellipse(
            (
                centre - rayon_interieur,
                centre - rayon_interieur,
                centre + rayon_interieur,
                centre + rayon_interieur
            ),
            fill=theme["panneau"]
        )


        dessin.ellipse(
            boite,
            outline=theme["bordure"],
            width=4
        )


        dessin.ellipse(
            (
                centre - rayon_interieur,
                centre - rayon_interieur,
                centre + rayon_interieur,
                centre + rayon_interieur
            ),
            outline=theme["bordure"],
            width=4
        )


        image_finale = image_hd.resize(
            (
                taille,
                taille
            ),
            Image.Resampling.LANCZOS
        )
        _CACHE_DONUTS_PIL[cle_cache] = image_finale.copy()
        return image_finale


    # ========================================================
    # COLONNE 2 — CAPACITE DU DEPOT
    # ========================================================

    panneau_capacite = tk.Frame(
        zone_principale,
        bg=theme["panneau"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    panneau_capacite.grid(
        row=0,
        column=1,
        sticky="nsew",
        padx=12
    )


    tk.Label(
        panneau_capacite,
        text=t("stock.capacity.title"),
        font=(POLICE, 12, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(18, 4)
    )


    tk.Label(
        panneau_capacite,
        text=t("stock.capacity.subtitle"),
        font=(POLICE, 8),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 14)
    )


    tk.Frame(
        panneau_capacite,
        height=1,
        bg=theme["separateur"]
    ).pack(
        fill="x",
        padx=18
    )


    canvas_capacite = tk.Canvas(
        panneau_capacite,
        width=330,
        height=330,
        bg=theme["panneau"],
        highlightthickness=0
    )

    canvas_capacite.pack(
        pady=(24, 0)
    )


    image_capacite = creer_donut_image(
        [
            stock_il2_actuel,
            stock_il2_consomme
        ],
        [
            theme["bleu"],
            theme["champ"]
        ],
        taille=300,
        trou=0.55
    )


    photo_capacite = ImageTk.PhotoImage(
        image_capacite
    )

    canvas_capacite.image_capacite = (
        photo_capacite
    )


    canvas_capacite.create_image(
        165,
        165,
        image=photo_capacite,
        anchor="center"
    )


    taux = min(
        100.0,
        (
            stock_il2_actuel
            / reference_stock_il2
            * 100.0
        )
    )


    canvas_capacite.create_text(
        165,
        145,
        text=f"{taux:.0f} %",
        font=(POLICE, 24, "bold"),
        fill=theme["texte"]
    )


    canvas_capacite.create_text(
        165,
        178,
        text=t("stock.capacity.remaining"),
        font=(POLICE, 8, "bold"),
        fill=theme["texte_faible"]
    )


    tk.Label(
        panneau_capacite,
        text=t(
            "stock.capacity.units",
            current=stock_il2_actuel,
            reference=reference_stock_il2
        ),
        font=(POLICE, 11, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(0, 20)
    )


    zone_capacite_detail = tk.Frame(
        panneau_capacite,
        bg=theme["panneau"]
    )

    zone_capacite_detail.pack(
        fill="x",
        padx=42
    )


    for titre, valeur, couleur in (
        (
            t("stock.capacity.legend.remaining"),
            stock_il2_actuel,
            theme["bleu"]
        ),
        (
            t("stock.capacity.legend.consumed"),
            stock_il2_consomme,
            theme["texte_faible"]
        )
    ):
        ligne = tk.Frame(
            zone_capacite_detail,
            bg=theme["panneau"]
        )

        ligne.pack(
            fill="x",
            pady=5
        )


        tk.Frame(
            ligne,
            width=10,
            height=10,
            bg=couleur
        ).pack(
            side="left",
            padx=(0, 8)
        )


        tk.Label(
            ligne,
            text=titre,
            font=(POLICE, 8, "bold"),
            bg=theme["panneau"],
            fg=theme["texte_faible"]
        ).pack(
            side="left"
        )


        tk.Label(
            ligne,
            text=f"{valeur:.0f}",
            font=(POLICE, 9, "bold"),
            bg=theme["panneau"],
            fg=theme["texte"]
        ).pack(
            side="right"
        )


    # ========================================================
    # COLONNE 3 — REPARTITION DU STOCK
    # ========================================================

    panneau_repartition = tk.Frame(
        zone_principale,
        bg=theme["panneau"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    panneau_repartition.grid(
        row=0,
        column=2,
        sticky="nsew"
    )


    tk.Label(
        panneau_repartition,
        text=t("stock.distribution.title"),
        font=(POLICE, 12, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(18, 4)
    )


    tk.Label(
        panneau_repartition,
        text=t("stock.distribution.subtitle"),
        font=(POLICE, 8),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 14)
    )


    tk.Frame(
        panneau_repartition,
        height=1,
        bg=theme["separateur"]
    ).pack(
        fill="x",
        padx=18
    )


    # ========================================================
    # CONTROLES DU MODELE DE REPARTITION
    # ========================================================

    zone_modele = tk.Frame(
        panneau_repartition,
        height=46,
        bg=theme["panneau"]
    )

    zone_modele.pack(
        fill="x",
        padx=18,
        pady=(12, 0)
    )

    zone_modele.pack_propagate(
        False
    )


    mode_actuel = mode_repartition_actif()

    texte_mode_actuel = nom_affiche_modele_actif()


    bouton_mode_repartition = tk.Button(
        zone_modele,
        text=texte_mode_actuel,
        font=(POLICE, 8, "bold"),
        bg=theme["champ"],
        fg=theme["texte"],
        activebackground=theme["panneau_alt"],
        activeforeground=theme["texte"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    )

    bouton_mode_repartition._profil_repartition_actif = (
        cle_modele_repartition_actif()
    )

    def selection_modele_stock(
        modele_selectionne
    ):
        bouton_mode_repartition._profil_repartition_actif = (
            modele_selectionne
        )

        bouton_mode_repartition.configure(
            text=nom_affiche_modele_actif()
        )


    bouton_mode_repartition.configure(
        command=lambda:
        ouvrir_menu_profils_repartition(
            bouton_mode_repartition,
            selection_modele_stock
        )
    )

    bouton_mode_repartition.pack(
        side="left",
        fill="y",
        ipadx=8
    )


    def confirmer_ouverture_editeur_modele_repartition():
        popup = tk.Toplevel(
            fenetre
        )

        appliquer_chrome_custom(
            popup,
            t("stock.model_warning.window"),
            760,
            560,
            popup.destroy
        )

        popup.transient(
            fenetre
        )

        popup.grab_set()

        fond = tk.Frame(
            popup,
            bg=theme["panneau"]
        )

        fond.pack(
            fill="both",
            expand=True
        )

        tk.Label(
            fond,
            text=t("stock.model_warning.title"),
            font=(POLICE, 15, "bold"),
            bg=theme["panneau"],
            fg=theme["texte"]
        ).pack(
            pady=(30, 8)
        )

        tk.Label(
            fond,
            text=t("stock.model_warning.intro"),
            font=(POLICE, 9),
            justify="center",
            wraplength=650,
            bg=theme["panneau"],
            fg=theme["texte"]
        ).pack(
            padx=40,
            pady=(8, 14)
        )

        cadre_standard = tk.Frame(
            fond,
            bg=theme["panneau_alt"],
            highlightbackground=theme["bordure"],
            highlightthickness=1
        )

        cadre_standard.pack(
            fill="x",
            padx=55,
            pady=(0, 16)
        )

        tk.Label(
            cadre_standard,
            text=t("stock.model_warning.standard_title"),
            font=(POLICE, 10, "bold"),
            bg=theme["panneau_alt"],
            fg=theme["bleu"]
        ).pack(
            pady=(14, 6)
        )

        tk.Label(
            cadre_standard,
            text=t("stock.model_warning.standard_body"),
            font=(POLICE, 9),
            justify="center",
            wraplength=610,
            bg=theme["panneau_alt"],
            fg=theme["texte"]
        ).pack(
            padx=24,
            pady=(0, 16)
        )

        tk.Label(
            fond,
            text=t("stock.model_warning.custom_body"),
            font=(POLICE, 9),
            justify="center",
            wraplength=650,
            bg=theme["panneau"],
            fg=theme["texte"]
        ).pack(
            padx=40,
            pady=(0, 18)
        )

        def ouvrir_apres_confirmation():
            try:
                popup.grab_release()
            except Exception:
                pass

            popup.destroy()

            ouvrir_editeur_modele_repartition()

        bouton_compris = tk.Button(
            fond,
            text=t("stock.model_warning.open"),
            command=ouvrir_apres_confirmation,
            font=(POLICE, 10, "bold"),
            bg=theme["rouge"],
            fg=theme["blanc"],
            activebackground=theme["rouge"],
            activeforeground=theme["blanc"],
            relief="solid",
            borderwidth=1,
            cursor="hand2"
        )

        bouton_compris.pack(
            padx=70,
            pady=(4, 28),
            fill="x",
            ipady=10
        )

        popup.protocol(
            "WM_DELETE_WINDOW",
            popup.destroy
        )

        popup.lift()
        popup.focus_force()




    bouton_modifier_repartition = tk.Button(
        zone_modele,
        text=t("stock.distribution.edit"),
        command=confirmer_ouverture_editeur_modele_repartition,
        font=(POLICE, 8, "bold"),
        bg=theme["rouge"],
        fg=theme["blanc"],
        activebackground=theme["rouge"],
        activeforeground=theme["blanc"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    )

    bouton_modifier_repartition.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(10, 0)
    )


    # Toutes les munitions globales disponibles sur la base.
    stock_global_disponible = [
        (nom, stock)
        for nom, stock in lire_stock(
            list(MUNITIONS.keys())
        )
        if stock > 0
    ]


    # Trie : Bombes -> Roquettes -> Réservoirs -> Spécial
    ordre_categories = {
        "Roquettes": 0,
        "Bombes": 1,
        "Réservoirs": 2,
        "Napalm": 3,
        "Spécial": 4
    }


    stock_global_disponible.sort(
        key=lambda element: (
            ordre_categories[
                categorie_affichage_munition(
                    element[0]
                )
            ],
            element[0].lower()
        )
    )


    valeurs_repartition = []
    couleurs_repartition = []
    donnees_legende = []


    compteurs_couleurs = {
        "Bombes": 0,
        "Roquettes": 0,
        "Réservoirs": 0,
        "Napalm": 0,
        "Spécial": 0
    }


    for nom, stock in stock_global_disponible:
        categorie = categorie_affichage_munition(
            nom
        )

        index = compteurs_couleurs[
            categorie
        ]

        couleur = couleur_munition_stock(
            nom,
            index
        )

        compteurs_couleurs[
            categorie
        ] += 1


        # On représente la part réelle de capacité occupée,
        # pas seulement le nombre brut d'objets.
        valeur_logistique = (
            float(stock)
            * cout_logistique(
                nom
            )
        )


        valeurs_repartition.append(
            valeur_logistique
        )

        couleurs_repartition.append(
            couleur
        )

        donnees_legende.append(
            (
                nom,
                stock,
                categorie,
                couleur,
                valeur_logistique
            )
        )


    canvas_repartition = tk.Canvas(
        panneau_repartition,
        width=340,
        height=340,
        bg=theme["panneau"],
        highlightthickness=0
    )

    canvas_repartition.pack(
        pady=(12, 0)
    )


    image_repartition = creer_donut_image(
        valeurs_repartition,
        couleurs_repartition,
        taille=310,
        trou=0.50
    )


    photo_repartition = ImageTk.PhotoImage(
        image_repartition
    )

    canvas_repartition.image_repartition = (
        photo_repartition
    )


    canvas_repartition.create_image(
        170,
        170,
        image=photo_repartition,
        anchor="center"
    )


    canvas_repartition.create_text(
        170,
        152,
        text=str(
            len(
                stock_global_disponible
            )
        ),
        font=(POLICE, 22, "bold"),
        fill=theme["texte"]
    )


    canvas_repartition.create_text(
        170,
        183,
        text=t("stock.distribution.count"),
        font=(POLICE, 8, "bold"),
        fill=theme["texte_faible"]
    )


    # ========================================================
    # ACCES A LA CONSULTATION DETAILLEE
    # ========================================================

    zone_consultation = tk.Frame(
        panneau_repartition,
        bg=theme["panneau"]
    )

    zone_consultation.pack(
        fill="x",
        padx=24,
        pady=(18, 22)
    )

    tk.Label(
        zone_consultation,
        text=t("stock.distribution.hint"),
        font=(POLICE, 7),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 8)
    )

    bouton_consulter_repartition = tk.Button(
        zone_consultation,
        text=t("stock.distribution.view"),
        command=ouvrir_consultation_repartition_stock,
        font=(POLICE, 9, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte"],
        activebackground=theme["bleu"],
        activeforeground=theme["blanc"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    )

    bouton_consulter_repartition.pack(
        fill="x",
        ipady=10
    )


    fenetre_stock.update_idletasks()

    rehausser_contour_fenetre(
        fenetre_stock
    )


bouton_consulter_stock = tk.Button(
    cadre_stock,
    text=t("main.stock.view"),
    command=ouvrir_stock_base,
    font=(POLICE, 12, "bold"),
    bg=theme["panneau_alt"],
    fg=theme["texte"],
    activebackground=theme["champ"],
    activeforeground=theme["texte"],
    relief="solid",
    borderwidth=1,
    cursor="hand2"
)

bouton_consulter_stock.place(
    x=80,
    y=185,
    width=230,
    height=58
)

widgets_panneau_alt.append(
    bouton_consulter_stock
)


bouton_rapports = tk.Button(
    cadre_stock,
    text=t("main.stock.report"),
    command=ouvrir_rapports_carriere,
    font=(POLICE, 10, "bold"),
    bg=theme["panneau_alt"],
    fg=theme["texte"],
    activebackground=theme["champ"],
    activeforeground=theme["texte"],
    relief="solid",
    borderwidth=1,
    cursor="hand2"
)

bouton_rapports.place(
    x=80,
    y=255,
    width=178,
    height=48
)

widgets_panneau_alt.append(
    bouton_rapports
)


label_badge_rapports = tk.Label(
    cadre_stock,
    text="0",
    font=(POLICE, 12, "bold"),
    relief="solid",
    borderwidth=1,
    bg=theme["panneau_alt"],
    fg=theme["texte_faible"]
)

label_badge_rapports.place(
    x=270,
    y=255,
    width=40,
    height=48
)


# ============================================================
# PANNEAU CENTRAL / PREPARATION
# ============================================================

cadre_central = tk.Frame(
    fenetre,
    highlightthickness=1
)

cadre_central.place(
    x=430,
    y=130,
    width=740,
    height=685
)

widgets_panneau.append(cadre_central)
widgets_bordure.append(cadre_central)


label_preparation = tk.Label(
    cadre_central,
    text=t("main.mission.title"),
    font=POLICE_SECTION
)

label_preparation.place(
    x=0,
    y=18,
    width=740
)

widgets_panneau.append(label_preparation)


creer_separateur(
    cadre_central
).place(
    x=25,
    y=52,
    width=690
)


# ============================================================
# DATE / HEURE / NOMBRE D'APPAREILS
# ============================================================

label_date = tk.Label(
    cadre_central,
    text=t("main.mission.career_date"),
    font=POLICE_PETIT
)

label_date.place(
    x=30,
    y=75
)

widgets_texte_faible.append(label_date)


date_preparation_initiale, heure_preparation_initiale = (
    charger_preparation_mission()
)


variable_date_carriere = tk.StringVar(
    value=date_preparation_initiale
)


champ_date = tk.Entry(
    cadre_central,
    textvariable=variable_date_carriere,
    font=(POLICE, 12, "bold"),
    justify="center",
    relief="solid",
    borderwidth=1,
    state="readonly",
    readonlybackground=theme["panneau_alt"],
    fg=theme["texte"],
    takefocus=False,
    cursor="arrow"
)

champ_date.place(
    x=30,
    y=100,
    width=150,
    height=36
)

widgets_champ.append(champ_date)


label_heure = tk.Label(
    cadre_central,
    text=t("main.mission.time"),
    font=POLICE_PETIT
)

label_heure.place(
    x=215,
    y=75
)

widgets_texte_faible.append(label_heure)


champ_heure = tk.Entry(
    cadre_central,
    font=(POLICE, 12, "bold"),
    justify="center",
    relief="solid",
    borderwidth=1
)

champ_heure.place(
    x=215,
    y=100,
    width=88,
    height=36
)

champ_heure.insert(
    0,
    heure_preparation_initiale
)

widgets_champ.append(champ_heure)


def sauvegarder_heure_depuis_champ(
    event=None
):
    try:
        heure_valide = datetime.strptime(
            champ_heure.get().strip(),
            "%H:%M"
        )

        texte = heure_valide.strftime(
            "%H:%M"
        )

        champ_heure.delete(
            0,
            "end"
        )

        champ_heure.insert(
            0,
            texte
        )

        sauvegarder_preparation_mission(
            heure_texte=texte
        )

    except ValueError:
        pass


def incrementer_heure_preparation(
    delta_heures
):
    """
    +/- 1 heure.

    Le passage 23:xx -> 00:xx ou 00:xx -> 23:xx
    ne modifie JAMAIS la date de mission.
    """
    try:
        heure_courante = datetime.strptime(
            champ_heure.get().strip(),
            "%H:%M"
        )

    except ValueError:
        heure_courante = datetime.strptime(
            charger_preparation_mission()[1],
            "%H:%M"
        )

    nouvelle_heure = (
        heure_courante
        + timedelta(
            hours=int(
                delta_heures
            )
        )
    )

    texte = nouvelle_heure.strftime(
        "%H:%M"
    )

    champ_heure.delete(
        0,
        "end"
    )

    champ_heure.insert(
        0,
        texte
    )

    sauvegarder_preparation_mission(
        heure_texte=texte
    )


bouton_heure_plus = tk.Button(
    cadre_central,
    text="▲",
    command=lambda:
    incrementer_heure_preparation(
        1
    ),
    font=(POLICE, 6, "bold"),
    relief="solid",
    borderwidth=1,
    cursor="hand2"
)

bouton_heure_plus.place(
    x=303,
    y=100,
    width=22,
    height=18
)

widgets_bouton.append(
    bouton_heure_plus
)


bouton_heure_moins = tk.Button(
    cadre_central,
    text="▼",
    command=lambda:
    incrementer_heure_preparation(
        -1
    ),
    font=(POLICE, 6, "bold"),
    relief="solid",
    borderwidth=1,
    cursor="hand2"
)

bouton_heure_moins.place(
    x=303,
    y=118,
    width=22,
    height=18
)

widgets_bouton.append(
    bouton_heure_moins
)


champ_heure.bind(
    "<FocusOut>",
    sauvegarder_heure_depuis_champ
)

champ_heure.bind(
    "<Return>",
    sauvegarder_heure_depuis_champ
)


label_appareils = tk.Label(
    cadre_central,
    text=t("main.mission.aircraft_count"),
    font=POLICE_PETIT
)

label_appareils.place(
    x=400,
    y=75
)

widgets_texte_faible.append(label_appareils)


champ_nombre_avions = tk.Entry(
    cadre_central,
    font=(POLICE, 15, "bold"),
    justify="center",
    relief="solid",
    borderwidth=1,
    highlightthickness=0
)

champ_nombre_avions.place(
    x=400,
    y=100,
    width=100,
    height=36
)

champ_nombre_avions.insert(
    0,
    "1"
)

widgets_champ.append(
    champ_nombre_avions
)


creer_separateur(
    cadre_central
).place(
    x=25,
    y=160,
    width=690
)


# ============================================================
# PRESETS
# ============================================================

label_preset = tk.Label(
    cadre_central,
    text=t("main.mission.preset"),
    font=POLICE_SECTION
)

label_preset.place(
    x=30,
    y=178
)

widgets_panneau.append(label_preset)


preset_nom_var = tk.StringVar(
    value=t("main.mission.no_preset")
)


bouton_preset = tk.Button(
    cadre_central,
    textvariable=preset_nom_var,
    command=lambda: ouvrir_selecteur_preset(),
    font=(POLICE, 10, "bold"),
    anchor="w",
    padx=12,
    relief="solid",
    borderwidth=1,
    cursor="hand2"
)

bouton_preset.place(
    x=145,
    y=169,
    width=270,
    height=38
)

widgets_panneau_alt.append(
    bouton_preset
)


bouton_charger_preset = tk.Button(
    cadre_central,
    text=t("main.mission.load"),
    command=lambda: charger_preset_selectionne(),
    font=(POLICE, 9, "bold"),
    relief="solid",
    borderwidth=1,
    cursor="hand2"
)

bouton_charger_preset.place(
    x=425,
    y=169,
    width=82,
    height=38
)

widgets_bouton.append(
    bouton_charger_preset
)


bouton_sauver_preset = tk.Button(
    cadre_central,
    text=t("main.mission.save"),
    command=lambda: sauvegarder_preset_actuel(),
    font=(POLICE, 9, "bold"),
    relief="solid",
    borderwidth=1,
    cursor="hand2"
)

bouton_sauver_preset.place(
    x=515,
    y=169,
    width=82,
    height=38
)

widgets_bouton.append(
    bouton_sauver_preset
)


bouton_supprimer_preset = tk.Button(
    cadre_central,
    text=t("main.mission.delete_short"),
    command=lambda: supprimer_preset_selectionne(),
    font=(POLICE, 9, "bold"),
    relief="solid",
    borderwidth=1,
    cursor="hand2"
)

bouton_supprimer_preset.place(
    x=605,
    y=169,
    width=82,
    height=38
)

widgets_bouton.append(
    bouton_supprimer_preset
)


creer_separateur(
    cadre_central
).place(
    x=25,
    y=224,
    width=690
)


# ============================================================
# EMPORT SELECTIONNE
# ============================================================

label_armement = tk.Label(
    cadre_central,
    text=t("main.mission.selected_loadout"),
    font=POLICE_SECTION
)

label_armement.place(
    x=30,
    y=242
)

widgets_panneau.append(label_armement)


label_par_avion = tk.Label(
    cadre_central,
    text=t("main.mission.per_aircraft"),
    font=POLICE_PETIT
)

label_par_avion.place(
    x=490,
    y=245,
    width=85
)

widgets_texte_faible.append(
    label_par_avion
)


label_total_titre = tk.Label(
    cadre_central,
    text=t("main.mission.total"),
    font=POLICE_PETIT
)

label_total_titre.place(
    x=590,
    y=245,
    width=65
)

widgets_texte_faible.append(
    label_total_titre
)


bouton_ajouter_emport = tk.Button(
    cadre_central,
    text="+",
    command=lambda: ouvrir_ajout_emport(),
    font=(POLICE, 18, "bold"),
    relief="solid",
    borderwidth=1,
    cursor="hand2"
)

bouton_ajouter_emport.place(
    x=225,
    y=235,
    width=42,
    height=36
)

widgets_bouton.append(
    bouton_ajouter_emport
)


canvas_emport = tk.Canvas(
    cadre_central,
    highlightthickness=0,
    borderwidth=0
)

canvas_emport.place(
    x=25,
    y=282,
    width=675,
    height=270
)


scroll_emport = tk.Scrollbar(
    cadre_central,
    orient="vertical",
    command=canvas_emport.yview
)

scroll_emport.place(
    x=702,
    y=282,
    width=14,
    height=270
)


canvas_emport.configure(
    yscrollcommand=scroll_emport.set
)


contenu_emport = tk.Frame(
    canvas_emport
)

item_contenu_emport = (
    canvas_emport.create_window(
        0,
        0,
        anchor="nw",
        window=contenu_emport
    )
)


def ajuster_emport_scroll(event=None):
    zone = canvas_emport.bbox("all")

    if zone is None:
        zone = (0, 0, 1, 1)

    canvas_emport.configure(
        scrollregion=zone
    )


def ajuster_emport_largeur(event):
    canvas_emport.itemconfig(
        item_contenu_emport,
        width=event.width
    )


contenu_emport.bind(
    "<Configure>",
    ajuster_emport_scroll
)

canvas_emport.bind(
    "<Configure>",
    ajuster_emport_largeur
)


canvas_emport.bind(
    "<MouseWheel>",
    lambda event:
    defiler_canvas_avec_molette(
        canvas_emport,
        event
    )
)


champs_munitions = {}
labels_totaux = {}
emports_selectionnes = {}


# ============================================================
# MESSAGE / VALIDATION
# ============================================================

label_message = tk.Label(
    cadre_central,
    text="",
    font=POLICE_PETIT
)

label_message.place(
    x=30,
    y=568,
    width=680
)

widgets_panneau.append(label_message)


bouton_valider = tk.Button(
    cadre_central,
    text=t("main.mission.validate"),
    command=lambda: valider_mission(),
    font=(POLICE, 10, "bold"),
    relief="solid",
    borderwidth=1,
    cursor="hand2"
)

bouton_valider.place(
    x=250,
    y=610,
    width=240,
    height=44
)

widgets_bouton.append(
    bouton_valider
)


# ============================================================
# HISTORIQUE
# ============================================================

cadre_droite = tk.Frame(
    fenetre,
    highlightthickness=1
)

cadre_droite.place(
    x=1185,
    y=130,
    width=390,
    height=685
)

widgets_panneau.append(cadre_droite)
widgets_bordure.append(cadre_droite)


label_historique = tk.Label(
    cadre_droite,
    text=t("main.history.title"),
    font=POLICE_SECTION
)

label_historique.place(
    x=0,
    y=18,
    width=390
)

widgets_panneau.append(label_historique)


creer_separateur(
    cadre_droite
).place(
    x=20,
    y=52,
    width=350
)


scroll_historique = tk.Scrollbar(
    cadre_droite
)

scroll_historique.place(
    x=365,
    y=70,
    width=14,
    height=520
)


canvas_historique = tk.Canvas(
    cadre_droite,
    highlightthickness=0,
    yscrollcommand=scroll_historique.set
)

canvas_historique.place(
    x=20,
    y=70,
    width=340,
    height=520
)


scroll_historique.configure(
    command=canvas_historique.yview
)


def defiler_historique(event):
    canvas_historique.yview_scroll(
        int(-event.delta / 120),
        "units"
    )


canvas_historique.bind(
    "<MouseWheel>",
    defiler_historique
)


def traduire_armement_historique_pour_affichage(armement):
    morceaux_traduits = []

    for morceau in str(armement or "").split(" | "):
        correspondance = re.match(r"^\s*(\d+)x\s+(.+?)\s*$", morceau)

        if correspondance:
            morceaux_traduits.append(
                f"{correspondance.group(1)}x {t_munition(correspondance.group(2))}"
            )
        else:
            morceaux_traduits.append(morceau)

    return " | ".join(morceaux_traduits)


def afficher_historique():
    canvas_historique.delete("all")

    missions = charger_missions()

    if not missions:
        canvas_historique.create_text(
            10,
            15,
            text=t("main.history.none"),
            anchor="nw",
            font=POLICE_PETIT,
            fill=theme["texte_faible"]
        )

        canvas_historique.configure(
            scrollregion=(0, 0, 340, 520)
        )

        return

    y = 10

    for mission in missions:
        date_heure = mission[1]
        avion_mission = mission[2]
        nombre_avions = mission[3]
        armement = mission[4]

        canvas_historique.create_text(
            5,
            y,
            text=date_heure,
            anchor="nw",
            font=(POLICE, 9, "bold"),
            fill=theme["texte"]
        )

        canvas_historique.create_text(
            5,
            y + 22,
            text=f"{nombre_avions} × {avion_mission}",
            anchor="nw",
            font=POLICE_PETIT,
            fill=theme["texte_faible"]
        )

        canvas_historique.create_text(
            5,
            y + 43,
            text=traduire_armement_historique_pour_affichage(armement),
            anchor="nw",
            width=310,
            font=(POLICE, 8),
            fill=theme["texte"]
        )

        canvas_historique.create_line(
            5,
            y + 92,
            320,
            y + 92,
            fill=theme["separateur"]
        )

        y += 108

    canvas_historique.configure(
        scrollregion=(0, 0, 315, y + 20)
    )

    canvas_historique.yview_moveto(0)


def effacer_historique():
    if not dialogue_message_custom(
        t("main.history.clear_title"),
        t("main.history.clear_confirm"),
        "question",
        fenetre
    ):
        return

    connexion = sqlite3.connect(FICHIER_BASE)
    curseur = connexion.cursor()

    curseur.execute(
        "DELETE FROM missions"
    )

    connexion.commit()
    connexion.close()

    afficher_historique()


bouton_effacer = bouton_style(
    cadre_droite,
    t("main.history.clear"),
    effacer_historique
)

bouton_effacer.place(
    x=115,
    y=620,
    width=160,
    height=34
)


# ============================================================
# BARRE BASSE
# ============================================================

barre_bas = tk.Frame(fenetre)

barre_bas.place(
    x=0,
    y=HAUTEUR_FENETRE - HAUTEUR_BARRE_BAS,
    width=LARGEUR_FENETRE,
    height=HAUTEUR_BARRE_BAS
)

widgets_barre.append(barre_bas)


label_version = tk.Label(
    barre_bas,
    text=VERSION_APPLICATION,
    font=(POLICE, 8)
)

label_version.place(
    x=20,
    y=22
)

widgets_barre.append(label_version)


# ============================================================
# EMPORT SELECTIONNE / PRESETS / VALIDATION
# ============================================================

def vider_frame(frame):
    for enfant in frame.winfo_children():
        enfant.destroy()


def lire_quantites_emport():
    resultat = {}

    for nom, champ in champs_munitions.items():
        valeur = champ.get().strip()

        if valeur.isdigit():
            quantite = int(valeur)

            if quantite > 0:
                resultat[nom] = quantite

    return resultat


def ouvrir_selecteur_preset():
    _debut_performance_ui = time.perf_counter()
    noms = charger_noms_presets(
        avion_selectionne
    )

    popup = tk.Toplevel(
        fenetre
    )

    popup.after_idle(
        lambda debut=_debut_performance_ui:
        journaliser_performance_ui(
            'Sélecteur preset',
            debut
        )
    )

    popup.overrideredirect(True)
    popup.configure(
        bg=theme["bordure"]
    )

    bouton_preset.update_idletasks()

    x = bouton_preset.winfo_rootx()
    y = (
        bouton_preset.winfo_rooty()
        + bouton_preset.winfo_height()
    )

    largeur = bouton_preset.winfo_width()

    if not noms:
        hauteur = 46
    else:
        hauteur = min(
            46 * len(noms),
            230
        )

    gauche, haut, largeur_zone, hauteur_zone = _zone_travail_moniteur(
        popup,
        parent=fenetre
    )

    largeur = min(
        largeur,
        max(120, largeur_zone - 2 * MARGE_ECRAN_ADAPTATIVE)
    )
    hauteur = min(
        hauteur,
        max(46, hauteur_zone - 2 * MARGE_ECRAN_ADAPTATIVE)
    )

    x = max(
        gauche + MARGE_ECRAN_ADAPTATIVE,
        min(
            x,
            gauche + largeur_zone - largeur - MARGE_ECRAN_ADAPTATIVE
        )
    )
    y = max(
        haut + MARGE_ECRAN_ADAPTATIVE,
        min(
            y,
            haut + hauteur_zone - hauteur - MARGE_ECRAN_ADAPTATIVE
        )
    )

    popup.geometry(
        f"{largeur}x{hauteur}+{x}+{y}"
    )

    cadre = tk.Frame(
        popup,
        bg=theme["panneau"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    cadre.pack(
        fill="both",
        expand=True
    )

    canvas = tk.Canvas(
        cadre,
        bg=theme["panneau"],
        highlightthickness=0,
        borderwidth=0
    )

    canvas.pack(
        side="left",
        fill="both",
        expand=True
    )

    contenu = tk.Frame(
        canvas,
        bg=theme["panneau"]
    )

    item = canvas.create_window(
        0,
        0,
        anchor="nw",
        window=contenu
    )

    def fermer_popup(event=None):
        if popup.winfo_exists():
            popup.destroy()

    def choisir(nom):
        preset_nom_var.set(nom)
        fermer_popup()

    if not noms:
        tk.Label(
            contenu,
            text=t("main.mission.no_preset"),
            font=(POLICE, 9, "bold"),
            anchor="w",
            padx=12,
            bg=theme["panneau"],
            fg=theme["texte_faible"]
        ).pack(
            fill="x",
            ipady=10
        )
    else:
        for nom in noms:
            bouton = tk.Button(
                contenu,
                text=nom,
                command=lambda n=nom: choisir(n),
                font=(POLICE, 9, "bold"),
                anchor="w",
                padx=12,
                relief="flat",
                borderwidth=0,
                cursor="hand2",
                bg=theme["panneau"],
                fg=theme["texte"],
                activebackground=theme["panneau_alt"],
                activeforeground=theme["texte"]
            )

            bouton.pack(
                fill="x",
                ipady=9
            )

            tk.Frame(
                contenu,
                height=1,
                bg=theme["separateur"]
            ).pack(
                fill="x"
            )

    def ajuster(event=None):
        canvas.configure(
            scrollregion=canvas.bbox("all")
        )
        canvas.itemconfig(
            item,
            width=canvas.winfo_width()
        )

    contenu.bind(
        "<Configure>",
        ajuster
    )

    canvas.bind(
        "<Configure>",
        ajuster
    )

    popup.bind(
        "<Escape>",
        fermer_popup
    )

    popup.focus_force()


def actualiser_menu_presets():
    noms = charger_noms_presets(
        avion_selectionne
    )

    if not noms:
        preset_nom_var.set(
            t("main.mission.no_preset")
        )
        return

    if preset_nom_var.get() not in noms:
        preset_nom_var.set(
            noms[0]
        )


def sauvegarder_preset_actuel():
    contenu = lire_quantites_emport()

    if not contenu:
        dialogue_message_custom(
            t("main.preset.empty_title"),
            t("main.preset.empty_body"),
            "warning",
            fenetre
        )
        return


    nom = dialogue_saisie_custom(
        t("main.preset.new_title"),
        t("main.preset.new_prompt", aircraft=avion_selectionne),
        fenetre
    )


    if nom is None:
        return


    nom = nom.strip()


    if not nom:
        return


    existants = charger_noms_presets(
        avion_selectionne
    )


    if (
        nom in existants
        and not dialogue_message_custom(
            t("main.preset.replace_title"),
            t("main.preset.replace_body", name=nom),
            "question",
            fenetre
        )
    ):
        return


    enregistrer_preset(
        avion_selectionne,
        nom,
        contenu
    )


    actualiser_menu_presets()

    preset_nom_var.set(
        nom
    )


    label_message.configure(
        text=t("main.preset.saved", name=nom),
        fg=theme["vert"]
    )


def charger_preset_selectionne():
    global emports_selectionnes


    nom = preset_nom_var.get()


    if (
        not nom
        or nom == t("main.mission.no_preset")
    ):
        label_message.configure(
            text=t("main.preset.none_available"),
            fg=theme["rouge"]
        )
        return


    contenu = charger_preset(
        avion_selectionne,
        nom
    )


    if contenu is None:
        label_message.configure(
            text=t("main.preset.not_found"),
            fg=theme["rouge"]
        )
        return


    compatibles = set(
        AVIONS_EMPORTS.get(
            avion_selectionne,
            []
        )
    )


    emports_selectionnes = {
        nom_munition: int(quantite)
        for nom_munition, quantite
        in contenu.items()
        if (
            nom_munition in compatibles
            and str(quantite).isdigit()
            and int(quantite) > 0
        )
    }


    reconstruire_emport_selectionne()


    label_message.configure(
        text=t("main.preset.loaded", name=nom),
        fg=theme["vert"]
    )


def supprimer_preset_selectionne():
    nom = preset_nom_var.get()


    if (
        not nom
        or nom == t("main.mission.no_preset")
    ):
        return


    if not dialogue_message_custom(
        t("main.preset.delete_title"),
        t(
            "main.preset.delete_body",
            name=nom,
            aircraft=avion_selectionne
        ),
        "question",
        fenetre
    ):
        return


    supprimer_preset_bdd(
        avion_selectionne,
        nom
    )


    preset_nom_var.set(
        t("main.mission.no_preset")
    )


    actualiser_menu_presets()


    label_message.configure(
        text=t("main.preset.deleted"),
        fg=theme["texte_faible"]
    )


def retirer_emport(nom):
    global emports_selectionnes
    global champs_munitions


    # Sauvegarde les quantités visibles, puis retire réellement l'emport.
    valeurs = lire_quantites_emport()

    valeurs.pop(
        nom,
        None
    )

    emports_selectionnes = valeurs

    # Important : empêche reconstruire_emport_selectionne() de relire
    # les anciens Entry et de réinjecter l'emport supprimé.
    champs_munitions = {}

    reconstruire_emport_selectionne()


def ajouter_emport(nom):
    global emports_selectionnes


    valeurs = lire_quantites_emport()

    emports_selectionnes = valeurs


    if nom not in emports_selectionnes:
        emports_selectionnes[nom] = 1


    reconstruire_emport_selectionne()


def reconstruire_emport_selectionne():
    global champs_munitions
    global labels_totaux
    global emports_selectionnes


    # Récupère les valeurs visibles avant de détruire les Entry.
    if champs_munitions:
        valeurs_actuelles = lire_quantites_emport()

        for nom, quantite in valeurs_actuelles.items():
            emports_selectionnes[nom] = quantite


    vider_frame(
        contenu_emport
    )


    champs_munitions = {}
    labels_totaux = {}


    contenu_emport.configure(
        bg=theme["panneau"]
    )

    canvas_emport.configure(
        bg=theme["panneau"]
    )


    if not emports_selectionnes:
        message = t(
            "main.loadout.none_selected"
        )


        if not AVIONS_EMPORTS.get(
            avion_selectionne,
            []
        ):
            message = t(
                "main.loadout.none_available"
            )


        label = tk.Label(
            contenu_emport,
            text=message,
            font=(POLICE, 10, "bold"),
            justify="center",
            bg=theme["panneau"],
            fg=theme["texte_faible"]
        )


        label.pack(
            fill="x",
            pady=75
        )


        fenetre.update_idletasks()

        ajuster_emport_scroll()

        canvas_emport.yview_moveto(0)

        lier_molette_recursivement(
            contenu_emport,
            canvas_emport
        )

        return


    ordre_emports_selectionnes = trier_munitions_logiquement(
        list(
            emports_selectionnes.keys()
        )
    )

    for nom in ordre_emports_selectionnes:
        quantite_initiale = emports_selectionnes[
            nom
        ]
        if nom not in AVIONS_EMPORTS.get(
            avion_selectionne,
            []
        ):
            continue


        ligne = tk.Frame(
            contenu_emport,
            height=62,
            bg=theme["panneau"]
        )


        ligne.pack(
            fill="x",
            padx=5,
            pady=1
        )


        ligne.pack_propagate(
            False
        )


        categorie_visuelle = categorie_affichage_munition(
            nom
        )

        index_visuel = sum(
            1
            for autre_nom in ordre_emports_selectionnes
            if (
                categorie_affichage_munition(autre_nom)
                == categorie_visuelle
                and autre_nom.lower() < nom.lower()
            )
        )

        couleur_visuelle = couleur_munition_stock(
            nom,
            index_visuel
        )


        # Liseré couleur sur toute la hauteur de la ligne.
        #
        # Avant, le liseré était packé à gauche puis la zone icône était
        # placée en x=0 par-dessus lui, ce qui masquait presque toute la
        # couleur. On utilise maintenant uniquement place() pour garantir
        # une bande continue et visible.
        liseret_couleur = tk.Frame(
            ligne,
            bg=couleur_visuelle
        )

        liseret_couleur.place(
            x=0,
            y=0,
            width=5,
            height=62
        )


        zone_icone = tk.Frame(
            ligne,
            width=48,
            height=58,
            bg=theme["panneau"]
        )

        zone_icone.place(
            x=5,
            y=0,
            width=48,
            height=58
        )


        photo = creer_icone_munition(
            nom,
            taille=36
        )


        icone = tk.Label(
            zone_icone,
            image=photo if photo else "",
            bg=theme["panneau"]
        )

        icone.image = photo

        icone.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )


        zone_nom = tk.Frame(
            ligne,
            width=405,
            height=58,
            bg=theme["panneau"]
        )

        zone_nom.place(
            x=53,
            y=0,
            width=400,
            height=58
        )


        tk.Label(
            zone_nom,
            text=t_munition(nom),
            font=(POLICE, 9),
            anchor="w",
            justify="left",
            bg=theme["panneau"],
            fg=theme["texte"]
        ).place(
            x=5,
            y=7,
            width=395,
            height=22
        )


        stock_actuel = lire_stock_unitaire(
            nom
        )


        tk.Label(
            zone_nom,
            text=t(
                "main.loadout.base_stock",
                category=t_categorie(categorie_visuelle),
                stock=stock_actuel
            ),
            font=(POLICE, 8),
            anchor="w",
            bg=theme["panneau"],
            fg=theme["texte_faible"]
        ).place(
            x=5,
            y=31,
            width=300,
            height=20
        )


        champ = tk.Entry(
            ligne,
            justify="center",
            font=(POLICE, 11, "bold"),
            width=7,
            relief="solid",
            borderwidth=1,
            bg=theme["champ"],
            fg=theme["champ_texte"],
            insertbackground=theme["champ_texte"]
        )

        champ.place(
            x=465,
            y=12,
            width=72,
            height=36
        )


        champ.insert(
            0,
            str(quantite_initiale)
        )


        total = tk.Label(
            ligne,
            text="0",
            font=(POLICE, 11, "bold"),
            width=5,
            bg=theme["panneau"],
            fg=theme["texte"]
        )

        total.place(
            x=565,
            y=14,
            width=55,
            height=30
        )


        bouton_retirer = tk.Button(
            ligne,
            text="×",
            command=lambda n=nom:
            retirer_emport(n),
            font=(POLICE, 12, "bold"),
            width=2,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            bg=theme["panneau"],
            fg=theme["rouge"],
            activebackground=theme["panneau_alt"],
            activeforeground=theme["rouge"]
        )

        bouton_retirer.place(
            x=630,
            y=14,
            width=28,
            height=28
        )


        champs_munitions[nom] = champ
        labels_totaux[nom] = total


        champ.bind(
            "<KeyRelease>",
            calculer_totaux
        )


        tk.Frame(
            contenu_emport,
            height=1,
            bg=theme["separateur"]
        ).pack(
            fill="x",
            padx=8
        )


    fenetre.update_idletasks()

    ajuster_emport_scroll()

    canvas_emport.yview_moveto(0)

    lier_molette_recursivement(
        contenu_emport,
        canvas_emport
    )

    calculer_totaux()


def calculer_totaux(event=None):
    valeur_avions = champ_nombre_avions.get()


    if valeur_avions.isdigit():
        nombre_avions = int(
            valeur_avions
        )

    else:
        nombre_avions = 0


    for nom, champ in champs_munitions.items():
        valeur = champ.get().strip()


        if valeur.isdigit():
            total = (
                int(valeur)
                * nombre_avions
            )

        else:
            total = 0


        labels_totaux[
            nom
        ].configure(
            text=str(total)
        )


champ_nombre_avions.bind(
    "<KeyRelease>",
    calculer_totaux
)


def ouvrir_ajout_emport():
    _debut_performance_ui = time.perf_counter()
    global fenetre_ajout_emport_ouverte


    compatibles = trier_munitions_logiquement(
        AVIONS_EMPORTS.get(
            avion_selectionne,
            []
        )
    )


    if not compatibles:
        dialogue_message_custom(
            t("main.loadout.no_external_title"),
            t(
                "main.loadout.no_external_body",
                aircraft=avion_selectionne
            ),
            "info",
            fenetre
        )
        return


    if (
        fenetre_ajout_emport_ouverte is not None
        and fenetre_ajout_emport_ouverte.winfo_exists()
    ):
        fenetre_ajout_emport_ouverte.lift()
        fenetre_ajout_emport_ouverte.focus_force()
        return


    selection = tk.Toplevel(
        fenetre
    )

    selection.after_idle(
        lambda debut=_debut_performance_ui:
        journaliser_performance_ui(
            'Ajout emport',
            debut
        )
    )


    fenetre_ajout_emport_ouverte = selection

    def fermer_ajout_chrome():
        global fenetre_ajout_emport_ouverte

        fenetre_ajout_emport_ouverte = None
        selection.destroy()

    appliquer_chrome_custom(
        selection,
        t("main.loadout.add_window"),
        820,
        650,
        fermer_ajout_chrome
    )


    tk.Label(
        selection,
        text=t("main.loadout.add_title"),
        font=(POLICE, 18, "bold"),
        bg=theme["fond"],
        fg=theme["texte"]
    ).pack(
        pady=(24, 5)
    )


    tk.Label(
        selection,
        text=t(
            "main.loadout.add_subtitle",
            aircraft=avion_selectionne
        ),
        font=(POLICE, 9),
        bg=theme["fond"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 20)
    )


    zone = tk.Frame(
        selection,
        bg=theme["panneau"]
    )


    zone.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=(0, 15)
    )


    scrollbar = tk.Scrollbar(
        zone,
        orient="vertical"
    )


    scrollbar.pack(
        side="right",
        fill="y"
    )


    canvas = tk.Canvas(
        zone,
        bg=theme["panneau"],
        highlightthickness=0,
        borderwidth=0,
        yscrollcommand=scrollbar.set
    )


    canvas.pack(
        side="left",
        fill="both",
        expand=True
    )


    scrollbar.configure(
        command=canvas.yview
    )


    contenu = tk.Frame(
        canvas,
        bg=theme["panneau"]
    )


    item = canvas.create_window(
        0,
        0,
        anchor="nw",
        window=contenu
    )


    contenu.bind(
        "<Configure>",
        lambda event:
        canvas.configure(
            scrollregion=canvas.bbox(
                "all"
            )
        )
    )


    canvas.bind(
        "<Configure>",
        lambda event:
        canvas.itemconfig(
            item,
            width=event.width
        )
    )


    valeurs_actuelles = set(
        emports_selectionnes.keys()
    ) | set(
        lire_quantites_emport().keys()
    )


    def fermer_selection():
        global fenetre_ajout_emport_ouverte


        try:
            selection.unbind_all(
                "<MouseWheel>"
            )
        except Exception:
            pass


        fenetre_ajout_emport_ouverte = None

        selection.destroy()


    def choisir(nom):
        ajouter_emport(
            nom
        )

        fermer_selection()


    for nom in compatibles:
        ligne = tk.Frame(
            contenu,
            height=72,
            bg=theme["panneau"],
            highlightbackground=theme["separateur"],
            highlightthickness=1
        )


        ligne.pack(
            fill="x",
            padx=10,
            pady=4
        )


        ligne.pack_propagate(
            False
        )


        categorie_visuelle = categorie_affichage_munition(
            nom
        )

        index_visuel = sum(
            1
            for autre_nom in compatibles
            if (
                categorie_affichage_munition(autre_nom)
                == categorie_visuelle
                and autre_nom.lower() < nom.lower()
            )
        )

        couleur_visuelle = couleur_munition_stock(
            nom,
            index_visuel
        )


        liseret_couleur = tk.Frame(
            ligne,
            bg=couleur_visuelle
        )

        liseret_couleur.pack(
            side="left",
            fill="y"
        )

        liseret_couleur.configure(
            width=5
        )


        zone_icone = tk.Frame(
            ligne,
            width=62,
            height=68,
            bg=theme["panneau"]
        )


        zone_icone.pack(
            side="left",
            fill="y"
        )


        zone_icone.pack_propagate(
            False
        )


        photo = creer_icone_munition(
            nom,
            taille=42
        )


        icone = tk.Label(
            zone_icone,
            image=photo if photo else "",
            bg=theme["panneau"]
        )


        icone.image = photo


        icone.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )


        zone_info = tk.Frame(
            ligne,
            bg=theme["panneau"]
        )


        zone_info.pack(
            side="left",
            fill="both",
            expand=True,
            padx=8
        )


        tk.Label(
            zone_info,
            text=t_munition(nom),
            font=(POLICE, 10, "bold"),
            anchor="w",
            bg=theme["panneau"],
            fg=theme["texte"]
        ).pack(
            anchor="w",
            pady=(12, 2)
        )


        stock = lire_stock_unitaire(
            nom
        )


        tk.Label(
            zone_info,
            text=t(
                "main.loadout.stock_base_long",
                category=t_categorie(categorie_visuelle),
                stock=stock
            ),
            font=(POLICE, 8),
            anchor="w",
            bg=theme["panneau"],
            fg=theme["texte_faible"]
        ).pack(
            anchor="w"
        )


        deja = nom in valeurs_actuelles


        bouton = tk.Button(
            ligne,
            text=(
                t("main.loadout.already_added")
                if deja
                else t("main.loadout.add")
            ),
            command=(
                (lambda n=nom: choisir(n))
                if not deja
                else None
            ),
            state=(
                "disabled"
                if deja
                else "normal"
            ),
            font=(POLICE, 9, "bold"),
            relief="solid",
            borderwidth=1,
            cursor=(
                "arrow"
                if deja
                else "hand2"
            )
        )


        bouton.pack(
            side="right",
            padx=15,
            ipadx=12,
            ipady=5
        )


    def defiler(event):
        return defiler_canvas_avec_molette(
            canvas,
            event
        )


    canvas.bind(
        "<Enter>",
        lambda event:
        selection.bind_all(
            "<MouseWheel>",
            defiler
        )
    )


    canvas.bind(
        "<Leave>",
        lambda event:
        selection.unbind_all(
            "<MouseWheel>"
        )
    )


    contenu.bind(
        "<Enter>",
        lambda event:
        selection.bind_all(
            "<MouseWheel>",
            defiler
        )
    )


    contenu.bind(
        "<Leave>",
        lambda event:
        selection.unbind_all(
            "<MouseWheel>"
        )
    )


    selection.update_idletasks()


    lier_molette_recursivement(
        contenu,
        canvas
    )


    tk.Button(
        selection,
        text=t("common.close"),
        command=fermer_selection,
        font=(POLICE, 9, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"],
        activebackground=theme["panneau_alt"],
        activeforeground=theme["texte"],
        relief="solid",
        borderwidth=1
    ).pack(
        pady=(0, 18),
        ipadx=18,
        ipady=5
    )


    selection.protocol(
        "WM_DELETE_WINDOW",
        fermer_selection
    )


def valider_mission():
    global emports_selectionnes

    try:
        datetime.strptime(
            champ_date.get().strip(),
            "%d.%m.%Y"
        )

    except ValueError:
        label_message.configure(
            text=t("main.validation.career_date"),
            fg=theme["rouge"]
        )
        return

    try:
        heure_mission_validee = datetime.strptime(
            champ_heure.get().strip(),
            "%H:%M"
        )

        texte_heure_validee = heure_mission_validee.strftime(
            "%H:%M"
        )

        champ_heure.delete(
            0,
            "end"
        )

        champ_heure.insert(
            0,
            texte_heure_validee
        )

        sauvegarder_preparation_mission(
            heure_texte=texte_heure_validee
        )

    except ValueError:
        label_message.configure(
            text=t("main.validation.invalid_time"),
            fg=theme["rouge"]
        )
        return

    valeur_avions = champ_nombre_avions.get()

    if not valeur_avions.isdigit():
        label_message.configure(
            text=t("main.validation.invalid_aircraft_count"),
            fg=theme["rouge"]
        )
        return

    nombre_avions = int(
        valeur_avions
    )

    if nombre_avions <= 0:
        label_message.configure(
            text=t("main.validation.aircraft_count_positive"),
            fg=theme["rouge"]
        )
        return

    if not champs_munitions:
        label_message.configure(
            text=t("main.validation.no_loadout"),
            fg=theme["rouge"]
        )
        return

    demandes = []

    for nom, champ in champs_munitions.items():
        valeur = champ.get().strip()

        if not valeur.isdigit():
            label_message.configure(
                text=t("main.validation.invalid_quantity", munition=t_munition(nom)),
                fg=theme["rouge"]
            )
            return

        par_avion = int(
            valeur
        )

        if par_avion <= 0:
            continue

        total = (
            par_avion
            * nombre_avions
        )

        stock_actuel = lire_stock_unitaire(
            nom
        )

        if total > stock_actuel:
            label_message.configure(
                text=t("main.validation.insufficient_stock", munition=t_munition(nom)),
                fg=theme["rouge"]
            )
            return

        demandes.append(
            (
                nom,
                par_avion,
                total
            )
        )

    if not demandes:
        label_message.configure(
            text=t("main.validation.no_quantity"),
            fg=theme["rouge"]
        )
        return

    date_complete = (
        champ_date.get()
        + " - "
        + champ_heure.get()
    )

    try:
        stock_engine.enregistrer_mission_et_consommer(
            FICHIER_BASE,
            date_heure=date_complete,
            avion=avion_selectionne,
            nombre_avions=nombre_avions,
            demandes=[
                (
                    nom,
                    total
                )
                for (
                    nom,
                    par_avion,
                    total
                ) in demandes
            ]
        )

    except stock_engine.StockInsuffisantError as erreur:
        label_message.configure(
            text=t("main.validation.insufficient_stock", munition=t_munition(erreur.nom)),
            fg=theme["rouge"]
        )
        return

    except Exception as erreur:
        journaliser_erreur_runtime(
            "Enregistrement mission / consommation stock",
            erreur
        )

        label_message.configure(
            text=t("main.validation.save_error"),
            fg=theme["rouge"]
        )
        return

    emports_selectionnes = {}

    reconstruire_emport_selectionne()

    afficher_historique()

    label_message.configure(
        text=t("main.validation.saved"),
        fg=theme["vert"]
    )


def changer_avion(nom_avion):
    global avion_selectionne
    global emports_selectionnes


    avion_selectionne = nom_avion


    config["avion"] = nom_avion


    sauvegarder_config()


    if DONNEES_CARRIERE_IL2 is not None:
        bouton_selection_avion.configure(
            text=(
                f"{nom_avion}  •  "
                f"{t('main.aircraft.linked')}"
            )
        )

    else:
        bouton_selection_avion.configure(
            text=(
                f"{nom_avion}  ▼"
            )
        )


    actualiser_image_avion()


    # Un changement d'appareil repart sur une préparation vide.
    emports_selectionnes = {}


    reconstruire_emport_selectionne()

    actualiser_menu_presets()


    preset_nom_var.set(
        (
            charger_noms_presets(
                avion_selectionne
            )[0]
            if charger_noms_presets(
                avion_selectionne
            )
            else t("main.mission.no_preset")
        )
    )


    label_message.configure(
        text=""
    )


# ============================================================
# SELECTEUR D'APPAREIL
# ============================================================

def ouvrir_selection_avion():
    _debut_performance_ui = time.perf_counter()
    global fenetre_selection_avion_ouverte

    if (
        fenetre_selection_avion_ouverte is not None
        and
        fenetre_selection_avion_ouverte.winfo_exists()
    ):
        fenetre_selection_avion_ouverte.lift()
        fenetre_selection_avion_ouverte.focus_force()
        return

    selection = tk.Toplevel(
        fenetre
    )

    selection.after_idle(
        lambda debut=_debut_performance_ui:
        journaliser_performance_ui(
            'Sélection avion',
            debut
        )
    )

    fenetre_selection_avion_ouverte = selection

    def fermer_selection_chrome():
        global fenetre_selection_avion_ouverte

        fenetre_selection_avion_ouverte = None
        selection.destroy()

    appliquer_chrome_custom(
        selection,
        t("main.aircraft_selector.window"),
        760,
        650,
        fermer_selection_chrome
    )

    tk.Label(
        selection,
        text=t("main.aircraft_selector.title"),
        font=(POLICE, 18, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(25, 5)
    )

    tk.Label(
        selection,
        text=t("main.aircraft_selector.subtitle"),
        font=POLICE_PETIT,
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 20)
    )

    zone_scroll = tk.Frame(
        selection,
        bg=theme["panneau"]
    )

    zone_scroll.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=(0, 15)
    )

    scrollbar = tk.Scrollbar(
        zone_scroll,
        orient="vertical"
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    canvas = tk.Canvas(
        zone_scroll,
        bg=theme["panneau"],
        highlightthickness=0,
        yscrollcommand=scrollbar.set
    )

    canvas.pack(
        side="left",
        fill="both",
        expand=True
    )

    scrollbar.configure(
        command=canvas.yview
    )

    contenu = tk.Frame(
        canvas,
        bg=theme["panneau"]
    )

    item = canvas.create_window(
        0,
        0,
        anchor="nw",
        window=contenu
    )

    contenu.bind(
        "<Configure>",
        lambda event:
        canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.bind(
        "<Configure>",
        lambda event:
        canvas.itemconfig(
            item,
            width=event.width
        )
    )

    selection.images_avions = []

    def fermer_selection():
        global fenetre_selection_avion_ouverte

        canvas.unbind_all(
            "<MouseWheel>"
        )

        fenetre_selection_avion_ouverte = None
        selection.destroy()

    def choisir(nom):
        changer_avion(nom)
        fermer_selection()

    for nom_avion, donnees in AVIONS.items():
        est_actif = (
            nom_avion == avion_selectionne
        )

        couleur_bordure = (
            theme["vert"]
            if est_actif
            else theme["bordure"]
        )

        carte = tk.Frame(
            contenu,
            bg=theme["panneau_alt"],
            highlightbackground=couleur_bordure,
            highlightcolor=couleur_bordure,
            highlightthickness=2 if est_actif else 1,
            cursor="hand2"
        )

        carte.pack(
            fill="x",
            padx=15,
            pady=7
        )

        cadre_miniature = tk.Frame(
            carte,
            bg=theme["champ"],
            width=205,
            height=92
        )

        cadre_miniature.pack(
            side="left",
            padx=12,
            pady=10
        )

        cadre_miniature.pack_propagate(
            False
        )

        label_miniature = tk.Label(
            cadre_miniature,
            bg=theme["champ"]
        )

        label_miniature.pack(
            fill="both",
            expand=True
        )

        chemin_image = donnees["image"]

        if chemin_image.exists():
            try:
                miniature = Image.open(
                    chemin_image
                ).convert("RGBA")

                miniature = adapter_image_contain(
                    miniature,
                    195,
                    82
                )

                photo = ImageTk.PhotoImage(
                    miniature
                )

                selection.images_avions.append(
                    photo
                )

                label_miniature.configure(
                    image=photo
                )

            except Exception:
                label_miniature.configure(
                    text=t("main.aircraft.image_unavailable"),
                    font=(POLICE, 7),
                    fg=theme["texte_faible"]
                )

        zone_info = tk.Frame(
            carte,
            bg=theme["panneau_alt"]
        )

        zone_info.pack(
            side="left",
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        label_nom = tk.Label(
            zone_info,
            text=nom_avion,
            font=(POLICE, 13, "bold"),
            bg=theme["panneau_alt"],
            fg=theme["texte"],
            anchor="w"
        )

        label_nom.pack(
            anchor="w",
            pady=(12, 4)
        )

        nombre_emports = len(
            AVIONS_EMPORTS.get(
                nom_avion,
                []
            )
        )

        if est_actif:
            texte_etat = t("main.aircraft_selector.active")
            couleur_etat = theme["vert"]

        elif nombre_emports == 0:
            texte_etat = t("main.aircraft_selector.no_loadout")
            couleur_etat = theme["texte_faible"]

        else:
            texte_etat = t(
                "main.aircraft_selector.compatible_count",
                count=nombre_emports
            )
            couleur_etat = theme["texte_faible"]

        label_etat = tk.Label(
            zone_info,
            text=texte_etat,
            font=(POLICE, 8, "bold"),
            bg=theme["panneau_alt"],
            fg=couleur_etat,
            anchor="w"
        )

        label_etat.pack(
            anchor="w"
        )

        for widget in [
            carte,
            cadre_miniature,
            label_miniature,
            zone_info,
            label_nom,
            label_etat
        ]:
            widget.bind(
                "<Button-1>",
                lambda event, n=nom_avion:
                choisir(n)
            )

    def defiler(event):
        canvas.yview_scroll(
            int(-event.delta / 120),
            "units"
        )

    canvas.bind(
        "<Enter>",
        lambda event:
        canvas.bind_all(
            "<MouseWheel>",
            defiler
        )
    )

    canvas.bind(
        "<Leave>",
        lambda event:
        canvas.unbind_all(
            "<MouseWheel>"
        )
    )

    tk.Button(
        selection,
        text=t("common.close"),
        command=fermer_selection,
        font=POLICE_PETIT,
        bg=theme["panneau"],
        fg=theme["texte"],
        activebackground=theme["panneau_alt"],
        activeforeground=theme["texte"]
    ).pack(
        pady=(0, 18)
    )

    selection.protocol(
        "WM_DELETE_WINDOW",
        fermer_selection
    )


bouton_selection_avion.configure(
    command=lambda:
    dialogue_message_custom(
        t("main.aircraft.linked_title"),
        t(
            "main.aircraft.linked_body",
            aircraft=avion_selectionne
        ),
        "info",
        fenetre
    )
)


# ============================================================
# RAFRAÎCHISSEMENT GLOBAL DU THÈME
# ============================================================

def _normaliser_couleur_tk(
    valeur
):
    try:
        return str(
            valeur
        ).strip().lower()
    except Exception:
        return ""


def _table_remappage_theme(
    ancien_theme,
    nouveau_theme
):
    """
    Construit une correspondance exacte :
    couleur de l'ancien thème -> couleur du nouveau thème.

    Seules les couleurs appartenant réellement au thème sont remappées.
    Les couleurs métier (catégories de munitions, graphiques, etc.)
    restent donc intactes.
    """
    correspondances = {}

    for cle, ancienne_couleur in ancien_theme.items():
        if cle not in nouveau_theme:
            continue

        if not isinstance(
            ancienne_couleur,
            str
        ):
            continue

        nouvelle_couleur = nouveau_theme[
            cle
        ]

        if not isinstance(
            nouvelle_couleur,
            str
        ):
            continue

        correspondances[
            _normaliser_couleur_tk(
                ancienne_couleur
            )
        ] = nouvelle_couleur

    return correspondances


def _remapper_option_couleur_widget(
    widget,
    option,
    correspondances
):
    try:
        valeur = widget.cget(
            option
        )
    except Exception:
        return

    cle = _normaliser_couleur_tk(
        valeur
    )

    if cle not in correspondances:
        return

    try:
        widget.configure(
            **{
                option: correspondances[
                    cle
                ]
            }
        )
    except Exception:
        pass


def _remapper_canvas_theme(
    canvas,
    correspondances
):
    """
    Les objets dessinés dans un Canvas ne sont pas des widgets Tk.
    On remappe donc aussi leurs couleurs fill/outline séparément.
    """
    try:
        items = canvas.find_all()
    except Exception:
        return

    for item in items:
        for option in (
            "fill",
            "outline"
        ):
            try:
                valeur = canvas.itemcget(
                    item,
                    option
                )
            except Exception:
                continue

            cle = _normaliser_couleur_tk(
                valeur
            )

            if cle not in correspondances:
                continue

            try:
                canvas.itemconfigure(
                    item,
                    **{
                        option: correspondances[
                            cle
                        ]
                    }
                )
            except Exception:
                pass


def remapper_theme_widget_recursif(
    widget,
    ancien_theme,
    nouveau_theme
):
    """
    Repeint récursivement un widget et tous ses descendants.

    Les widgets marqués `_theme_preview_fixe = True` sont volontairement
    ignorés : c'est notamment le cas des cartes de prévisualisation
    Clair/Sombre dans Options, qui doivent montrer leurs propres couleurs.
    """
    try:
        if not widget.winfo_exists():
            return
    except Exception:
        return

    if getattr(
        widget,
        "_theme_preview_fixe",
        False
    ):
        return

    correspondances = _table_remappage_theme(
        ancien_theme,
        nouveau_theme
    )

    options_couleur = (
        "background",
        "foreground",
        "activebackground",
        "activeforeground",
        "disabledforeground",
        "highlightbackground",
        "highlightcolor",
        "insertbackground",
        "readonlybackground",
        "selectbackground",
        "selectforeground",
        "buttonbackground",
        "troughcolor"
    )

    for option in options_couleur:
        _remapper_option_couleur_widget(
            widget,
            option,
            correspondances
        )

    if isinstance(
        widget,
        tk.Canvas
    ):
        _remapper_canvas_theme(
            widget,
            correspondances
        )

    try:
        enfants = widget.winfo_children()
    except Exception:
        enfants = []

    for enfant in enfants:
        remapper_theme_widget_recursif(
            enfant,
            ancien_theme,
            nouveau_theme
        )


def rafraichir_theme_toutes_fenetres(
    ancien_theme,
    nouveau_theme
):
    """
    Repeint immédiatement la fenêtre principale ET tous les Toplevel ouverts.
    """
    remapper_theme_widget_recursif(
        fenetre,
        ancien_theme,
        nouveau_theme
    )

    # Les Toplevel sont déjà descendants de Tk, mais cette deuxième passe
    # explicite sécurise les fenêtres transient / custom créées dynamiquement.
    try:
        for enfant in fenetre.winfo_children():
            if isinstance(
                enfant,
                tk.Toplevel
            ):
                remapper_theme_widget_recursif(
                    enfant,
                    ancien_theme,
                    nouveau_theme
                )
    except Exception:
        pass

    actualiser_contours_fenetres()


# ============================================================
# APPLICATION DU THEME
# ============================================================

def appliquer_theme(
    nom_theme,
    sauvegarder=True
):
    global theme

    ancien_theme = dict(
        theme
    )

    theme = THEMES[
        nom_theme
    ]

    if sauvegarder:
        config["theme"] = nom_theme
        sauvegarder_config()

    # --------------------------------------------------------
    # RAFRAÎCHISSEMENT GLOBAL
    # --------------------------------------------------------
    # L'ancien système reposait uniquement sur quelques listes de widgets.
    # Tout widget créé dynamiquement ou dans un Toplevel pouvait donc garder
    # des couleurs de l'ancien thème jusqu'au redémarrage.
    #
    # On remappe maintenant immédiatement toutes les couleurs de palette
    # présentes dans toutes les fenêtres ouvertes.
    rafraichir_theme_toutes_fenetres(
        ancien_theme,
        theme
    )

    fenetre.configure(
        bg=theme["fond"]
    )

    for widget in widgets_fond:
        try:
            widget.configure(
                bg=theme["fond"],
                fg=theme["texte"]
            )
        except tk.TclError:
            try:
                widget.configure(
                    bg=theme["fond"]
                )
            except tk.TclError:
                pass

    for widget in widgets_panneau:
        try:
            widget.configure(
                bg=theme["panneau"],
                fg=theme["texte"]
            )
        except tk.TclError:
            try:
                widget.configure(
                    bg=theme["panneau"]
                )
            except tk.TclError:
                pass

    for widget in widgets_panneau_alt:
        try:
            widget.configure(
                bg=theme["panneau_alt"],
                fg=theme["texte"],
                activebackground=theme["champ"],
                activeforeground=theme["texte"]
            )
        except tk.TclError:
            pass

    for widget in widgets_texte_faible:
        try:
            widget.configure(
                bg=theme["panneau"],
                fg=theme["texte_faible"]
            )
        except tk.TclError:
            pass

    for widget in widgets_bordure:
        try:
            widget.configure(
                highlightbackground=theme["bordure"],
                highlightcolor=theme["bordure"]
            )
        except tk.TclError:
            pass

    for widget in widgets_separateur:
        try:
            widget.configure(
                bg=theme["separateur"]
            )
        except tk.TclError:
            pass

    for widget in widgets_champ:
        try:
            widget.configure(
                bg=theme["champ"],
                fg=theme["champ_texte"],
                insertbackground=theme["champ_texte"]
            )
        except tk.TclError:
            pass

    for widget in widgets_bouton:
        try:
            widget.configure(
                bg=theme["panneau"],
                fg=theme["texte"],
                activebackground=theme["panneau_alt"],
                activeforeground=theme["texte"]
            )
        except tk.TclError:
            pass

    for widget in widgets_barre:
        try:
            widget.configure(
                bg=theme["barre"],
                fg=theme["blanc"]
            )
        except tk.TclError:
            try:
                widget.configure(
                    bg=theme["barre"]
                )
            except tk.TclError:
                pass

    for widget in widgets_barre_bouton:
        try:
            widget.configure(
                bg=theme["barre"],
                fg=theme["blanc"],
                activeforeground=theme["blanc"],
                activebackground=theme["panneau_alt"]
            )
        except tk.TclError:
            pass

    bouton_fermer.configure(
        activebackground=theme["rouge"]
    )

    # Le bouton UPDATE doit rester rouge lorsqu'une mise à jour
    # est disponible, même après un changement de thème.
    actualiser_bouton_mise_a_jour()


    actualiser_contours_fenetres()

    cadre_image_avion.configure(
        bg=theme["champ"],
        highlightbackground=theme["bordure"],
        highlightcolor=theme["bordure"]
    )

    label_image_avion.configure(
        bg=theme["champ"]
    )

    canvas_historique.configure(
        bg=theme["panneau"]
    )

    canvas_emport.configure(
        bg=theme["panneau"]
    )

    label_message.configure(
        bg=theme["panneau"]
    )

    reconstruire_emport_selectionne()
    actualiser_menu_presets()
    afficher_historique()
    actualiser_image_avion()

    # Les fonctions ci-dessus peuvent reconstruire certains widgets.
    # Une dernière passe garantit qu'ils utilisent tous le thème courant.
    fenetre.after_idle(
        lambda:
        rafraichir_theme_toutes_fenetres(
            ancien_theme,
            theme
        )
    )


# ============================================================
# OUTILS ADMIN
# ============================================================

def modifier_points_commandement_admin():
    if not mode_admin_actif():
        dialogue_message_custom(
            t("admin.required.title"),
            t("admin.required.body"),
            "info",
            fenetre
        )
        return

    dialogue = tk.Toplevel(
        fenetre
    )

    appliquer_chrome_custom(
        dialogue,
        t("admin.points.window"),
        520,
        300,
        dialogue.destroy
    )

    fond = tk.Frame(
        dialogue,
        bg=theme["panneau"]
    )

    fond.pack(
        fill="both",
        expand=True
    )

    tk.Label(
        fond,
        text=t("admin.points.title"),
        font=(POLICE, 15, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(28, 8)
    )

    tk.Label(
        fond,
        text=t("admin.points.description"),
        font=(POLICE, 8),
        justify="center",
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 18)
    )

    variable_points = tk.StringVar(
        value=str(
            obtenir_points_commandement()
        )
    )

    entree = tk.Entry(
        fond,
        textvariable=variable_points,
        justify="center",
        font=(POLICE, 14, "bold"),
        bg=theme["champ"],
        fg=theme["champ_texte"],
        insertbackground=theme["champ_texte"],
        relief="solid",
        borderwidth=1
    )

    entree.pack(
        ipadx=20,
        ipady=7
    )

    def enregistrer_points():
        try:
            texte = (
                variable_points.get()
                .strip()
                .replace(
                    ",",
                    "."
                )
            )

            valeur = float(
                texte
            )

            valeur_x10 = int(
                round(
                    valeur
                    * 10
                )
            )

            if (
                valeur < 0
                or abs(
                    valeur_x10 / 10.0
                    - valeur
                ) > 0.000001
            ):
                raise ValueError

        except ValueError:
            dialogue_message_custom(
                t("admin.value_invalid.title"),
                t("admin.value_invalid.body"),
                "error",
                dialogue
            )
            return

        try:
            local_db.definir_points_commandement_x10(
                FICHIER_BASE,
                valeur_x10
            )

        except Exception as erreur:
            dialogue_message_custom(
                t("common.error"),
                str(
                    erreur
                ),
                "error",
                dialogue
            )
            return

        actualiser_affichage_points_commandement_ouvert()

        dialogue.destroy()

        dialogue_message_custom(
            t("admin.points.changed_title"),
            t(
                "admin.points.changed_body",
                points=formater_points_commandement(valeur_x10 / 10.0)
            ),
            "info",
            fenetre
        )

    tk.Button(
        fond,
        text=t("common.save"),
        command=enregistrer_points,
        font=(POLICE, 9, "bold"),
        bg=theme["vert"],
        fg=theme["blanc"],
        activebackground=theme["vert"],
        activeforeground=theme["blanc"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    ).pack(
        pady=22,
        ipadx=25,
        ipady=7
    )

    entree.focus_set()
    entree.selection_range(
        0,
        "end"
    )


def modifier_gain_points_commandement_admin():
    """
    Modifie le gain journalier pour la carrière locale active.

    Valeurs autorisées :
    0,1 / 0,5 / 1 / 2 / 3 points par jour de campagne.
    """
    if not mode_admin_actif():
        dialogue_message_custom(
            t("admin.required.title"),
            t("admin.required.body"),
            "info",
            fenetre
        )
        return

    # Crédite d'abord les éventuels jours écoulés avec l'ancien taux.
    try:
        actualiser_points_commandement_journaliers()
    except Exception:
        pass

    dialogue = tk.Toplevel(
        fenetre
    )

    appliquer_chrome_custom(
        dialogue,
        t("admin.daily.window"),
        660,
        430,
        dialogue.destroy
    )

    fond = tk.Frame(
        dialogue,
        bg=theme["panneau"]
    )

    fond.pack(
        fill="both",
        expand=True
    )

    tk.Label(
        fond,
        text=t("admin.daily.title"),
        font=(POLICE, 15, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(26, 6)
    )

    tk.Label(
        fond,
        text=t("admin.daily.description"),
        font=(POLICE, 8),
        justify="center",
        wraplength=550,
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        padx=35,
        pady=(0, 20)
    )

    courant_x10 = int(
        round(
            obtenir_gain_points_journalier()
            * 10
        )
    )

    variable_gain = tk.IntVar(
        value=courant_x10
    )

    cadre_choix = tk.Frame(
        fond,
        bg=theme["panneau"]
    )

    cadre_choix.pack(
        fill="x",
        padx=34,
        pady=(0, 16)
    )

    boutons_gain = {}

    def rafraichir_choix():
        selection = int(
            variable_gain.get()
        )

        for valeur_x10, bouton in boutons_gain.items():
            actif = (
                valeur_x10 == selection
            )

            bouton.configure(
                bg=(
                    COULEUR_OR_COMMANDEMENT
                    if actif
                    else theme["panneau_alt"]
                ),
                fg=(
                    theme["barre"]
                    if actif
                    else theme["texte"]
                ),
                activebackground=COULEUR_OR_COMMANDEMENT_ACTIF,
                activeforeground=theme["barre"]
            )

    def selectionner_gain(
        valeur_x10
    ):
        variable_gain.set(
            int(
                valeur_x10
            )
        )

        rafraichir_choix()

    for valeur_x10 in GAINS_POINTS_JOURNALIERS_ADMIN_X10:
        valeur = (
            valeur_x10
            / 10.0
        )

        bouton = tk.Button(
            cadre_choix,
            text=t(
                "admin.daily.rate_option",
                value=formater_points_commandement(valeur)
            ),
            command=lambda v=valeur_x10:
            selectionner_gain(
                v
            ),
            font=(POLICE, 9, "bold"),
            relief="solid",
            borderwidth=1,
            cursor="hand2"
        )

        bouton.pack(
            side="left",
            fill="x",
            expand=True,
            padx=4,
            ipady=10
        )

        boutons_gain[
            valeur_x10
        ] = bouton

    rafraichir_choix()

    label_actuel = tk.Label(
        fond,
        text=t(
            "admin.daily.current_rate",
            value=texte_gain_points_journalier().replace("+", "", 1)
        ),
        font=(POLICE, 8, "bold"),
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    )

    label_actuel.pack(
        pady=(2, 16)
    )

    def enregistrer_gain():
        valeur_x10 = int(
            variable_gain.get()
        )

        try:
            local_db.definir_gain_points_journalier_x10(
                FICHIER_BASE,
                valeur_x10
            )

        except Exception as erreur:
            dialogue_message_custom(
                t("common.error"),
                str(
                    erreur
                ),
                "error",
                dialogue
            )
            return

        actualiser_affichage_points_commandement_ouvert()

        dialogue.destroy()

        dialogue_message_custom(
            t("admin.daily.saved_title"),
            t(
                "admin.daily.saved_body",
                points=formater_points_commandement(valeur_x10 / 10.0)
            ),
            "info",
            fenetre
        )

    tk.Button(
        fond,
        text=t("common.save"),
        command=enregistrer_gain,
        font=(POLICE, 9, "bold"),
        bg=theme["vert"],
        fg=theme["blanc"],
        activebackground=theme["vert"],
        activeforeground=theme["blanc"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    ).pack(
        pady=(0, 24),
        ipadx=28,
        ipady=8
    )


def reinitialiser_toute_carriere_admin():
    """
    Reset usine complet de la carrière LOCALE.

    Préserve volontairement :
    - la base IL-2, strictement en lecture seule ;
    - les préréglages de mission utilisateur ;
    - les modèles/presets de répartition personnalisés créés par l'utilisateur ;
    - les préférences globales de l'application (thème, mode admin).

    Réinitialise :
    - stock concret ;
    - historique de missions ;
    - rapports ;
    - historique de ravitaillements ;
    - boosts ;
    - livraisons urgentes ;
    - directives du Haut commandement ;
    - points de commandement ;
    - paramètres de ravitaillement ;
    - modèle actif ;
    - capacité/référence de synchro ;
    - préparation de mission courante.
    """
    if not mode_admin_actif():
        dialogue_message_custom(
            t("admin.required.title"),
            t("admin.required.body"),
            "info",
            fenetre
        )
        return

    # Relecture de la date avant le reset pour repartir du vrai état IL-2.
    try:
        rafraichir_date_carriere_en_memoire()
    except Exception:
        pass

    avion = DONNEES_CARRIERE_IL2.get(
        "avion",
        avion_selectionne
    )

    annee, mois = extraire_annee_mois_carriere(
        DONNEES_CARRIERE_IL2
    )

    ammo_qty = max(
        0,
        int(
            DONNEES_CARRIERE_IL2.get(
                "ammo_qty",
                0
            )
        )
    )

    noms_mois = {
        1: "JANVIER",
        2: "FÉVRIER",
        3: "MARS",
        4: "AVRIL",
        5: "MAI",
        6: "JUIN",
        7: "JUILLET",
        8: "AOÛT",
        9: "SEPTEMBRE",
        10: "OCTOBRE",
        11: "NOVEMBRE",
        12: "DÉCEMBRE"
    }

    popup = tk.Toplevel(
        fenetre
    )

    appliquer_chrome_custom(
        popup,
        t("admin.reset_all.window"),
        780,
        690,
        popup.destroy
    )

    popup.transient(
        fenetre
    )

    popup.grab_set()

    fond = tk.Frame(
        popup,
        bg=theme["panneau"]
    )

    fond.pack(
        fill="both",
        expand=True
    )

    tk.Label(
        fond,
        text=t("admin.reset_all.title"),
        font=(POLICE, 16, "bold"),
        bg=theme["panneau"],
        fg=theme["rouge"]
    ).pack(
        pady=(28, 6)
    )

    tk.Label(
        fond,
        text=t("admin.reset_all.description"),
        font=(POLICE, 9),
        justify="center",
        wraplength=650,
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        padx=45,
        pady=(4, 14)
    )

    cadre_infos = tk.Frame(
        fond,
        bg=theme["panneau_alt"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    cadre_infos.pack(
        fill="x",
        padx=55,
        pady=(0, 14)
    )

    tk.Label(
        cadre_infos,
        text=t(
            "admin.reset_all.summary",
            aircraft=avion,
            period=f"{t_mois(mois)} {annee}",
            ammo=ammo_qty
        ),
        font=(POLICE, 9, "bold"),
        justify="center",
        bg=theme["panneau_alt"],
        fg=theme["texte"]
    ).pack(
        pady=14
    )

    tk.Label(
        fond,
        text=t("admin.reset_all.will"),
        font=(POLICE, 9),
        justify="left",
        anchor="w",
        wraplength=610,
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        fill="x",
        padx=80,
        pady=(0, 14)
    )

    tk.Label(
        fond,
        text=t("admin.reset_all.keep"),
        font=(POLICE, 8, "bold"),
        justify="center",
        wraplength=630,
        bg=theme["panneau"],
        fg=theme["vert"]
    ).pack(
        padx=55,
        pady=(0, 18)
    )

    zone_boutons = tk.Frame(
        fond,
        bg=theme["panneau"]
    )

    zone_boutons.pack(
        fill="x",
        padx=55,
        pady=(0, 28)
    )

    def fermer_popup():
        try:
            popup.grab_release()
        except Exception:
            pass

        popup.destroy()

    def confirmer_reset_total():
        global emports_selectionnes
        global champs_munitions

        fichier_sync = cle_sync_carriere(
            DONNEES_CARRIERE_IL2
        )

        signature = stock_engine.signature_snapshot_carriere(
            DONNEES_CARRIERE_IL2
        )

        nouveau_stock = calculer_stock_initial_standard_carriere(
            avion,
            DONNEES_CARRIERE_IL2
        )

        date_reference_points = (
            extraire_date_complete_carriere(
                DONNEES_CARRIERE_IL2
            )
            or obtenir_date_reference_commandement()
        )

        ordinal_points = date_reference_points.date().toordinal()

        connexion = sqlite3.connect(
            FICHIER_BASE
        )

        try:
            connexion.execute(
                "BEGIN IMMEDIATE"
            )

            curseur = connexion.cursor()

            # ------------------------------------------------
            # HISTORIQUES / ÉTATS DE CARRIÈRE
            # ------------------------------------------------
            for table in (
                "missions",
                "ravitaillements",
                "rapports_carriere",
                "boosts_commandement",
                "livraisons_urgentes",
                "directives_standard_priorites",
                "directives_standard_commandement",
                "carriere_sync",
                "capacite_carriere",
                "priorites_repartition_mensuelles"
            ):
                curseur.execute(
                    f"DELETE FROM {table}"
                )

            # ------------------------------------------------
            # PARAMÈTRES DE CARRIÈRE
            # ------------------------------------------------
            curseur.execute(
                "DELETE FROM preferences_repartition"
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
                """
            )

            curseur.execute(
                """
                INSERT INTO preferences_repartition (
                    cle,
                    valeur
                )
                VALUES (
                    'mode_repartition',
                    'STANDARD'
                )
                """
            )

            curseur.execute(
                "DELETE FROM commandement_etat"
            )

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
                """
            )

            curseur.execute(
                """
                INSERT INTO commandement_etat (
                    cle,
                    valeur
                )
                VALUES (
                    'derniere_date_gain_points',
                    ?
                )
                """,
                (
                    int(
                        ordinal_points
                    ),
                )
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
                """,
                (
                    int(
                        local_db.VERSION_USINE_POINTS_COMMANDEMENT
                    ),
                )
            )

            # Ancienne clé locale conservée uniquement pour compatibilité.
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
                """
            )

            # Paramètres de ravitaillement usine.
            curseur.execute(
                "DELETE FROM ravitaillement_parametres"
            )

            for cle, valeur in PARAMETRES_RAVITAILLEMENT_DEFAUT.items():
                curseur.execute(
                    """
                    INSERT INTO ravitaillement_parametres (
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

            # Modèles de simulation internes remis à leurs valeurs usine.
            curseur.execute(
                "DELETE FROM modeles_simulation"
            )

            for cle_profil in PROFILS_SIMULATION:
                curseur.execute(
                    """
                    INSERT INTO modeles_simulation (
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

            # ------------------------------------------------
            # STOCK STANDARD DE DÉPART
            # ------------------------------------------------
            curseur.execute(
                """
                UPDATE munitions
                SET stock = 0
                """
            )

            for munition, quantite in nouveau_stock.items():
                curseur.execute(
                    """
                    UPDATE munitions
                    SET stock = ?
                    WHERE nom = ?
                    """,
                    (
                        int(
                            quantite
                        ),
                        munition
                    )
                )

            # ------------------------------------------------
            # NOUVELLE RÉFÉRENCE IL-2 SANS FAUX RAVITAILLEMENT
            # ------------------------------------------------
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
                """,
                (
                    fichier_sync,
                    avion,
                    ammo_qty,
                    signature,
                    datetime.now().strftime(
                        "%d.%m.%Y - %H:%M"
                    )
                )
            )

            curseur.execute(
                """
                INSERT INTO capacite_carriere (
                    fichier,
                    reference_max
                )
                VALUES (?, ?)
                """,
                (
                    fichier_sync,
                    ammo_qty
                )
            )

            # Métadonnées de l'état usine courant.
            curseur.execute(
                """
                INSERT INTO carriere_locale_meta (
                    cle,
                    valeur
                )
                VALUES (
                    'defaults_version',
                    '2'
                )
                ON CONFLICT(cle)
                DO UPDATE SET
                    valeur = excluded.valeur
                """
            )

            curseur.execute(
                """
                INSERT INTO carriere_locale_meta (
                    cle,
                    valeur
                )
                VALUES (
                    'dernier_reset_total',
                    ?
                )
                ON CONFLICT(cle)
                DO UPDATE SET
                    valeur = excluded.valeur
                """,
                (
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                )
            )

            connexion.commit()

        except Exception as erreur:
            connexion.rollback()
            connexion.close()

            dialogue_message_custom(
                t("common.error"),
                t("admin.reset_all.fail_body", error=str(erreur)),
                "error",
                popup
            )
            return

        connexion.close()

        # ----------------------------------------------------
        # CONFIG DE PRÉPARATION DE MISSION POUR CETTE CARRIÈRE
        # ----------------------------------------------------
        try:
            cle_preparation = cle_preparation_mission_carriere()

            config.setdefault(
                "preparation_mission",
                {}
            ).pop(
                cle_preparation,
                None
            )

            sauvegarder_config()

        except Exception:
            pass

        # ----------------------------------------------------
        # ÉTAT VISUEL COURANT
        # ----------------------------------------------------
        try:
            emports_selectionnes = {}
            champs_munitions = {}

            reconstruire_emport_selectionne()

            champ_nombre_avions.delete(
                0,
                "end"
            )

            champ_nombre_avions.insert(
                0,
                "1"
            )

            rafraichir_date_interface_depuis_carriere(
                DONNEES_CARRIERE_IL2
            )

            champ_heure.delete(
                0,
                "end"
            )

            champ_heure.insert(
                0,
                "10:00"
            )

            preset_nom_var.set(
                t("main.mission.no_preset")
            )

            calculer_totaux()
            actualiser_badge_rapports()

        except Exception:
            pass

        try:
            rafraichir_interface_apres_synchro()
        except Exception:
            pass

        fermer_popup()

        dialogue_message_custom(
            t("admin.reset_all.success_title"),
            t("admin.reset_all.success_body"),
            "info",
            fenetre
        )

    tk.Button(
        zone_boutons,
        text=t("common.cancel"),
        command=fermer_popup,
        font=(POLICE, 9, "bold"),
        bg=theme["champ"],
        fg=theme["texte"],
        activebackground=theme["panneau_alt"],
        activeforeground=theme["texte"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    ).pack(
        side="left",
        fill="x",
        expand=True,
        padx=(0, 7),
        ipady=10
    )

    tk.Button(
        zone_boutons,
        text=t("admin.reset_all.button"),
        command=confirmer_reset_total,
        font=(POLICE, 9, "bold"),
        bg=theme["rouge"],
        fg=theme["blanc"],
        activebackground=theme["rouge"],
        activeforeground=theme["blanc"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    ).pack(
        side="left",
        fill="x",
        expand=True,
        padx=(7, 0),
        ipady=10
    )

    popup.protocol(
        "WM_DELETE_WINDOW",
        fermer_popup
    )

    popup.lift()
    popup.focus_force()


def reinitialiser_stock_standard_admin():
    """
    Réinitialise uniquement le stock concret local de la carrière active
    avec le profil STANDARD correspondant à l'appareil et à la période.

    Ne modifie jamais :
    - la base IL-2 ;
    - ammoQty ;
    - la référence de synchronisation ammoQty ;
    - les boosts ;
    - les livraisons ;
    - les directives ;
    - les rapports.
    """
    if not mode_admin_actif():
        dialogue_message_custom(
            t("admin.required.title"),
            t("admin.required.body"),
            "info",
            fenetre
        )
        return

    avion = DONNEES_CARRIERE_IL2.get(
        "avion",
        avion_selectionne
    )

    annee, mois = extraire_annee_mois_carriere(
        DONNEES_CARRIERE_IL2
    )

    noms_mois = {
        1: "JANVIER",
        2: "FÉVRIER",
        3: "MARS",
        4: "AVRIL",
        5: "MAI",
        6: "JUIN",
        7: "JUILLET",
        8: "AOÛT",
        9: "SEPTEMBRE",
        10: "OCTOBRE",
        11: "NOVEMBRE",
        12: "DÉCEMBRE"
    }

    popup = tk.Toplevel(
        fenetre
    )

    appliquer_chrome_custom(
        popup,
        t("admin.reset_stock.window"),
        700,
        500,
        popup.destroy
    )

    popup.transient(
        fenetre
    )

    popup.grab_set()

    fond = tk.Frame(
        popup,
        bg=theme["panneau"]
    )

    fond.pack(
        fill="both",
        expand=True
    )

    tk.Label(
        fond,
        text=t("options.admin.reset_standard"),
        font=(POLICE, 15, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(28, 8)
    )

    tk.Label(
        fond,
        text=t("admin.reset_stock.description"),
        font=(POLICE, 9),
        justify="center",
        wraplength=590,
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        padx=40,
        pady=(6, 16)
    )

    cadre_infos = tk.Frame(
        fond,
        bg=theme["panneau_alt"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    cadre_infos.pack(
        fill="x",
        padx=55,
        pady=(0, 16)
    )

    tk.Label(
        cadre_infos,
        text=t(
            "admin.reset_stock.summary",
            aircraft=avion,
            period=f"{t_mois(mois)} {annee}"
        ),
        font=(POLICE, 10, "bold"),
        justify="center",
        bg=theme["panneau_alt"],
        fg=theme["texte"]
    ).pack(
        pady=16
    )

    tk.Label(
        fond,
        text=t("admin.reset_stock.body"),
        font=(POLICE, 9),
        justify="center",
        wraplength=590,
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        padx=45,
        pady=(0, 20)
    )

    zone_boutons = tk.Frame(
        fond,
        bg=theme["panneau"]
    )

    zone_boutons.pack(
        fill="x",
        padx=55,
        pady=(4, 28)
    )

    def fermer_popup():
        try:
            popup.grab_release()
        except Exception:
            pass

        popup.destroy()

    def confirmer_reset():
        nouvelles_valeurs = calculer_stock_initial_standard_carriere(
            avion,
            DONNEES_CARRIERE_IL2
        )

        try:
            stock_engine.remplacer_stock_local(
                FICHIER_BASE,
                nouvelles_valeurs
            )

        except Exception as erreur:
            dialogue_message_custom(
                t("common.error"),
                t("admin.reset_stock.fail_body", error=str(erreur)),
                "error",
                popup
            )
            return

        fermer_popup()

        try:
            rafraichir_interface_apres_synchro()
        except Exception:
            pass

        dialogue_message_custom(
            t("admin.reset_stock.success_title"),
            t("admin.reset_stock.success_body"),
            "info",
            fenetre
        )

    bouton_annuler = tk.Button(
        zone_boutons,
        text=t("common.cancel"),
        command=fermer_popup,
        font=(POLICE, 9, "bold"),
        bg=theme["champ"],
        fg=theme["texte"],
        activebackground=theme["panneau_alt"],
        activeforeground=theme["texte"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    )

    bouton_annuler.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(0, 7),
        ipady=9
    )

    bouton_confirmer = tk.Button(
        zone_boutons,
        text=t("admin.reset_stock.button"),
        command=confirmer_reset,
        font=(POLICE, 9, "bold"),
        bg=theme["rouge"],
        fg=theme["blanc"],
        activebackground=theme["rouge"],
        activeforeground=theme["blanc"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    )

    bouton_confirmer.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(7, 0),
        ipady=9
    )

    popup.protocol(
        "WM_DELETE_WINDOW",
        fermer_popup
    )

    popup.lift()
    popup.focus_force()



def modifier_stock_admin():
    if not mode_admin_actif():
        dialogue_message_custom(
            t("admin.required.title"),
            t("admin.required.body"),
            "info",
            fenetre
        )
        return

    dialogue = tk.Toplevel(
        fenetre
    )

    appliquer_chrome_custom(
        dialogue,
        t("admin.stock.window"),
        980,
        820,
        dialogue.destroy
    )

    fond = tk.Frame(
        dialogue,
        bg=theme["fond"]
    )

    fond.pack(
        fill="both",
        expand=True
    )

    tk.Label(
        fond,
        text=t("admin.stock.title"),
        font=(POLICE, 15, "bold"),
        bg=theme["fond"],
        fg=theme["texte"]
    ).pack(
        pady=(18, 4)
    )

    tk.Label(
        fond,
        text=t(
            "admin.stock.description",
            aircraft=DONNEES_CARRIERE_IL2.get("avion", avion_selectionne)
        ),
        font=(POLICE, 8),
        bg=theme["fond"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 12)
    )

    cadre = tk.Frame(
        fond,
        bg=theme["panneau"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    cadre.pack(
        fill="both",
        expand=True,
        padx=18,
        pady=(0, 10)
    )

    tk.Label(
        cadre,
        text=t("common.ammunition"),
        font=(POLICE, 8, "bold"),
        anchor="w",
        bg=theme["panneau_alt"],
        fg=theme["texte_faible"]
    ).place(
        x=14,
        y=0,
        width=710,
        height=36
    )

    tk.Label(
        cadre,
        text=t("common.stock"),
        font=(POLICE, 8, "bold"),
        anchor="e",
        bg=theme["panneau_alt"],
        fg=theme["texte_faible"]
    ).place(
        x=750,
        y=0,
        width=150,
        height=36
    )

    zone = tk.Frame(
        cadre,
        bg=theme["panneau"]
    )

    zone.place(
        x=8,
        y=44,
        relwidth=1.0,
        width=-16,
        relheight=1.0,
        height=-52
    )

    scrollbar = tk.Scrollbar(
        zone,
        orient="vertical"
    )

    scrollbar.pack(
        side="right",
        fill="y"
    )

    canvas = tk.Canvas(
        zone,
        bg=theme["panneau"],
        highlightthickness=0,
        yscrollcommand=scrollbar.set
    )

    canvas.pack(
        side="left",
        fill="both",
        expand=True
    )

    scrollbar.configure(
        command=canvas.yview
    )

    contenu = tk.Frame(
        canvas,
        bg=theme["panneau"]
    )

    item = canvas.create_window(
        0,
        0,
        window=contenu,
        anchor="nw"
    )

    contenu.bind(
        "<Configure>",
        lambda event:
        canvas.configure(
            scrollregion=(
                canvas.bbox(
                    "all"
                )
                or (
                    0,
                    0,
                    1,
                    1
                )
            )
        )
    )

    canvas.bind(
        "<Configure>",
        lambda event:
        canvas.itemconfig(
            item,
            width=event.width
        )
    )

    variables = {}

    avion_admin = DONNEES_CARRIERE_IL2.get(
        "avion",
        avion_selectionne
    )

    munitions_admin = trier_munitions_logiquement(
        AVIONS_EMPORTS.get(
            avion_admin,
            []
        )
    )

    if not munitions_admin:
        tk.Label(
            contenu,
            text=t("admin.stock.none", aircraft=avion_admin),
            font=(POLICE, 9, "bold"),
            bg=theme["panneau"],
            fg=theme["texte_faible"]
        ).pack(
            pady=30
        )

    for munition in munitions_admin:
        ligne = tk.Frame(
            contenu,
            height=46,
            bg=theme["panneau"],
            highlightbackground=theme["separateur"],
            highlightthickness=1
        )

        ligne.pack(
            fill="x",
            pady=1
        )

        ligne.pack_propagate(
            False
        )

        tk.Label(
            ligne,
            text=t_munition(munition),
            font=(POLICE, 8, "bold"),
            anchor="w",
            bg=theme["panneau"],
            fg=theme["texte"]
        ).place(
            x=10,
            y=0,
            width=700,
            height=46
        )

        variable = tk.StringVar(
            value=str(
                lire_stock_unitaire(
                    munition
                )
            )
        )

        variables[
            munition
        ] = variable

        entree = tk.Entry(
            ligne,
            textvariable=variable,
            justify="center",
            font=(POLICE, 9, "bold"),
            bg=theme["champ"],
            fg=theme["champ_texte"],
            insertbackground=theme["champ_texte"],
            relief="solid",
            borderwidth=1
        )

        entree.place(
            x=760,
            y=7,
            width=120,
            height=32
        )

    def enregistrer_stock_admin():
        nouvelles_valeurs = {}

        for munition, variable in variables.items():
            try:
                valeur = int(
                    variable.get().strip()
                )

                if valeur < 0:
                    raise ValueError

            except ValueError:
                dialogue_message_custom(
                    t("admin.stock.invalid_title"),
                    t(
                        "admin.stock.invalid_body",
                        munition=t_munition(munition)
                    ),
                    "error",
                    dialogue
                )
                return

            nouvelles_valeurs[
                munition
            ] = valeur

        confirmer = dialogue_message_custom(
            t("admin.stock.confirm_title"),
            t("admin.stock.confirm_body"),
            "question",
            dialogue
        )

        if not confirmer:
            return

        try:
            stock_engine.definir_quantites_stock(
                FICHIER_BASE,
                nouvelles_valeurs
            )

        except Exception as erreur:
            dialogue_message_custom(
                t("common.error"),
                str(
                    erreur
                ),
                "error",
                dialogue
            )
            return
        dialogue.destroy()

        try:
            rafraichir_interface_apres_synchro()
        except Exception:
            pass

        dialogue_message_custom(
            t("admin.stock.saved_title"),
            t("admin.stock.saved_body"),
            "info",
            fenetre
        )

    zone_boutons = tk.Frame(
        fond,
        height=58,
        bg=theme["fond"]
    )

    zone_boutons.pack(
        fill="x",
        padx=18,
        pady=(0, 14)
    )

    zone_boutons.pack_propagate(
        False
    )

    tk.Button(
        zone_boutons,
        text=t("admin.stock.save_button"),
        command=enregistrer_stock_admin,
        font=(POLICE, 9, "bold"),
        bg=theme["vert"],
        fg=theme["blanc"],
        activebackground=theme["vert"],
        activeforeground=theme["blanc"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    ).pack(
        side="right",
        fill="y",
        ipadx=25
    )

    lier_molette_recursivement(
        contenu,
        canvas
    )


# ============================================================
# OPTIONS
# ============================================================

def ouvrir_options():
    _debut_performance_ui = time.perf_counter()
    global fenetre_options_ouverte

    if (
        fenetre_options_ouverte is not None
        and fenetre_options_ouverte.winfo_exists()
    ):
        fenetre_options_ouverte.lift()
        fenetre_options_ouverte.focus_force()
        return

    fenetre_options = tk.Toplevel(
        fenetre
    )

    fenetre_options.after_idle(
        lambda debut=_debut_performance_ui:
        journaliser_performance_ui(
            'Options',
            debut
        )
    )

    fenetre_options_ouverte = fenetre_options

    def fermer_options_chrome():
        global fenetre_options_ouverte

        fenetre_options_ouverte = None
        fenetre_options.destroy()

    appliquer_chrome_custom(
        fenetre_options,
        t("options.title"),
        760,
        760,
        fermer_options_chrome
    )

    cadre_options = tk.Frame(
        fenetre_options,
        bg=theme["panneau"]
    )

    cadre_options.pack(
        fill="both",
        expand=True
    )

    scrollbar_options = tk.Scrollbar(
        cadre_options,
        orient="vertical"
    )

    scrollbar_options.pack(
        side="right",
        fill="y"
    )

    canvas_options = tk.Canvas(
        cadre_options,
        bg=theme["panneau"],
        highlightthickness=0,
        borderwidth=0,
        yscrollcommand=scrollbar_options.set
    )

    canvas_options.pack(
        side="left",
        fill="both",
        expand=True
    )

    scrollbar_options.configure(
        command=canvas_options.yview
    )

    contenu = tk.Frame(
        canvas_options,
        bg=theme["panneau"]
    )

    item = canvas_options.create_window(
        0,
        0,
        anchor="nw",
        window=contenu
    )

    contenu.bind(
        "<Configure>",
        lambda event:
        canvas_options.configure(
            scrollregion=canvas_options.bbox(
                "all"
            )
        )
    )

    canvas_options.bind(
        "<Configure>",
        lambda event:
        canvas_options.itemconfig(
            item,
            width=event.width
        )
    )

    tk.Label(
        contenu,
        text=t("options.title"),
        font=(POLICE, 18, "bold"),
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(26, 6)
    )

    tk.Label(
        contenu,
        text=t("options.appearance.title"),
        font=POLICE_SECTION,
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(10, 4)
    )

    tk.Label(
        contenu,
        text=t("options.appearance.description"),
        font=POLICE_PETIT,
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 12)
    )

    cadre_themes = tk.Frame(
        contenu,
        bg=theme["panneau"]
    )

    cadre_themes.pack(
        padx=55,
        fill="x"
    )

    cartes = {}

    for cle_theme, theme_carte in (
        ("clair", THEME_CLAIR),
        ("sombre", THEME_SOMBRE)
    ):
        cadre = tk.Frame(
            cadre_themes,
            bg=theme_carte["panneau"],
            highlightbackground=theme_carte["bordure"],
            highlightthickness=1,
            cursor="hand2"
        )

        cadre.pack(
            fill="x",
            pady=5
        )

        interieur = tk.Frame(
            cadre,
            bg=theme_carte["panneau"],
            cursor="hand2"
        )

        interieur.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=13
        )

        texte = tk.Label(
            interieur,
            text=t(
                f"options.appearance.theme.{cle_theme}"
            ),
            font=(POLICE, 10, "bold"),
            bg=theme_carte["panneau"],
            fg=theme_carte["texte"],
            cursor="hand2"
        )

        texte.pack(
            side="left"
        )

        statut = tk.Label(
            interieur,
            text="",
            font=(POLICE, 8, "bold"),
            bg=theme_carte["panneau"],
            fg=theme_carte["vert"],
            cursor="hand2"
        )

        statut.pack(
            side="right"
        )

        # Ces quatre widgets sont une PRÉVISUALISATION volontaire du
        # thème Clair/Sombre. Le moteur global de recoloration ne doit pas
        # les transformer avec le thème actif.
        for widget_preview in (
            cadre,
            interieur,
            texte,
            statut
        ):
            widget_preview._theme_preview_fixe = True

        cartes[
            cle_theme
        ] = {
            "cadre": cadre,
            "interieur": interieur,
            "texte": texte,
            "statut": statut,
            "theme": theme_carte
        }

    def actualiser_selection_theme():
        for cle, donnees in cartes.items():
            actif = (
                config["theme"] == cle
            )

            donnees[
                "statut"
            ].configure(
                text=(
                    t(
                        "common.active"
                    )
                    if actif
                    else ""
                )
            )

            donnees[
                "cadre"
            ].configure(
                highlightbackground=(
                    donnees[
                        "theme"
                    ][
                        "vert"
                    ]
                    if actif
                    else donnees[
                        "theme"
                    ][
                        "bordure"
                    ]
                ),
                highlightthickness=(
                    2
                    if actif
                    else 1
                )
            )

    def changer_theme_options(
        cle
    ):
        appliquer_theme(
            cle
        )

        actualiser_selection_theme()

        # appliquer_theme() repeint maintenant toute l'application.
        # On garde seulement la mise à jour des états dynamiques propres
        # au menu Options.
        actualiser_admin_options()

        fenetre_options.after_idle(
            lambda:
            ajuster_fenetre_custom_au_contenu(
                fenetre_options,
                marge_x=28,
                marge_y=32
            )
        )

    for cle, donnees in cartes.items():
        for widget in (
            donnees["cadre"],
            donnees["interieur"],
            donnees["texte"],
            donnees["statut"]
        ):
            widget.bind(
                "<Button-1>",
                lambda event, c=cle:
                changer_theme_options(
                    c
                )
            )

    # ========================================================
    # LANGUE
    # ========================================================

    separateur_langue = tk.Frame(
        contenu,
        height=1,
        bg=theme["separateur"]
    )

    separateur_langue.pack(
        fill="x",
        padx=55,
        pady=(22, 16)
    )

    tk.Label(
        contenu,
        text=t(
            "options.language.title"
        ),
        font=POLICE_SECTION,
        bg=theme["panneau"],
        fg=theme["texte"]
    ).pack(
        pady=(0, 5)
    )

    tk.Label(
        contenu,
        text=t(
            "options.language.description"
        ),
        font=POLICE_PETIT,
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 12)
    )

    cadre_langue = tk.Frame(
        contenu,
        bg=theme["panneau_alt"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    cadre_langue.pack(
        fill="x",
        padx=55
    )

    zone_langue = tk.Frame(
        cadre_langue,
        bg=theme["panneau_alt"]
    )

    zone_langue.pack(
        fill="x",
        padx=16,
        pady=(14, 8)
    )

    boutons_langue = {}

    label_note_langue = tk.Label(
        cadre_langue,
        text="",
        font=(POLICE, 7),
        justify="center",
        wraplength=590,
        bg=theme["panneau_alt"],
        fg=theme["texte_faible"]
    )

    label_note_langue.pack(
        padx=18,
        pady=(0, 14)
    )

    def actualiser_boutons_langue():
        langue_selectionnee = config.get(
            "langue",
            "en"
        )

        for cle, bouton in boutons_langue.items():
            selectionne = (
                cle == langue_selectionnee
            )

            bouton.configure(
                bg=(
                    theme["vert"]
                    if selectionne
                    else theme["champ"]
                ),
                fg=(
                    theme["blanc"]
                    if selectionne
                    else theme["texte"]
                )
            )

        label_note_langue.configure(
            text=t(
                (
                    "options.language.restart_pending"
                    if langue_selectionnee != langue_active()
                    else "options.language.restart"
                )
            )
        )

    def choisir_langue_options(
        cle
    ):
        if cle not in LANGUES_SUPPORTEES:
            return

        if config.get(
            "langue",
            "en"
        ) == cle:
            return

        config[
            "langue"
        ] = cle

        sauvegarder_config()

        # La session courante reste dans sa langue de démarrage.
        actualiser_boutons_langue()

    for cle in LANGUES_SUPPORTEES:
        bouton = tk.Button(
            zone_langue,
            text=t(
                f"options.language.{cle}"
            ),
            command=lambda c=cle:
            choisir_langue_options(
                c
            ),
            font=(POLICE, 8, "bold"),
            relief="solid",
            borderwidth=1,
            cursor="hand2"
        )

        bouton.pack(
            side="left",
            fill="x",
            expand=True,
            padx=3,
            ipady=7
        )

        boutons_langue[
            cle
        ] = bouton

    separateur_affichage = tk.Frame(
        contenu,
        height=1,
        bg=theme["separateur"]
    )

    separateur_affichage.pack(
        fill="x",
        padx=55,
        pady=(22, 16)
    )

    label_affichage_titre = tk.Label(
        contenu,
        text=t("options.display.title"),
        font=POLICE_SECTION,
        bg=theme["panneau"],
        fg=theme["texte"]
    )

    label_affichage_titre.pack(
        pady=(0, 5)
    )

    tk.Label(
        contenu,
        text=t("options.display.description"),
        font=POLICE_PETIT,
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(0, 12)
    )

    cadre_affichage = tk.Frame(
        contenu,
        bg=theme["panneau_alt"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    cadre_affichage.pack(
        fill="x",
        padx=55
    )

    tk.Label(
        cadre_affichage,
        text=t("options.display.text_size"),
        font=(POLICE, 8, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(14, 6)
    )

    zone_taille_police = tk.Frame(
        cadre_affichage,
        bg=theme["panneau_alt"]
    )

    zone_taille_police.pack(
        fill="x",
        padx=16,
        pady=(0, 14)
    )

    boutons_taille_police = {}

    def actualiser_boutons_taille_police():
        actif = config.get(
            "taille_police",
            "standard"
        )

        for cle, bouton in boutons_taille_police.items():
            selectionne = (
                cle == actif
            )

            bouton.configure(
                bg=(
                    theme["vert"]
                    if selectionne
                    else theme["champ"]
                ),
                fg=(
                    theme["blanc"]
                    if selectionne
                    else theme["texte"]
                )
            )

    def choisir_taille_police(
        cle
    ):
        if config.get(
            "taille_police",
            "standard"
        ) == cle:
            return

        config[
            "taille_police"
        ] = cle

        sauvegarder_config()

        appliquer_taille_police_globale()

        actualiser_boutons_taille_police()

    for cle in (
        "compact",
        "standard",
        "grand"
    ):
        bouton = tk.Button(
            zone_taille_police,
            text=t(
                f"options.display.profile.{cle}"
            ),
            command=lambda c=cle:
            choisir_taille_police(
                c
            ),
            font=(POLICE, 8, "bold"),
            relief="solid",
            borderwidth=1,
            cursor="hand2"
        )

        bouton.pack(
            side="left",
            fill="x",
            expand=True,
            padx=3,
            ipady=6
        )

        boutons_taille_police[
            cle
        ] = bouton

    tk.Label(
        cadre_affichage,
        text=t("options.display.windows_size"),
        font=(POLICE, 8, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte_faible"]
    ).pack(
        pady=(4, 6)
    )

    zone_taille_fenetres = tk.Frame(
        cadre_affichage,
        bg=theme["panneau_alt"]
    )

    zone_taille_fenetres.pack(
        fill="x",
        padx=16,
        pady=(0, 8)
    )

    boutons_taille_fenetres = {}

    def actualiser_boutons_taille_fenetres():
        actif = config.get(
            "taille_fenetres",
            "standard"
        )

        for cle, bouton in boutons_taille_fenetres.items():
            selectionne = (
                cle == actif
            )

            bouton.configure(
                bg=(
                    theme["vert"]
                    if selectionne
                    else theme["champ"]
                ),
                fg=(
                    theme["blanc"]
                    if selectionne
                    else theme["texte"]
                )
            )

    def choisir_taille_fenetres(
        cle
    ):
        # Cliquer à nouveau sur le profil déjà actif ne fait strictement
        # rien. Cela évite toute réapplication inutile.
        if config.get(
            "taille_fenetres",
            "standard"
        ) == cle:
            return

        config[
            "taille_fenetres"
        ] = cle

        sauvegarder_config()

        # Redimensionnement direct depuis la taille de base d'origine.
        # Aucun auto-size n'est relancé pendant ce changement.
        appliquer_taille_fenetres_ouvertes()

        actualiser_boutons_taille_fenetres()

    for cle in (
        "compact",
        "standard",
        "grand"
    ):
        bouton = tk.Button(
            zone_taille_fenetres,
            text=t(
                f"options.display.profile.{cle}"
            ),
            command=lambda c=cle:
            choisir_taille_fenetres(
                c
            ),
            font=(POLICE, 8, "bold"),
            relief="solid",
            borderwidth=1,
            cursor="hand2"
        )

        bouton.pack(
            side="left",
            fill="x",
            expand=True,
            padx=3,
            ipady=6
        )

        boutons_taille_fenetres[
            cle
        ] = bouton

    tk.Label(
        cadre_affichage,
        text=t("options.display.main_fixed"),
        font=(POLICE, 7),
        justify="center",
        wraplength=590,
        bg=theme["panneau_alt"],
        fg=theme["texte_faible"]
    ).pack(
        padx=18,
        pady=(0, 14)
    )

    separateur = tk.Frame(
        contenu,
        height=1,
        bg=theme["separateur"]
    )

    separateur.pack(
        fill="x",
        padx=55,
        pady=(22, 16)
    )

    label_admin_titre = tk.Label(
        contenu,
        text=t("options.admin.title"),
        font=POLICE_SECTION,
        bg=theme["panneau"],
        fg=theme["texte"]
    )

    label_admin_titre.pack(
        pady=(0, 5)
    )

    label_admin_description = tk.Label(
        contenu,
        text=t("options.admin.description"),
        font=POLICE_PETIT,
        justify="center",
        bg=theme["panneau"],
        fg=theme["texte_faible"]
    )

    label_admin_description.pack(
        pady=(0, 12)
    )

    cadre_admin = tk.Frame(
        contenu,
        bg=theme["panneau_alt"],
        highlightbackground=theme["bordure"],
        highlightthickness=1
    )

    cadre_admin.pack(
        fill="x",
        padx=55
    )

    label_admin_statut = tk.Label(
        cadre_admin,
        text="",
        font=(POLICE, 10, "bold"),
        bg=theme["panneau_alt"],
        fg=theme["texte"]
    )

    label_admin_statut.pack(
        pady=(15, 7)
    )

    bouton_admin = tk.Button(
        cadre_admin,
        text="",
        font=(POLICE, 9, "bold"),
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    )

    bouton_admin.pack(
        fill="x",
        padx=18,
        pady=(0, 12),
        ipady=7
    )

    tk.Label(
        cadre_admin,
        text=t(
            "options.admin.tools"
        ),
        font=(POLICE, 8),
        justify="left",
        anchor="w",
        bg=theme["panneau_alt"],
        fg=theme["texte_faible"]
    ).pack(
        fill="x",
        padx=22,
        pady=(0, 12)
    )

    zone_outils = tk.Frame(
        cadre_admin,
        bg=theme["panneau_alt"]
    )

    zone_outils.pack(
        fill="x",
        padx=18,
        pady=(0, 18)
    )

    bouton_stock_admin = tk.Button(
        zone_outils,
        text=t("options.admin.modify_stock"),
        command=modifier_stock_admin,
        font=(POLICE, 8, "bold"),
        relief="solid",
        borderwidth=1
    )

    bouton_stock_admin.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(0, 5),
        ipady=6
    )

    bouton_points_admin = tk.Button(
        zone_outils,
        text=t("options.admin.modify_points"),
        command=modifier_points_commandement_admin,
        font=(POLICE, 8, "bold"),
        relief="solid",
        borderwidth=1
    )

    bouton_points_admin.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(5, 0),
        ipady=6
    )

    bouton_gain_points_admin = tk.Button(
        cadre_admin,
        text=t("options.admin.daily_gain"),
        command=modifier_gain_points_commandement_admin,
        font=(POLICE, 8, "bold"),
        relief="solid",
        borderwidth=1
    )

    bouton_gain_points_admin.pack(
        fill="x",
        padx=18,
        pady=(0, 8),
        ipady=6
    )

    bouton_reset_stock_admin = tk.Button(
        cadre_admin,
        text=t("options.admin.reset_standard"),
        command=reinitialiser_stock_standard_admin,
        font=(POLICE, 8, "bold"),
        relief="solid",
        borderwidth=1
    )

    bouton_reset_stock_admin.pack(
        fill="x",
        padx=18,
        pady=(0, 8),
        ipady=7
    )

    bouton_reset_total_admin = tk.Button(
        cadre_admin,
        text=t("options.admin.reset_career"),
        command=reinitialiser_toute_carriere_admin,
        font=(POLICE, 8, "bold"),
        relief="solid",
        borderwidth=1
    )

    bouton_reset_total_admin.pack(
        fill="x",
        padx=18,
        pady=(0, 18),
        ipady=8
    )

    def basculer_admin_options():
        nouvel_etat = not mode_admin_actif()

        if nouvel_etat:
            confirmer = dialogue_message_custom(
                t(
                    "options.admin.confirm_title"
                ),
                t(
                    "options.admin.confirm_body"
                ),
                "question",
                fenetre_options
            )

            if not confirmer:
                return

        if definir_mode_admin(
            nouvel_etat
        ):
            actualiser_admin_options()

    bouton_admin.configure(
        command=basculer_admin_options
    )

    def actualiser_admin_options():
        actif = mode_admin_actif()

        label_admin_statut.configure(
            text=(
                t(
                    "options.admin.status_on"
                )
                if actif
                else t(
                    "options.admin.status_off"
                )
            ),
            fg=(
                theme["vert"]
                if actif
                else theme["texte_faible"]
            ),
            bg=theme["panneau_alt"]
        )

        bouton_admin.configure(
            text=(
                t(
                    "options.admin.disable"
                )
                if actif
                else t(
                    "options.admin.enable"
                )
            ),
            bg=(
                theme["rouge"]
                if actif
                else theme["champ"]
            ),
            fg=(
                theme["blanc"]
                if actif
                else theme["texte"]
            ),
            activebackground=(
                theme["rouge"]
                if actif
                else theme["panneau_alt"]
            ),
            activeforeground=(
                theme["blanc"]
                if actif
                else theme["texte"]
            )
        )

        for bouton in (
            bouton_stock_admin,
            bouton_points_admin,
            bouton_reset_stock_admin,
            bouton_reset_total_admin
        ):
            bouton.configure(
                state=(
                    "normal"
                    if actif
                    else "disabled"
                ),
                cursor=(
                    "hand2"
                    if actif
                    else "arrow"
                ),
                bg=(
                    theme["champ"]
                    if actif
                    else theme["panneau_alt"]
                ),
                fg=(
                    theme["texte"]
                    if actif
                    else theme["texte_faible"]
                ),
                disabledforeground=theme[
                    "texte_faible"
                ]
            )

    def defiler_options(
        event
    ):
        canvas_options.yview_scroll(
            int(
                -event.delta / 120
            ),
            "units"
        )

    canvas_options.bind(
        "<Enter>",
        lambda event:
        canvas_options.bind_all(
            "<MouseWheel>",
            defiler_options
        )
    )

    canvas_options.bind(
        "<Leave>",
        lambda event:
        canvas_options.unbind_all(
            "<MouseWheel>"
        )
    )

    def fermer_options():
        global fenetre_options_ouverte

        canvas_options.unbind_all(
            "<MouseWheel>"
        )

        fenetre_options_ouverte = None
        fenetre_options.destroy()

    fenetre_options.protocol(
        "WM_DELETE_WINDOW",
        fermer_options
    )

    tk.Button(
        contenu,
        text=t(
            "common.close"
        ),
        command=fermer_options,
        font=POLICE_PETIT,
        bg=theme["champ"],
        fg=theme["texte"],
        activebackground=theme["panneau_alt"],
        activeforeground=theme["texte"],
        relief="solid",
        borderwidth=1,
        cursor="hand2"
    ).pack(
        pady=(24, 34),
        ipadx=25,
        ipady=6
    )

    actualiser_selection_theme()
    actualiser_boutons_langue()
    actualiser_boutons_taille_police()
    actualiser_boutons_taille_fenetres()
    actualiser_admin_options()




# ============================================================
# BOUTONS BARRE BASSE
# ============================================================

bouton_mise_a_jour = tk.Button(
    barre_bas,
    text=t("main.update.button"),
    command=action_bouton_mise_a_jour,
    font=(POLICE, 9, "bold"),
    relief="flat",
    borderwidth=0,
    cursor="hand2"
)

bouton_mise_a_jour.place(
    x=1225,
    y=16,
    width=120,
    height=32
)

widgets_barre_bouton.append(
    bouton_mise_a_jour
)

actualiser_bouton_mise_a_jour()


bouton_options = tk.Button(
    barre_bas,
    text=t("common.options"),
    command=ouvrir_options,
    font=(POLICE, 11),
    relief="flat",
    borderwidth=0,
    cursor="hand2"
)

bouton_options.place(
    x=1360,
    y=16,
    width=105,
    height=32
)

widgets_barre_bouton.append(
    bouton_options
)


bouton_quitter = tk.Button(
    barre_bas,
    text=t("common.quit"),
    command=fenetre.destroy,
    font=(POLICE, 11, "bold"),
    relief="solid",
    borderwidth=1,
    cursor="hand2"
)

bouton_quitter.place(
    x=1475,
    y=14,
    width=100,
    height=36
)

widgets_barre_bouton.append(
    bouton_quitter
)


# ============================================================
# PREMIER AFFICHAGE
# ============================================================

changer_avion(
    avion_selectionne
)

appliquer_theme(
    config["theme"],
    sauvegarder=False
)

calculer_totaux()



# ============================================================
# SURVEILLANCE TEMPS RÉEL DE LA CARRIÈRE
# ============================================================

def _executer_rafraichissement_interface_securise():
    """
    Rafraîchissement UI exécuté hors du callback de synchronisation SQLite.

    Une erreur visuelle ne doit jamais annuler ou bloquer un ravitaillement
    déjà validé dans la base locale.
    """
    try:
        reconstruire_emport_selectionne()
    except Exception as erreur:
        journaliser_erreur_runtime(
            "Rafraîchissement emports après synchronisation",
            erreur
        )

    try:
        calculer_totaux()
    except Exception as erreur:
        journaliser_erreur_runtime(
            "Recalcul totaux après synchronisation",
            erreur
        )

    try:
        if (
            fenetre_stock_ouverte is not None
            and fenetre_stock_ouverte.winfo_exists()
        ):
            fenetre.after(
                150,
                rafraichir_fenetre_stock_ouverte
            )

    except Exception as erreur:
        journaliser_erreur_runtime(
            "Rafraîchissement fenêtre Stock",
            erreur
        )


def rafraichir_interface_apres_synchro():
    """
    Programme le rafraîchissement visuel une fois le callback courant terminé.

    Le moteur de stock n'attend donc jamais une reconstruction Tkinter.
    """
    try:
        fenetre.after_idle(
            _executer_rafraichissement_interface_securise
        )

    except Exception as erreur:
        journaliser_erreur_runtime(
            "Programmation rafraîchissement interface",
            erreur
        )

def rafraichir_fenetre_stock_ouverte():
    """
    Reconstruit proprement la fenêtre Stock hors du callback de surveillance.
    """
    global fenetre_stock_ouverte

    ancienne_fenetre = fenetre_stock_ouverte

    if (
        ancienne_fenetre is None
        or not ancienne_fenetre.winfo_exists()
    ):
        return


    # On libère uniquement les bindings appartenant à cette fenêtre.
    try:
        ancienne_fenetre.unbind_all(
            "<MouseWheel>"
        )
    except Exception:
        pass


    fenetre_stock_ouverte = None


    try:
        ancienne_fenetre.destroy()
    except Exception:
        return


    # On laisse Tk finir complètement la destruction avant de recréer.
    fenetre.after(
        250,
        ouvrir_stock_base
    )


def travailleur_lecture_carriere(chemin):
    """
    Thread secondaire : lecture SQLite uniquement.

    AUCUN appel Tkinter n'est effectué ici.
    """
    try:
        donnees = analyser_carriere_il2(
            chemin
        )

        file_surveillance_carriere.put(
            (
                "ok",
                donnees
            )
        )

    except Exception as erreur:
        file_surveillance_carriere.put(
            (
                "erreur",
                str(
                    erreur
                )
            )
        )


def lancer_lecture_carriere_arriere_plan():
    """
    Lance au maximum UNE lecture SQLite en arrière-plan.
    """
    global surveillance_carriere_en_cours

    if not surveillance_carriere_active:
        return

    if surveillance_carriere_en_cours:
        return


    chemin = DONNEES_CARRIERE_IL2.get(
        "fichier",
        ""
    )

    if not chemin:
        return


    surveillance_carriere_en_cours = True


    thread = threading.Thread(
        target=travailleur_lecture_carriere,
        args=(
            chemin,
        ),
        daemon=True
    )

    thread.start()


def traiter_resultats_surveillance():
    """
    Thread principal Tkinter : traite les lectures produites par le worker.

    Règle v0.9.51.10 :
    aucune erreur secondaire (UI, rapport, badge...) ne doit interrompre
    définitivement le watcher après réception d'un ravitaillement.
    """
    global DONNEES_CARRIERE_IL2
    global RESULTAT_SYNCHRO_CARRIERE
    global surveillance_carriere_en_cours
    global reference_ammo_temps_reel

    if not surveillance_carriere_active:
        return

    try:
        while True:
            try:
                (
                    type_resultat,
                    contenu
                ) = file_surveillance_carriere.get_nowait()

            except queue.Empty:
                break

            surveillance_carriere_en_cours = False

            try:
                if type_resultat != "ok":
                    print(
                        "Lecture carrière temporairement impossible :",
                        contenu
                    )
                    continue

                nouvelles_donnees = contenu

                ancien_avion = DONNEES_CARRIERE_IL2.get(
                    "avion"
                )

                nouvel_avion = nouvelles_donnees.get(
                    "avion"
                )

                # Changement d'appareil : chantier séparé.
                if (
                    ancien_avion is not None
                    and nouvel_avion is not None
                    and ancien_avion != nouvel_avion
                ):
                    print(
                        "Changement d'appareil détecté - "
                        "synchronisation ignorée pour l'instant."
                    )
                    continue

                nouvelle_valeur = int(
                    nouvelles_donnees.get(
                        "ammo_qty",
                        0
                    )
                )

                if reference_ammo_temps_reel is None:
                    reference_ammo_temps_reel = int(
                        DONNEES_CARRIERE_IL2.get(
                            "ammo_qty",
                            nouvelle_valeur
                        )
                    )

                ancienne_valeur = int(
                    reference_ammo_temps_reel
                )

                # Toujours conserver les données fraîches en mémoire.
                DONNEES_CARRIERE_IL2 = nouvelles_donnees

                try:
                    rafraichir_date_interface_depuis_carriere(
                        nouvelles_donnees
                    )
                except Exception as erreur:
                    journaliser_erreur_runtime(
                        "Mise à jour date carrière",
                        erreur
                    )

                try:
                    resultat_gain_points = (
                        actualiser_points_commandement_journaliers(
                            nouvelles_donnees
                        )
                    )

                    if (
                        resultat_gain_points.get(
                            "ajout_x10",
                            0
                        ) > 0
                    ):
                        actualiser_affichage_points_commandement_ouvert()

                except Exception as erreur:
                    journaliser_erreur_runtime(
                        "Gain journalier de points de commandement",
                        erreur
                    )

                try:
                    enregistrer_meta_carriere_locale(
                        nouvelles_donnees
                    )
                except Exception as erreur:
                    journaliser_erreur_runtime(
                        "Métadonnées carrière locale",
                        erreur
                    )

                # Les livraisons urgentes locales sont indépendantes de ammoQty.
                try:
                    livraison_recue = traiter_livraisons_urgentes(
                        nouvelles_donnees
                    )

                    if livraison_recue:
                        rafraichir_interface_apres_synchro()

                except Exception as erreur:
                    journaliser_erreur_runtime(
                        "Traitement livraisons urgentes",
                        erreur
                    )

                try:
                    mettre_a_jour_reference_capacite_carriere(
                        nouvelles_donnees
                    )
                except Exception as erreur:
                    journaliser_erreur_runtime(
                        "Mise à jour capacité carrière",
                        erreur
                    )

                if nouvelle_valeur == ancienne_valeur:
                    continue

                print(
                    "Evolution ammoQty détectée :",
                    ancienne_valeur,
                    "->",
                    nouvelle_valeur
                )

                # ------------------------------------------------
                # ÉTAPE CRITIQUE : STOCK + SNAPSHOT ATOMIQUES
                # ------------------------------------------------
                try:
                    RESULTAT_SYNCHRO_CARRIERE = (
                        appliquer_delta_carriere_temps_reel(
                            nouvelles_donnees,
                            ancienne_valeur,
                            nouvelle_valeur
                        )
                    )

                except Exception as erreur:
                    journaliser_erreur_runtime(
                        "Application delta ammoQty",
                        erreur
                    )

                    # La référence mémoire reste inchangée.
                    # Le prochain contrôle pourra retenter.
                    continue

                # Le backend est maintenant au nouvel ammoQty, y compris si le
                # delta avait déjà été appliqué lors d'un passage précédent.
                reference_ammo_temps_reel = nouvelle_valeur

                # ------------------------------------------------
                # ÉTAPES SECONDAIRES : JAMAIS BLOQUANTES
                # ------------------------------------------------
                rafraichir_interface_apres_synchro()

                if (
                    RESULTAT_SYNCHRO_CARRIERE
                    and RESULTAT_SYNCHRO_CARRIERE.get(
                        "type_changement",
                        "aucun"
                    )
                    not in (
                        "aucun",
                        "deja_applique"
                    )
                ):
                    try:
                        enregistrer_rapport_carriere(
                            nouvelles_donnees,
                            RESULTAT_SYNCHRO_CARRIERE
                        )

                    except Exception as erreur:
                        journaliser_erreur_runtime(
                            "Enregistrement rapport de ravitaillement",
                            erreur
                        )

            except Exception as erreur:
                # Une erreur imprévue sur UN résultat ne doit jamais tuer
                # le polling complet.
                journaliser_erreur_runtime(
                    "Traitement résultat watcher carrière",
                    erreur
                )

    finally:
        # Même après une exception, le polling Tkinter continue.
        if surveillance_carriere_active:
            try:
                fenetre.after(
                    250,
                    traiter_resultats_surveillance
                )

            except Exception as erreur:
                journaliser_erreur_runtime(
                    "Reprogrammation watcher carrière",
                    erreur
                )

def cycle_lecture_carriere():
    """
    Lance une nouvelle lecture environ toutes les 4 secondes.
    Si le worker précédent travaille encore, ce cycle est simplement sauté.
    """
    if not surveillance_carriere_active:
        return

    lancer_lecture_carriere_arriere_plan()

    fenetre.after(
        INTERVALLE_SURVEILLANCE_CARRIERE_MS,
        cycle_lecture_carriere
    )


def demarrer_surveillance_carriere():
    """
    Initialise la référence et démarre :
    - le worker périodique SQLite ;
    - le polling léger de la queue côté Tkinter.
    """
    global reference_ammo_temps_reel

    reference_ammo_temps_reel = int(
        DONNEES_CARRIERE_IL2.get(
            "ammo_qty",
            0
        )
    )

    cycle_lecture_carriere()

    fenetre.after(
        250,
        traiter_resultats_surveillance
    )


# ============================================================
# LANCEMENT
# ============================================================

if (
    RESULTAT_SYNCHRO_CARRIERE
    and RESULTAT_SYNCHRO_CARRIERE.get(
        "type_changement"
    ) != "aucun"
):
    enregistrer_rapport_carriere(
        DONNEES_CARRIERE_IL2,
        RESULTAT_SYNCHRO_CARRIERE
    )


# Initialise le badge des rapports persistants.
actualiser_badge_rapports()


# Surveillance robuste : SQLite en arrière-plan, interface jamais bloquée.
demarrer_surveillance_carriere()


# Mise à jour : polling Tk léger + vérification GitHub silencieuse au démarrage.
fenetre.after(
    250,
    traiter_resultats_mise_a_jour
)

fenetre.after(
    1800,
    lambda:
    demarrer_verification_mise_a_jour(
        manuelle=False,
        parent=fenetre
    )
)


# Applique le profil de texte mémorisé une fois toute l'interface créée.
fenetre.after_idle(
    appliquer_taille_police_globale
)

fenetre.after(
    120,
    adapter_boxes_fenetre_principale
)

# Dernière passe après la construction complète : capture les coordonnées
# de base de tous les widgets puis applique le facteur du moniteur courant.
fenetre.after(
    180,
    adapter_fenetre_principale_ecran
)


fenetre.mainloop()
