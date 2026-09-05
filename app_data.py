"""Données et logique pure de l'application IL-2 Korea Stock Manager.

Extrait de interface.py sans changement fonctionnel pour le refactor pré-1.0.
Ce module ne dépend ni de Tkinter, ni d'une base de carrière, ni des chemins locaux.
"""

MUNITIONS = {
    "Roquette aérienne semi-perforante à haute vitesse HVAR 5\"": {
        "icone": "hvar_ap.png"
    },
    "Roquette aérienne à haute vitesse HVAR 5\"": {
        "icone": "hvar.png"
    },
    "Réservoir de napalm 110 gal": {
        "icone": "napalm_110.png"
    },
    "Réservoir largable 110 gal": {
        "icone": "tank_110.png"
    },
    "Réservoir largable 75 gal": {
        "icone": "tank_75.png"
    },
    "AN-M64A1 500 lb": {
        "icone": "anm64_500.png"
    },
    "AN-M65A1 1000 lb": {
        "icone": "anm65_1000.png"
    },
    "Bombe éclairante à parachute AN-M26A1": {
        "icone": "anm26a1_flare.png"
    },
    "M26A2 500 lb à sous-munitions": {
        "icone": "m26a2_cluster.png"
    },
    "M29A1 500 lb à sous-munitions": {
        "icone": "m29a1_cluster.png"
    },
    "Roquette ATAR 6,5\"": {
        "icone": "atar_65.png"
    },
    "AN-M57A1 250 lb": {
        "icone": "anm57_250.png"
    },
    "AN-M88 220 lb à fragmentation": {
        "icone": "anm88_220.png"
    },
    "Réservoir largable 165 gal": {
        "icone": "tank_165.png"
    },
    "Réservoir largable 265 gal": {
        "icone": "tank_265.png"
    },
    "Roquette Tiny Tim 12\"": {
        "icone": "tiny_tim_12.png"
    },
    "Réservoir largable 230 gal": {
        "icone": "tank_230.png"
    },
    "Réservoir largable 120 gal": {
        "icone": "tank_120.png"
    },
    "Réservoir largable 245 gal": {
        "icone": "tank_245.png"
    },
    "M-13UK 132 mm": {
        "icone": "m13uk_132.png"
    },
    "M-8 82 mm": {
        "icone": "m8_82.png"
    },
    "PTAB-10-2.5": {
        "icone": "ptab_10_25.png"
    },
    "PTAB-2,5-1,5": {
        "icone": "ptab_25_15.png"
    },
    "SAB-100-55": {
        "icone": "sab_100_55.png"
    },
    "AO-10sc": {
        "icone": "ao_10sc.png"
    },
    "AO-2,5sc": {
        "icone": "ao_25sc.png"
    },
    "AO-25sl": {
        "icone": "ao_25sl.png"
    },
    "FAB-100sc": {
        "icone": "fab_100sc.png"
    },
    "FAB-250 M43": {
        "icone": "fab_250_m43.png"
    },
    "FAB-50sc": {
        "icone": "fab_50sc.png"
    },
    "Réservoir largable 250 L": {
        "icone": "tank_250l.png"
    }
}

AVIONS_EMPORTS = {
    "F-51D": [
        "Roquette aérienne semi-perforante à haute vitesse HVAR 5\"",
        "Roquette aérienne à haute vitesse HVAR 5\"",
        "Réservoir de napalm 110 gal",
        "Réservoir largable 110 gal",
        "Réservoir largable 75 gal",
        "AN-M64A1 500 lb",
        "AN-M65A1 1000 lb",
        "Bombe éclairante à parachute AN-M26A1",
        "M26A2 500 lb à sous-munitions",
        "M29A1 500 lb à sous-munitions",
        "Roquette ATAR 6,5\""
    ],

    "F-80C-10": [
        "M29A1 500 lb à sous-munitions",
        "Roquette aérienne à haute vitesse HVAR 5\"",
        "Réservoir de napalm 110 gal",
        "Réservoir largable 165 gal",
        "Réservoir largable 265 gal",
        "AN-M57A1 250 lb",
        "AN-M64A1 500 lb",
        "AN-M65A1 1000 lb",
        "AN-M88 220 lb à fragmentation",
        "Bombe éclairante à parachute AN-M26A1",
        "M26A2 500 lb à sous-munitions"
    ],

    "F-84E": [
        "M29A1 500 lb à sous-munitions",
        "Roquette Tiny Tim 12\"",
        "Roquette aérienne à haute vitesse HVAR 5\"",
        "Réservoir de napalm 110 gal",
        "Réservoir largable 230 gal",
        "AN-M57A1 250 lb",
        "AN-M64A1 500 lb",
        "AN-M65A1 1000 lb",
        "AN-M88 220 lb à fragmentation",
        "Bombe éclairante à parachute AN-M26A1",
        "M26A2 500 lb à sous-munitions"
    ],

    "F-86A-5": [
        "Réservoir de napalm 110 gal",
        "Réservoir largable 120 gal",
        "Réservoir largable 245 gal",
        "AN-M64A1 500 lb",
        "AN-M65A1 1000 lb",
        "Bombe éclairante à parachute AN-M26A1",
        "M26A2 500 lb à sous-munitions",
        "M29A1 500 lb à sous-munitions",
        "Roquette aérienne à haute vitesse HVAR 5\""
    ],

    "IL-10": [
        "M-13UK 132 mm",
        "M-8 82 mm",
        "PTAB-10-2.5",
        "PTAB-2,5-1,5",
        "SAB-100-55",
        "AO-10sc",
        "AO-2,5sc",
        "AO-25sl",
        "FAB-100sc",
        "FAB-250 M43",
        "FAB-50sc"
    ],

    "MiG-15bis": [
        "FAB-100sc",
        "Réservoir largable 250 L",
        "SAB-100-55"
    ],

    "Yak-9P": [],
    "La-11": []
}

PARAMETRES_RAVITAILLEMENT_DEFAUT = {
    "capacite_depot": 7500.0,
    "budget_hebdo": 900.0,
    "variation": 0.12,
    "modificateur_global": 1.00,
    "coef_bombes": 1.00,
    "coef_roquettes": 1.00,
    "coef_reservoirs": 1.00,
    "coef_special": 1.00
}

DISPONIBILITE_SPECIFIQUE = {
    "AN-M57A1 250 lb": 1.15,
    "AN-M64A1 500 lb": 1.25,
    "AN-M65A1 1000 lb": 0.82,
    "AN-M88 220 lb à fragmentation": 0.92,

    "Roquette aérienne à haute vitesse HVAR 5\"": 1.08,
    "Roquette aérienne semi-perforante à haute vitesse HVAR 5\"": 0.88,
    "Roquette Tiny Tim 12\"": 0.28,
    "Roquette ATAR 6,5\"": 0.42,

    "Réservoir de napalm 110 gal": 0.55,
    "Bombe éclairante à parachute AN-M26A1": 0.48,
    "M26A2 500 lb à sous-munitions": 0.58,
    "M29A1 500 lb à sous-munitions": 0.62,

    "M-13UK 132 mm": 0.82,
    "M-8 82 mm": 0.95,
    "PTAB-10-2.5": 0.62,
    "PTAB-2,5-1,5": 0.70,
    "SAB-100-55": 0.52,
    "AO-10sc": 0.72,
    "AO-2,5sc": 0.76,
    "AO-25sl": 0.68,

    "FAB-50sc": 1.10,
    "FAB-100sc": 1.08,
    "FAB-250 M43": 0.95
}

COUT_LOGISTIQUE_SPECIFIQUE = {
    "AN-M57A1 250 lb": 1.0,
    "AN-M64A1 500 lb": 1.8,
    "AN-M65A1 1000 lb": 3.0,
    "AN-M88 220 lb à fragmentation": 0.9,

    "Roquette aérienne à haute vitesse HVAR 5\"": 0.70,
    "Roquette aérienne semi-perforante à haute vitesse HVAR 5\"": 0.78,
    "Roquette Tiny Tim 12\"": 2.50,
    "Roquette ATAR 6,5\"": 1.15,

    "Réservoir de napalm 110 gal": 2.10,
    "Bombe éclairante à parachute AN-M26A1": 1.20,
    "M26A2 500 lb à sous-munitions": 2.00,
    "M29A1 500 lb à sous-munitions": 2.00,

    "M-13UK 132 mm": 0.85,
    "M-8 82 mm": 0.45,
    "PTAB-10-2.5": 1.40,
    "PTAB-2,5-1,5": 1.20,
    "SAB-100-55": 1.10,
    "AO-10sc": 1.00,
    "AO-2,5sc": 1.00,
    "AO-25sl": 1.00,

    "FAB-50sc": 0.55,
    "FAB-100sc": 0.85,
    "FAB-250 M43": 1.45
}

def categorie_logistique(nom):
    texte = nom.lower()

    if (
        "réservoir" in texte
        or "reservoir" in texte
    ):
        return "Réservoirs"

    if (
        "roquette" in texte
        or nom.startswith("M-13")
        or nom.startswith("M-8")
    ):
        return "Roquettes"

    if (
        "sous-munitions" in texte
        or "napalm" in texte
        or "éclairante" in texte
        or nom.startswith("PTAB")
        or nom.startswith("AO-")
        or nom.startswith("SAB-")
    ):
        return "Spécial"

    return "Bombes"

def cout_logistique(nom):
    if nom in COUT_LOGISTIQUE_SPECIFIQUE:
        return COUT_LOGISTIQUE_SPECIFIQUE[nom]

    categorie = categorie_logistique(nom)

    if categorie == "Réservoirs":
        return 1.50

    if categorie == "Roquettes":
        return 0.75

    if categorie == "Spécial":
        return 1.40

    return 1.20

def disponibilite_logistique(nom):
    return DISPONIBILITE_SPECIFIQUE.get(
        nom,
        0.90
    )

def stock_cible_logistique(nom):
    categorie = categorie_logistique(nom)

    if categorie == "Roquettes":
        cible = 160

    elif categorie == "Réservoirs":
        cible = 55

    elif categorie == "Spécial":
        cible = 45

    else:
        cible = 120

    # Les matériels rares ont volontairement un stock-cible plus faible.
    dispo = disponibilite_logistique(nom)

    if dispo < 0.45:
        cible = int(cible * 0.45)

    elif dispo < 0.70:
        cible = int(cible * 0.70)

    return max(
        10,
        cible
    )

def cle_coefficient_categorie(categorie):
    return {
        "Bombes": "coef_bombes",
        "Roquettes": "coef_roquettes",
        "Réservoirs": "coef_reservoirs",
        "Spécial": "coef_special"
    }[categorie]

def trier_munitions_logiquement(liste_munitions):
    """
    Ordre d'affichage global pour tous les avions :

    1. Roquettes
    2. Bombes
    3. Réservoirs
    4. Spécial

    A l'intérieur d'une même famille, tri alphabétique.
    """
    ordre_categories = {
        "Roquettes": 0,
        "Bombes": 1,
        "Réservoirs": 2,
        "Napalm": 3,
        "Spécial": 4
    }

    return sorted(
        liste_munitions,
        key=lambda nom: (
            ordre_categories.get(
                categorie_affichage_munition(nom),
                99
            ),
            nom.lower()
        )
    )

NOMS_MOIS = {
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

PROFILS_SIMULATION = {
    "STANDARD": {
        "nom_affiche": "STANDARD",
        "description": (
            "Flux logistique équilibré pour une campagne normale."
        ),
        "budget_hebdo": 900.0,
        "capacite_depot": 7500.0,
        "variation": 0.12,
        "modificateur_global": 1.00,
        "priorites": {
            "Bombes": 1.00,
            "Roquettes": 1.00,
            "Réservoirs": 1.00,
            "Spécial": 1.00
        }
    },

    "CONTRAINT": {
        "nom_affiche": "CONTRAINT",
        "description": (
            "Ravitaillement réduit et plus irrégulier."
        ),
        "budget_hebdo": 650.0,
        "capacite_depot": 7000.0,
        "variation": 0.20,
        "modificateur_global": 0.84,
        "priorites": {
            "Bombes": 1.00,
            "Roquettes": 0.82,
            "Réservoirs": 0.92,
            "Spécial": 0.70
        }
    },

    "OFFENSIVE": {
        "nom_affiche": "OFFENSIVE",
        "description": (
            "Flux renforcé pour une phase opérationnelle soutenue."
        ),
        "budget_hebdo": 1250.0,
        "capacite_depot": 8500.0,
        "variation": 0.10,
        "modificateur_global": 1.15,
        "priorites": {
            "Bombes": 1.18,
            "Roquettes": 1.22,
            "Réservoirs": 1.02,
            "Spécial": 1.08
        }
    }
}

COEFFICIENT_GLOBAL_MOIS_DEFAUT = {
    1: 0.84,
    2: 0.88,
    3: 0.94,
    4: 1.00,
    5: 1.06,
    6: 1.10,
    7: 1.08,
    8: 1.05,
    9: 1.00,
    10: 0.96,
    11: 0.90,
    12: 0.85
}

COEFFICIENT_CATEGORIE_MOIS_DEFAUT = {
    1:  {"Bombes": 0.92, "Roquettes": 0.86, "Réservoirs": 1.00, "Spécial": 0.88},
    2:  {"Bombes": 0.94, "Roquettes": 0.90, "Réservoirs": 1.00, "Spécial": 0.90},
    3:  {"Bombes": 0.98, "Roquettes": 0.96, "Réservoirs": 1.00, "Spécial": 0.95},
    4:  {"Bombes": 1.00, "Roquettes": 1.00, "Réservoirs": 1.00, "Spécial": 1.00},
    5:  {"Bombes": 1.05, "Roquettes": 1.08, "Réservoirs": 1.00, "Spécial": 1.03},
    6:  {"Bombes": 1.08, "Roquettes": 1.12, "Réservoirs": 1.02, "Spécial": 1.06},
    7:  {"Bombes": 1.08, "Roquettes": 1.10, "Réservoirs": 1.02, "Spécial": 1.05},
    8:  {"Bombes": 1.05, "Roquettes": 1.08, "Réservoirs": 1.02, "Spécial": 1.04},
    9:  {"Bombes": 1.02, "Roquettes": 1.02, "Réservoirs": 1.00, "Spécial": 1.00},
    10: {"Bombes": 0.98, "Roquettes": 0.96, "Réservoirs": 1.00, "Spécial": 0.96},
    11: {"Bombes": 0.94, "Roquettes": 0.90, "Réservoirs": 1.00, "Spécial": 0.92},
    12: {"Bombes": 0.90, "Roquettes": 0.84, "Réservoirs": 1.00, "Spécial": 0.86}
}

def construire_modele_avance_defaut(cle_profil):
    profil = PROFILS_SIMULATION.get(
        cle_profil,
        PROFILS_SIMULATION["STANDARD"]
    )

    modele = {
        "profil": cle_profil,
        "budget_hebdo": float(profil["budget_hebdo"]),
        "capacite_depot": float(profil["capacite_depot"]),
        "variation": float(profil["variation"]),
        "modificateur_global": float(profil["modificateur_global"]),
        "priorites": dict(profil["priorites"]),
        "mois": {},
        "munitions": {}
    }

    for numero in range(1, 13):
        modele["mois"][str(numero)] = {
            "global": float(
                COEFFICIENT_GLOBAL_MOIS_DEFAUT[numero]
            ),
            "categories": dict(
                COEFFICIENT_CATEGORIE_MOIS_DEFAUT[numero]
            )
        }

    for nom in MUNITIONS:
        modele["munitions"][nom] = {
            "disponibilite": float(
                disponibilite_logistique(nom)
            ),
            "stock_cible": int(
                stock_cible_logistique(nom)
            ),
            "cout_logistique": float(
                cout_logistique(nom)
            ),
            "mois": {
                str(numero): 1.0
                for numero in range(1, 13)
            }
        }

    return modele

CLE_MODELE_LOGISTIQUE = "STANDARD"

PALETTES_STOCK = {
    "Bombes": [
        "#8f4f48",
        "#a95f52",
        "#be7665",
        "#7a433d",
        "#c68c7c",
        "#96584d",
        "#b96e5d",
        "#824a43"
    ],

    "Roquettes": [
        "#47758c",
        "#5f8fa7",
        "#6fa2ba",
        "#3d6478",
        "#82b1c6",
        "#527f95",
        "#35586b",
        "#749aad"
    ],

    "Réservoirs": [
        "#5f775c",
        "#708a69",
        "#829c79",
        "#4d644b",
        "#91aa86",
        "#687f61",
        "#789070",
        "#566e52"
    ],

    "Napalm": [
        "#c8a83e",
        "#d7b94d",
        "#b9962f"
    ],

    "Spécial": [
        "#9a7a4e",
        "#a68a62",
        "#8c6c50",
        "#8b7182",
        "#9a8090",
        "#7d7464",
        "#a58e72",
        "#75687c"
    ]
}

def categorie_affichage_munition(nom_munition):
    """
    Catégorie purement VISUELLE.

    Le napalm est volontairement séparé des réservoirs de carburant.
    Cela ne modifie pas le moteur logistique interne.
    """
    if "napalm" in nom_munition.lower():
        return "Napalm"

    return categorie_logistique(
        nom_munition
    )

def couleur_munition_stock(nom_munition, index_dans_categorie):
    categorie = categorie_affichage_munition(
        nom_munition
    )

    palette = PALETTES_STOCK.get(
        categorie,
        ["#808080"]
    )

    return palette[
        index_dans_categorie
        % len(palette)
    ]

THEME_CLAIR = {
    "nom": "STYLE IL-2 KOREA CLAIR",
    "fond": "#d8d2c7",
    "panneau": "#eeeae2",
    "panneau_alt": "#e6e1d7",
    "barre": "#171914",
    "texte": "#4b4943",
    "texte_faible": "#777269",
    "bordure": "#8d887e",
    "contour_fenetre": "#777268",
    "separateur": "#b6b0a6",
    "champ": "#f8f5ef",
    "champ_texte": "#383630",
    "bleu": "#769db5",
    "rouge": "#b75b55",
    "vert": "#6e9470",
    "blanc": "#f2f0ea"
}

THEME_SOMBRE = {
    "nom": "STYLE IL-2 KOREA SOMBRE",
    "fond": "#242620",
    "panneau": "#30322b",
    "panneau_alt": "#393b33",
    "barre": "#151611",
    "texte": "#ddd8cd",
    "texte_faible": "#a49f94",
    "bordure": "#696b61",
    "contour_fenetre": "#85877c",
    "separateur": "#55584f",
    "champ": "#3b3d35",
    "champ_texte": "#eee9dd",
    "bleu": "#7ea2b8",
    "rouge": "#bd6b62",
    "vert": "#879f79",
    "blanc": "#f1eee5"
}

THEMES = {
    "clair": THEME_CLAIR,
    "sombre": THEME_SOMBRE
}

CONFIG_DEFAUT = {
    "theme": "clair",
    "avion": "F-51D",
    "profil_simulation": "STANDARD",
    "carriere_fichier": "",
    "carriere_id": "",
    "base_carriere_locale": "",
    "preparation_mission": {},
    "mode_admin": False,
    "taille_police": "standard",
    "taille_fenetres": "standard",
    "langue": "en"
}

MAPPING_CONFIG_AVIONS_IL2 = {
    "f51d": "F-51D",
    "f80c": "F-80C-10",
    "f80c10": "F-80C-10",
    "f84e": "F-84E",
    "f86a5": "F-86A-5",
    "f86a": "F-86A-5",
    "mig15bis": "MiG-15bis",
    "mig15": "MiG-15bis",
    "la11": "La-11",
    "yak9p": "Yak-9P",
    "il10": "IL-10"
}

