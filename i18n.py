"""Couche légère d’internationalisation de l’interface.

Aucune logique métier ne doit vivre ici. Le français est toujours le secours.
"""

from locales.fr import TEXTES as TEXTES_FR
from locales.en import TEXTES as TEXTES_EN

LANGUES_SUPPORTEES = ("fr", "en")
CATALOGUES = {"fr": TEXTES_FR, "en": TEXTES_EN}
_LANGUE_ACTIVE = "fr"


MUNITION_TRANSLATION_KEYS = {
    'Roquette aérienne semi-perforante à haute vitesse HVAR 5"': 'munition.m01',
    'Roquette aérienne à haute vitesse HVAR 5"': 'munition.m02',
    'Réservoir de napalm 110 gal': 'munition.m03',
    'Réservoir largable 110 gal': 'munition.m04',
    'Réservoir largable 75 gal': 'munition.m05',
    'AN-M64A1 500 lb': 'munition.m06',
    'AN-M65A1 1000 lb': 'munition.m07',
    'Bombe éclairante à parachute AN-M26A1': 'munition.m08',
    'M26A2 500 lb à sous-munitions': 'munition.m09',
    'M29A1 500 lb à sous-munitions': 'munition.m10',
    'Roquette ATAR 6,5"': 'munition.m11',
    'AN-M57A1 250 lb': 'munition.m12',
    'AN-M88 220 lb à fragmentation': 'munition.m13',
    'Réservoir largable 165 gal': 'munition.m14',
    'Réservoir largable 265 gal': 'munition.m15',
    'Roquette Tiny Tim 12"': 'munition.m16',
    'Réservoir largable 230 gal': 'munition.m17',
    'Réservoir largable 120 gal': 'munition.m18',
    'Réservoir largable 245 gal': 'munition.m19',
    'M-13UK 132 mm': 'munition.m20',
    'M-8 82 mm': 'munition.m21',
    'PTAB-10-2.5': 'munition.m22',
    'PTAB-2,5-1,5': 'munition.m23',
    'SAB-100-55': 'munition.m24',
    'AO-10sc': 'munition.m25',
    'AO-2,5sc': 'munition.m26',
    'AO-25sl': 'munition.m27',
    'FAB-100sc': 'munition.m28',
    'FAB-250 M43': 'munition.m29',
    'FAB-50sc': 'munition.m30',
    'Réservoir largable 250 L': 'munition.m31',
}



MONTH_TRANSLATION_KEYS = {i: f"month.{i}" for i in range(1, 13)}

PRIORITY_TRANSLATION_KEYS = {
    "TRÈS ÉLEVÉE": "priority.critical",
    "ÉLEVÉE": "priority.strong",
    "NORMALE": "priority.normal",
    "FAIBLE": "priority.low",
    "TRÈS FAIBLE": "priority.rare",
    "INDISPONIBLE": "priority.unavailable",
}

DELIVERY_SIZE_TRANSLATION_KEYS = {
    "PETITE": "delivery.small",
    "GRANDE": "delivery.large",
}

DELIVERY_STATUS_TRANSLATION_KEYS = {
    "LIVREE": "delivery.delivered",
    "LIVRÉE": "delivery.delivered",
    "EN_TRANSIT": "delivery.in_transit",
    "EN TRANSIT": "delivery.in_transit",
}

CATEGORY_TRANSLATION_KEYS = {
    "Bombes": "category.bombs",
    "Roquettes": "category.rockets",
    "Réservoirs": "category.tanks",
    "Napalm": "category.napalm",
    "Spécial": "category.special",
}

def normaliser_langue(langue):
    code = str(langue or "").strip().lower()
    return code if code in LANGUES_SUPPORTEES else "fr"

def definir_langue(langue):
    global _LANGUE_ACTIVE
    _LANGUE_ACTIVE = normaliser_langue(langue)
    return _LANGUE_ACTIVE

def langue_active():
    return _LANGUE_ACTIVE

def t(cle, **variables):
    cle = str(cle)
    catalogue = CATALOGUES.get(_LANGUE_ACTIVE, TEXTES_FR)
    texte = catalogue.get(cle)
    if texte is None:
        texte = TEXTES_FR.get(cle, cle)
    if variables:
        try:
            texte = texte.format(**variables)
        except (KeyError, ValueError):
            pass
    return texte

def t_munition(nom):
    """Traduit uniquement le nom affiché ; la clé interne reste inchangée."""
    nom = str(nom)
    cle = MUNITION_TRANSLATION_KEYS.get(nom)
    return t(cle) if cle else nom


def t_categorie(categorie):
    """Traduit une catégorie d'affichage sans modifier sa valeur métier."""
    categorie = str(categorie)
    cle = CATEGORY_TRANSLATION_KEYS.get(categorie)
    return t(cle) if cle else categorie



def t_mois(mois):
    try:
        numero = int(mois)
    except (TypeError, ValueError):
        return str(mois)
    cle = MONTH_TRANSLATION_KEYS.get(numero)
    return t(cle) if cle else str(mois)


def t_priorite(niveau):
    niveau = str(niveau)
    cle = PRIORITY_TRANSLATION_KEYS.get(niveau)
    return t(cle) if cle else niveau


def t_taille_livraison(taille):
    taille = str(taille).upper()
    cle = DELIVERY_SIZE_TRANSLATION_KEYS.get(taille)
    return t(cle) if cle else str(taille)


def t_statut_livraison(statut):
    statut = str(statut).upper()
    cle = DELIVERY_STATUS_TRANSLATION_KEYS.get(statut)
    return t(cle) if cle else str(statut)


def verifier_catalogues():
    reference = set(TEXTES_FR)
    resultat = {"reference": len(reference), "langues": {}, "ok": True}
    for langue in LANGUES_SUPPORTEES:
        cles = set(CATALOGUES[langue])
        manquantes = sorted(reference - cles)
        supplementaires = sorted(cles - reference)
        resultat["langues"][langue] = {"cles": len(cles), "manquantes": manquantes, "supplementaires": supplementaires}
        if manquantes or supplementaires:
            resultat["ok"] = False
    return resultat
