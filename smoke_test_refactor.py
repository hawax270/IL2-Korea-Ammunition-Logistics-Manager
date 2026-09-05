"""Smoke tests non-GUI du refactor pré-1.0 v0.9.53.

Ce fichier ne lance pas Tkinter et ne touche à aucune carrière réelle.
"""

import sqlite3
import ast
import tempfile
from pathlib import Path

import app_data
import career_reader
import local_database
import stock_engine
import i18n
import updater


def verifier_catalogue():
    assert len(app_data.MUNITIONS) == 31
    assert set(app_data.AVIONS_EMPORTS) == {
        "F-51D", "F-80C-10", "F-84E", "F-86A-5",
        "MiG-15bis", "La-11", "Yak-9P", "IL-10",
    }
    for avion, emports in app_data.AVIONS_EMPORTS.items():
        assert len(emports) == len(set(emports)), f"Doublon dans {avion}"
        for munition in emports:
            assert munition in app_data.MUNITIONS, (avion, munition)


def verifier_i18n():
    resultat = i18n.verifier_catalogues()
    assert resultat["ok"]
    assert resultat["langues"]["fr"]["cles"] == resultat["langues"]["en"]["cles"]
    assert resultat["langues"]["fr"]["manquantes"] == []
    assert resultat["langues"]["en"]["manquantes"] == []

    i18n.definir_langue("fr")
    assert i18n.t("main.title") == "MENU PRINCIPAL"

    i18n.definir_langue("en")
    assert i18n.t("main.title") == "MAIN MENU"
    assert i18n.t("app.title") == "AMMUNITION STOCK MANAGEMENT"
    assert i18n.t("main.mission.title") == "MISSION PREPARATION"
    assert i18n.t("stock.window.title") == "AIRBASE STOCK"
    assert i18n.t_munition('Réservoir largable 110 gal') == '110 gal drop tank'
    assert i18n.t_categorie('Roquettes') == 'ROCKETS'

    assert i18n.definir_langue("xx") == "fr"
    assert i18n.t("main.title") == "MENU PRINCIPAL"
    assert i18n.t_munition('Réservoir largable 110 gal') == 'Réservoir largable 110 gal'
    assert i18n.t_categorie('Roquettes') == 'ROQUETTES'
    assert i18n.t("__cle_inconnue_test__") == "__cle_inconnue_test__"
    assert app_data.CONFIG_DEFAUT["langue"] == "en"




def verifier_chargement_carriere_systematique_v0959():
    source = Path(__file__).with_name("interface.py").read_text(
        encoding="utf-8"
    )

    assert 'VERSION_APPLICATION = "v1.1.0"' in source
    assert "def afficher_chargement_carriere(" in source
    assert "duree_minimale=5.0" in source
    assert 'name="chargement-carriere"' in source
    assert "threading.Thread(" in source
    assert "file_resultat = queue.Queue(maxsize=1)" in source
    assert "def charger_carriere_demarrage():" in source
    assert "RESULTATS_CHARGEMENT_CARRIERE = afficher_chargement_carriere(" in source
    assert "def afficher_initialisation_nouvelle_carriere(" not in source
    assert "duree = 3.0" not in source




def verifier_centrage_chargement_v09591():
    source = Path(__file__).with_name(
        "interface.py"
    ).read_text(
        encoding="utf-8"
    )

    debut = source.index(
        "def afficher_chargement_carriere("
    )
    fin = source.index(
        "# ============================================================\n# INITIALISATION",
        debut
    )

    bloc = source[
        debut:fin
    ]

    assert "popup.withdraw()" in bloc
    assert "popup.deiconify()" in bloc
    assert "geometrie_centree =" in bloc

    assert bloc.count(
        "popup.geometry(\n        geometrie_centree"
    ) == 2

    assert 'popup.attributes("-topmost", True)' not in bloc




def verifier_anglais_par_defaut_v09592():
    source_interface = Path(__file__).with_name(
        "interface.py"
    ).read_text(
        encoding="utf-8"
    )

    source_app_data = Path(__file__).with_name(
        "app_data.py"
    ).read_text(
        encoding="utf-8"
    )

    assert 'VERSION_APPLICATION = "v1.1.0"' in source_interface
    assert '"langue": "en"' in source_app_data

    assert 'resultat[\n                "langue"\n            ] = "en"' in source_interface

    assert 'config.get(\n        "langue",\n        "en"\n    )' in source_interface

    # Le français reste bien disponible.
    assert "fr" in i18n.LANGUES_SUPPORTEES
    assert "en" in i18n.LANGUES_SUPPORTEES

    i18n.definir_langue("en")
    assert i18n.t("main.title") == "MAIN MENU"

    i18n.definir_langue("fr")
    assert i18n.t("main.title") == "MENU PRINCIPAL"




def verifier_career_linked_v09593():
    source = Path(__file__).with_name(
        "interface.py"
    ).read_text(
        encoding="utf-8"
    )

    assert 'VERSION_APPLICATION = "v1.1.0"' in source
    assert 'anchor="center"' in source
    assert 'f"{nom_avion}  •  "' in source

    # Plus d'alignement manuel avec une longue série d'espaces.
    assert 'f"                         • {t(\'main.aircraft.linked\')}"' not in source
    assert '"                                      ▼"' not in source




def verifier_donnees_utilisateur_localappdata_v101():
    source = Path(__file__).with_name(
        "interface.py"
    ).read_text(
        encoding="utf-8"
    )

    assert 'VERSION_APPLICATION = "v1.1.0"' in source
    assert 'os.environ.get(' in source
    assert '"LOCALAPPDATA"' in source
    assert '/ "hawax270"' in source
    assert '/ "IL2 Korea Ammunition Logistics Manager"' in source

    assert 'DOSSIER_CARRIERES = DOSSIER_DONNEES / "careers"' in source
    assert 'FICHIER_CONFIG = DOSSIER_DONNEES / "config.json"' in source
    assert 'DOSSIER_LOGS = DOSSIER_DONNEES / "logs"' in source
    assert 'FICHIER_BASE_HERITAGE = DOSSIER_DONNEES / "stock.db"' in source

    assert "def migrer_donnees_utilisateur_legacy():" in source
    assert 'ancien_config = DOSSIER / "config.json"' in source
    assert 'ancien_dossier_carrieres = DOSSIER / "careers"' in source
    assert 'ancien_dossier_logs = DOSSIER / "logs"' in source

    # Le vieux runtime ne doit plus être défini directement dans DOSSIER.
    assert 'DOSSIER_CARRIERES = DOSSIER / "careers"' not in source
    assert 'FICHIER_CONFIG = DOSSIER / "config.json"' not in source
    assert 'DOSSIER_LOGS = DOSSIER / "logs"' not in source




def verifier_updater_github_v102():
    assert updater.GITHUB_OWNER == "hawax270"
    assert updater.GITHUB_REPOSITORY == "IL2-Korea-Ammunition-Logistics-Manager"

    assert updater.normaliser_version("v1.0.2") == (
        1,
        0,
        2,
        0
    )

    assert updater.version_plus_recente(
        "v1.0.2",
        "v1.0.1"
    )

    assert not updater.version_plus_recente(
        "v1.0.1",
        "v1.0.2"
    )

    faux_release = {
        "tag_name": "v1.0.2",
        "assets": [
            {
                "name": "source.zip",
                "browser_download_url": (
                    "https://github.com/hawax270/"
                    "IL2-Korea-Ammunition-Logistics-Manager/"
                    "releases/download/v1.0.2/source.zip"
                ),
                "size": 1,
            },
            {
                "name": "IL2_Korea_ALM_Setupv1.0.2.exe",
                "browser_download_url": (
                    "https://github.com/hawax270/"
                    "IL2-Korea-Ammunition-Logistics-Manager/"
                    "releases/download/v1.0.2/"
                    "IL2_Korea_ALM_Setupv1.0.2.exe"
                ),
                "size": 42000000,
            },
        ],
    }

    asset = updater.extraire_asset_installeur(
        faux_release
    )

    assert asset["name"] == (
        "IL2_Korea_ALM_Setupv1.0.2.exe"
    )

    source = Path(__file__).with_name(
        "interface.py"
    ).read_text(
        encoding="utf-8"
    )

    assert 'VERSION_APPLICATION = "v1.1.0"' in source
    assert "import updater" in source
    assert "def demarrer_verification_mise_a_jour(" in source
    assert "def demarrer_telechargement_mise_a_jour(" in source
    assert "def traiter_resultats_mise_a_jour():" in source
    assert 'name="github-update-check"' in source
    assert 'name="github-update-download"' in source
    assert "main.update.button" in source
    assert "def action_bouton_mise_a_jour():" in source
    assert "def actualiser_bouton_mise_a_jour():" in source
    assert "info_mise_a_jour_disponible" in source
    assert "options.update.check" not in source
    assert "1800" in source
    assert "manuelle=False" in source


def verifier_logistique():
    modele = app_data.construire_modele_avance_defaut("STANDARD")
    assert modele["profil"] == "STANDARD"
    assert len(modele["mois"]) == 12
    assert len(modele["munitions"]) == len(app_data.MUNITIONS)
    assert app_data.categorie_logistique("Roquette aérienne à haute vitesse HVAR 5\"") == "Roquettes"
    assert app_data.categorie_affichage_munition("Réservoir de napalm 110 gal") == "Napalm"


def verifier_lecture_carriere():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "Pilote Test, 12e FBS USAF(2).db"
        con = sqlite3.connect(db)
        con.executescript(
            """
            CREATE TABLE plane (id INTEGER, config TEXT, squadronId INTEGER, isDeleted INTEGER);
            CREATE TABLE squadron (id INTEGER, ammoQty INTEGER, isDeleted INTEGER);
            CREATE TABLE supply (
                id INTEGER, supplyNum INTEGER, scheduled TEXT, status INTEGER,
                statusDate TEXT, quantity INTEGER, isDeleted INTEGER,
                squadronId INTEGER, type INTEGER
            );
            CREATE TABLE career (
                id INTEGER, cuid TEXT, personageId TEXT,
                currentDate TEXT, currentTime TEXT, isDeleted INTEGER
            );
            INSERT INTO squadron VALUES (1, 777, 0);
            INSERT INTO plane VALUES (1, 'luascripts/worldobjects/planes/f51d.txt', 1, 0);
            INSERT INTO supply VALUES (10, 2, '1951.04.15 08:00:00', 1, '', 120, 0, 1, 4);
            INSERT INTO career VALUES (1, 'TEST-CUID', 'P1', '1951.04.13', '1951.04.13 08:32:00', 0);
            """
        )
        con.commit()
        con.close()

        donnees = career_reader.analyser_carriere_il2(db)
        assert donnees["avion"] == "F-51D"
        assert donnees["ammo_qty"] == 777
        assert donnees["date_jeu"] == "1951.04.13"
        assert donnees["career_cuid"] == "TEST-CUID"
        assert donnees["nom_escadrille"] == "12e FBS USAF"
        assert donnees["total_ravitaillements_munitions"] == 120

        assert career_reader.extraire_nom_escadrille_depuis_fichier(
            "Mehdi Krouri, 12e FBS USAF(2).db"
        ) == "12e FBS USAF"
        assert career_reader.extraire_nom_escadrille_depuis_fichier(
            "LA11 test, 4e IAP PLAAF.db"
        ) == "4e IAP PLAAF"
        assert career_reader.extraire_nom_escadrille_depuis_fichier(
            "carriere_sans_escadrille.db"
        ) == ""

        date = career_reader.lire_date_carriere_il2(db)
        assert date.startswith("1951.04.13")

        ro = career_reader.connexion_sqlite_lecture_seule(db)
        try:
            try:
                ro.execute("CREATE TABLE interdit(x INTEGER)")
            except sqlite3.Error:
                pass
            else:
                raise AssertionError("La connexion carrière n'est pas read-only")
        finally:
            ro.close()




def verifier_base_locale():
    with tempfile.TemporaryDirectory() as tmp:
        racine = Path(tmp)
        dossier_carrieres = racine / "careers"
        heritage = racine / "stock.db"
        source_carriere = racine / "Pilote Test, 12e FBS USAF.db"
        source_carriere.touch()

        donnees = {
            "fichier": str(source_carriere),
            "career_cuid": "CAREER-TEST-001",
            "career_personage_id": "P1",
            "avion": "F-51D",
        }

        # Identité et chemin par carrière.
        assert local_database.obtenir_identifiant_carriere(
            donnees
        ) == "CAREER-TEST-001"

        assert local_database.nom_fichier_carriere_locale(
            "CAREER:TEST/001"
        ) == "CAREER_TEST_001"

        assert not local_database.base_locale_carriere_existe(
            donnees,
            dossier_carrieres
        )

        fichier_base, migration = (
            local_database.configurer_base_locale_carriere(
                donnees,
                dossier_carrieres,
                heritage,
                ""
            )
        )

        assert migration is False
        assert fichier_base.name == "CAREER-TEST-001.db"

        # Création complète du schéma.
        local_database.initialiser_base(
            fichier_base
        )

        assert fichier_base.exists()

        con = sqlite3.connect(
            fichier_base
        )

        tables = {
            ligne[0]
            for ligne in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        tables_attendues = {
            "munitions",
            "missions",
            "presets",
            "ravitaillement_parametres",
            "ravitaillements",
            "modeles_simulation",
            "carriere_sync",
            "rapports_carriere",
            "capacite_carriere",
            "preferences_repartition",
            "commandement_etat",
            "livraisons_urgentes",
            "boosts_commandement",
            "directives_standard_commandement",
            "directives_standard_priorites",
            "priorites_repartition_mensuelles",
            "niveaux_repartition",
            "niveaux_repartition_periodes",
            "affectations_repartition",
            "profils_repartition",
            "standard_repartition_mensuelle",
        }

        assert tables_attendues.issubset(
            tables
        )

        assert con.execute(
            "SELECT valeur FROM commandement_etat WHERE cle='points_commandement'"
        ).fetchone()[0] == 1

        assert con.execute(
            "SELECT valeur FROM commandement_etat WHERE cle='gain_points_journalier_x10'"
        ).fetchone()[0] == 10

        assert con.execute(
            "SELECT COUNT(*) FROM munitions"
        ).fetchone()[0] >= len(
            app_data.MUNITIONS
        )

        con.close()

        # Métadonnées.
        local_database.enregistrer_meta_carriere_locale(
            fichier_base,
            donnees
        )

        con = sqlite3.connect(
            fichier_base
        )

        meta = dict(
            con.execute(
                "SELECT cle, valeur FROM carriere_locale_meta"
            ).fetchall()
        )

        con.close()

        assert meta["career_id"] == "CAREER-TEST-001"
        assert meta["avion_derniere_lecture"] == "F-51D"

        # Presets d'emport.
        contenu = {
            "AN-M64A1 500 lb": 2
        }

        local_database.enregistrer_preset(
            fichier_base,
            "F-51D",
            "TEST",
            contenu
        )

        assert local_database.charger_noms_presets(
            fichier_base,
            "F-51D"
        ) == ["TEST"]

        assert local_database.charger_preset(
            fichier_base,
            "F-51D",
            "TEST"
        ) == contenu

        local_database.supprimer_preset_bdd(
            fichier_base,
            "F-51D",
            "TEST"
        )

        assert local_database.charger_noms_presets(
            fichier_base,
            "F-51D"
        ) == []

        # Paramètres logistiques.
        params = local_database.lire_parametres_ravitaillement(
            fichier_base
        )

        assert set(
            app_data.PARAMETRES_RAVITAILLEMENT_DEFAUT
        ).issubset(
            params
        )

        local_database.enregistrer_parametres_ravitaillement(
            fichier_base,
            {
                "budget_hebdo": 1234.0,
                "cle_inconnue": 999,
            }
        )

        params = local_database.lire_parametres_ravitaillement(
            fichier_base
        )

        assert params["budget_hebdo"] == 1234.0
        assert "cle_inconnue" not in params

        # État usine d'une carrière neuve.
        con = sqlite3.connect(
            fichier_base
        )

        con.execute(
            """
            INSERT INTO missions (
                date_heure, avion, nombre_avions, armement
            )
            VALUES ('01.01.1951 - 10:00', 'F-51D', 1, 'test')
            """
        )

        con.execute(
            """
            UPDATE commandement_etat
            SET valeur = 7
            WHERE cle='points_commandement'
            """
        )

        con.commit()
        con.close()

        local_database.appliquer_valeurs_usine_nouvelle_carriere(
            fichier_base,
            "vTEST"
        )

        con = sqlite3.connect(
            fichier_base
        )

        assert con.execute(
            "SELECT COUNT(*) FROM missions"
        ).fetchone()[0] == 0

        assert con.execute(
            "SELECT valeur FROM commandement_etat WHERE cle='points_commandement'"
        ).fetchone()[0] == 1

        meta = dict(
            con.execute(
                "SELECT cle, valeur FROM carriere_locale_meta"
            ).fetchall()
        )

        assert meta["version_application_initiale"] == "vTEST"

        con.close()

        # Isolation de deux carrières.
        donnees_b = dict(
            donnees
        )

        donnees_b[
            "career_cuid"
        ] = "CAREER-TEST-002"

        fichier_b, _ = local_database.configurer_base_locale_carriere(
            donnees_b,
            dossier_carrieres,
            heritage,
            ""
        )

        local_database.initialiser_base(
            fichier_b
        )

        assert fichier_b != fichier_base

        con_a = sqlite3.connect(
            fichier_base
        )

        con_b = sqlite3.connect(
            fichier_b
        )

        con_a.execute(
            """
            UPDATE munitions
            SET stock = 111
            WHERE nom='AN-M64A1 500 lb'
            """
        )

        con_b.execute(
            """
            UPDATE munitions
            SET stock = 222
            WHERE nom='AN-M64A1 500 lb'
            """
        )

        con_a.commit()
        con_b.commit()
        con_a.close()
        con_b.close()

        assert local_database.lire_stock_unitaire(
            fichier_base,
            "AN-M64A1 500 lb"
        ) == 111

        assert local_database.lire_stock_unitaire(
            fichier_b,
            "AN-M64A1 500 lb"
        ) == 222




def verifier_points_commandement_journaliers():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "points.db"

        local_database.initialiser_base(
            base
        )

        # Une nouvelle DB démarre désormais avec 1 point.
        assert local_database.lire_points_commandement_x10(
            base
        ) == 10

        # Premier jour : référence initialisée, aucun cadeau rétroactif.
        jour_1 = 712000

        resultat = local_database.actualiser_points_commandement_journaliers(
            base,
            jour_1
        )

        assert resultat["ajout_x10"] == 0
        assert resultat["points_x10"] == 10

        # Trois jours plus tard à +1 pt/jour = +3 points.
        resultat = local_database.actualiser_points_commandement_journaliers(
            base,
            jour_1 + 3
        )

        assert resultat["jours_ajoutes"] == 3
        assert resultat["ajout_x10"] == 30
        assert resultat["points_x10"] == 40

        # Passage à 0,5 pt/jour.
        local_database.definir_gain_points_journalier_x10(
            base,
            5
        )

        resultat = local_database.actualiser_points_commandement_journaliers(
            base,
            jour_1 + 5
        )

        assert resultat["jours_ajoutes"] == 2
        assert resultat["ajout_x10"] == 10
        assert resultat["points_x10"] == 50

        # On place explicitement le solde à 54 pts pour tester un débit de 10.
        local_database.definir_points_commandement_x10(
            base,
            540
        )

        # Débit 10 pts -> 44.
        con = sqlite3.connect(
            base
        )

        con.execute(
            "BEGIN IMMEDIATE"
        )

        ok, restant = local_database.debiter_points_commandement_transaction(
            con.cursor(),
            10,
            gratuit=False
        )

        assert ok
        assert restant == 44.0

        con.commit()
        con.close()

        assert local_database.lire_points_commandement_x10(
            base
        ) == 440

        # 0,1 pt/jour conserve bien la décimale.
        local_database.definir_gain_points_journalier_x10(
            base,
            1
        )

        resultat = local_database.actualiser_points_commandement_journaliers(
            base,
            jour_1 + 6
        )

        assert resultat["points_x10"] == 441

        # Recul de sauvegarde : jamais de retrait.
        resultat = local_database.actualiser_points_commandement_journaliers(
            base,
            jour_1 + 2
        )

        assert resultat["points_x10"] == 441
        assert resultat["ajout_x10"] == 0

        # Toutes les valeurs admin prévues sont autorisées.
        for gain_x10 in (
            1,
            5,
            10,
            20,
            30,
        ):
            assert local_database.definir_gain_points_journalier_x10(
                base,
                gain_x10
            ) == gain_x10


def verifier_migration_usine_points_existants():
    """
    Une carrière déjà existante doit être recalée UNE SEULE FOIS à 1 point
    lors du passage à la nouvelle version usine.
    """
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "ancienne_carriere.db"

        local_database.initialiser_base(
            base
        )

        con = sqlite3.connect(
            base
        )

        # Simule une ancienne carrière avant version usine 3.
        con.execute(
            "DELETE FROM commandement_etat"
        )

        con.execute(
            """
            INSERT INTO commandement_etat (
                cle,
                valeur
            )
            VALUES (
                'points_commandement',
                50
            )
            """
        )

        con.execute(
            """
            INSERT INTO commandement_etat (
                cle,
                valeur
            )
            VALUES (
                'points_commandement_x10',
                500
            )
            """
        )

        con.execute(
            """
            INSERT INTO commandement_etat (
                cle,
                valeur
            )
            VALUES (
                'gain_points_journalier_x10',
                30
            )
            """
        )

        con.commit()
        con.close()

        # Premier accès de la nouvelle version -> usine : 1 point / +1 jour.
        assert local_database.lire_points_commandement_x10(
            base
        ) == 10

        assert local_database.lire_gain_points_journalier_x10(
            base
        ) == 10

        # Après la migration, une modification manuelle doit rester.
        local_database.definir_points_commandement_x10(
            base,
            425
        )

        assert local_database.lire_points_commandement_x10(
            base
        ) == 425

        # Même chose pour le taux admin : pas de reset à chaque lecture.
        local_database.definir_gain_points_journalier_x10(
            base,
            5
        )

        assert local_database.lire_gain_points_journalier_x10(
            base
        ) == 5

        con = sqlite3.connect(
            base
        )

        version = con.execute(
            """
            SELECT valeur
            FROM commandement_etat
            WHERE cle = 'version_usine_points_commandement'
            """
        ).fetchone()[0]

        con.close()

        assert version == local_database.VERSION_USINE_POINTS_COMMANDEMENT

def verifier_ordre_demarrage_ravitaillement():
    """
    Phase 2B :
    l'interface ne contient plus le moteur SQLite de synchronisation.
    Elle conserve uniquement les wrappers historiques avant le premier appel.
    """
    source_interface = (
        Path(__file__).with_name(
            "interface.py"
        ).read_text(
            encoding="utf-8"
        )
    )

    source_moteur = (
        Path(__file__).with_name(
            "stock_engine.py"
        ).read_text(
            encoding="utf-8"
        )
    )

    position_sync_initiale = source_interface.index(
        "RESULTAT_SYNCHRO_CARRIERE = ("
    )

    position_wrapper = source_interface.index(
        "def synchroniser_stock_avec_carriere("
    )

    assert position_wrapper < position_sync_initiale

    bloc_wrapper = source_interface[
        position_wrapper:
        source_interface.index(
            "\ndef ",
            position_wrapper + 5
        )
    ]

    assert "stock_engine.synchroniser_stock_avec_carriere(" in bloc_wrapper

    # Le moteur métier doit rester indépendant de Tkinter et de la langue.
    assert "import tkinter" not in source_moteur
    assert "from tkinter" not in source_moteur
    assert "import i18n" not in source_moteur
    assert "from i18n" not in source_moteur


def verifier_stock_engine_phase2b():
    """
    Scénario fonctionnel complet du moteur extrait :
    initialisation -> ravitaillement -> baisse ammoQty -> delta à chaud
    -> anti-double-application -> mission -> stock insuffisant.
    """
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(
            tmp
        ) / "stock_engine.db"

        local_database.initialiser_base(
            base
        )

        con = sqlite3.connect(
            base
        )

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS test_calcul_side_effect (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                etape TEXT NOT NULL
            )
            """
        )

        con.commit()
        con.close()

        munition_a = app_data.AVIONS_EMPORTS[
            "F-51D"
        ][
            0
        ]

        munition_b = app_data.AVIONS_EMPORTS[
            "F-51D"
        ][
            1
        ]

        appels = {
            "initial": 0,
            "repartition": 0
        }

        def effet_sqlite(
            etape
        ):
            # Ce callback ouvre sa PROPRE connexion et écrit.
            # Il reproduit le comportement du STANDARD mensuel.
            connexion = sqlite3.connect(
                base,
                timeout=1.0
            )

            connexion.execute(
                """
                INSERT INTO test_calcul_side_effect (
                    etape
                )
                VALUES (?)
                """,
                (
                    etape,
                )
            )

            connexion.commit()
            connexion.close()

        def calcul_initial(
            avion,
            donnees
        ):
            appels[
                "initial"
            ] += 1

            effet_sqlite(
                "initial"
            )

            assert avion == "F-51D"

            return {
                munition_a: 10,
                munition_b: 5
            }

        def calcul_repartition(
            avion,
            ammo_qty,
            donnees
        ):
            appels[
                "repartition"
            ] += 1

            effet_sqlite(
                "repartition"
            )

            assert avion == "F-51D"
            assert int(
                ammo_qty
            ) > 0

            return {
                munition_a: 3
            }

        carriere = {
            "career_cuid": "PHASE2B-TEST",
            "fichier": str(
                Path(
                    tmp
                ) / "Career Test.db"
            ),
            "avion": "F-51D",
            "ammo_qty": 100
        }

        # 1. Initialisation.
        resultat = stock_engine.synchroniser_stock_avec_carriere(
            base,
            carriere,
            calculer_stock_initial=calcul_initial,
            calculer_repartition=calcul_repartition
        )

        assert resultat[
            "type_changement"
        ] == "initialisation"

        assert local_database.lire_stock_unitaire(
            base,
            munition_a
        ) == 10

        assert local_database.lire_stock_unitaire(
            base,
            munition_b
        ) == 5

        # 2. Aucun changement : aucun recalcul.
        resultat = stock_engine.synchroniser_stock_avec_carriere(
            base,
            carriere,
            calculer_stock_initial=calcul_initial,
            calculer_repartition=calcul_repartition
        )

        assert resultat[
            "type_changement"
        ] == "aucun"

        assert appels[
            "initial"
        ] == 1

        # 3. Ravitaillement positif.
        carriere_120 = dict(
            carriere
        )

        carriere_120[
            "ammo_qty"
        ] = 120

        resultat = stock_engine.synchroniser_stock_avec_carriere(
            base,
            carriere_120,
            calculer_stock_initial=calcul_initial,
            calculer_repartition=calcul_repartition
        )

        assert resultat[
            "type_changement"
        ] == "augmentation"

        assert resultat[
            "delta"
        ] == 20

        assert local_database.lire_stock_unitaire(
            base,
            munition_a
        ) == 13

        assert local_database.lire_stock_unitaire(
            base,
            munition_b
        ) == 5

        # 4. Baisse ammoQty : référence seulement, stock concret inchangé.
        carriere_90 = dict(
            carriere
        )

        carriere_90[
            "ammo_qty"
        ] = 90

        resultat = stock_engine.synchroniser_stock_avec_carriere(
            base,
            carriere_90,
            calculer_stock_initial=calcul_initial,
            calculer_repartition=calcul_repartition
        )

        assert resultat[
            "type_changement"
        ] == "diminution_reference"

        assert local_database.lire_stock_unitaire(
            base,
            munition_a
        ) == 13

        assert local_database.lire_stock_unitaire(
            base,
            munition_b
        ) == 5

        # 5. Delta positif à chaud.
        carriere_100 = dict(
            carriere
        )

        carriere_100[
            "ammo_qty"
        ] = 100

        resultat = stock_engine.appliquer_delta_carriere_temps_reel(
            base,
            carriere_100,
            90,
            100,
            calculer_repartition=calcul_repartition
        )

        assert resultat[
            "type_changement"
        ] == "augmentation"

        assert local_database.lire_stock_unitaire(
            base,
            munition_a
        ) == 16

        # 6. Même delta rejoué : aucune double application.
        resultat = stock_engine.appliquer_delta_carriere_temps_reel(
            base,
            carriere_100,
            90,
            100,
            calculer_repartition=calcul_repartition
        )

        assert resultat[
            "type_changement"
        ] == "deja_applique"

        assert local_database.lire_stock_unitaire(
            base,
            munition_a
        ) == 16

        # 7. Mission atomique.
        resultat_mission = stock_engine.enregistrer_mission_et_consommer(
            base,
            date_heure="13.04.1951 - 10:00",
            avion="F-51D",
            nombre_avions=2,
            demandes=[
                (
                    munition_a,
                    4
                ),
                (
                    munition_b,
                    2
                )
            ]
        )

        assert resultat_mission[
            "stock_apres"
        ][
            munition_a
        ] == 12

        assert resultat_mission[
            "stock_apres"
        ][
            munition_b
        ] == 3

        con = sqlite3.connect(
            base
        )

        nombre_missions_avant = con.execute(
            """
            SELECT COUNT(*)
            FROM missions
            """
        ).fetchone()[
            0
        ]

        con.close()

        # 8. Stock insuffisant : rollback complet.
        try:
            stock_engine.enregistrer_mission_et_consommer(
                base,
                date_heure="14.04.1951 - 10:00",
                avion="F-51D",
                nombre_avions=2,
                demandes=[
                    (
                        munition_a,
                        9999
                    )
                ]
            )

            raise AssertionError(
                "StockInsuffisantError attendu."
            )

        except stock_engine.StockInsuffisantError as erreur:
            assert erreur.nom == munition_a

        assert local_database.lire_stock_unitaire(
            base,
            munition_a
        ) == 12

        con = sqlite3.connect(
            base
        )

        nombre_missions_apres = con.execute(
            """
            SELECT COUNT(*)
            FROM missions
            """
        ).fetchone()[
            0
        ]

        effets = con.execute(
            """
            SELECT COUNT(*)
            FROM test_calcul_side_effect
            """
        ).fetchone()[
            0
        ]

        con.close()

        assert nombre_missions_apres == nombre_missions_avant

        # Si les calculs avaient été exécutés sous BEGIN IMMEDIATE,
        # ces écritures par connexion secondaire auraient levé "database locked".
        assert effets >= 3



def verifier_consolidation_stock_engine():
    """Vérifie les opérations de maintenance sorties de l'interface."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(
            tmp
        ) / "maintenance_stock.db"

        local_database.initialiser_base(
            base
        )

        noms_munitions = list(
            app_data.MUNITIONS
        )

        munition_a = noms_munitions[0]
        munition_b = noms_munitions[1]
        munition_c = noms_munitions[2]

        stock_engine.definir_quantites_stock(
            base,
            {
                munition_a: 12,
                munition_b: 7,
                munition_c: 4,
            }
        )

        assert local_database.lire_stock_unitaire(base, munition_a) == 12
        assert local_database.lire_stock_unitaire(base, munition_b) == 7
        assert local_database.lire_stock_unitaire(base, munition_c) == 4

        stock_engine.definir_quantites_stock(
            base,
            {
                munition_a: 21,
            }
        )

        assert local_database.lire_stock_unitaire(base, munition_a) == 21
        assert local_database.lire_stock_unitaire(base, munition_b) == 7

        stock_engine.remplacer_stock_local(
            base,
            {
                munition_b: 33,
            }
        )

        assert local_database.lire_stock_unitaire(base, munition_a) == 0
        assert local_database.lire_stock_unitaire(base, munition_b) == 33
        assert local_database.lire_stock_unitaire(base, munition_c) == 0

        stock_engine.definir_quantites_stock(
            base,
            {
                munition_b: -5,
            }
        )

        assert local_database.lire_stock_unitaire(base, munition_b) == 0

    source_interface = Path(__file__).with_name("interface.py").read_text(encoding="utf-8")

    assert "def signature_snapshot_carriere(" not in source_interface
    assert "def seed_snapshot_carriere(" not in source_interface
    assert "stock_engine.signature_snapshot_carriere(" in source_interface

    debut_reset = source_interface.index("def reinitialiser_stock_standard_admin():")
    fin_reset = source_interface.index("def modifier_stock_admin():", debut_reset)
    bloc_reset = source_interface[debut_reset:fin_reset]

    assert "stock_engine.remplacer_stock_local(" in bloc_reset
    assert "UPDATE munitions" not in bloc_reset
    assert "BEGIN IMMEDIATE" not in bloc_reset

    debut_modif = source_interface.index("def modifier_stock_admin():")
    fin_modif = source_interface.index("def ouvrir_options():", debut_modif)
    bloc_modif = source_interface[debut_modif:fin_modif]

    assert "stock_engine.definir_quantites_stock(" in bloc_modif
    assert "UPDATE munitions" not in bloc_modif
    assert "BEGIN IMMEDIATE" not in bloc_modif





def verifier_traduction_complete_v0956():
    resultat = i18n.verifier_catalogues()
    assert resultat["ok"]

    i18n.definir_langue("en")
    assert i18n.t("forecast.title") == "FORECAST STOCK DISTRIBUTION"
    assert i18n.t_mois(5) == "MAY"
    assert i18n.t_priorite("TRÈS ÉLEVÉE") == "CRITICAL"
    assert i18n.t_taille_livraison("PETITE") == "SMALL"
    assert i18n.t_statut_livraison("EN_TRANSIT") == "IN TRANSIT"
    assert "rocket" in i18n.t_munition('Roquette aérienne à haute vitesse HVAR 5"').lower()

    i18n.definir_langue("fr")
    assert i18n.t_mois(5) == "MAI"
    assert i18n.t_priorite("TRÈS ÉLEVÉE") == "CRITIQUE"

    source = Path(__file__).with_name("interface.py").read_text(encoding="utf-8")
    assert 'VERSION_APPLICATION = "v1.1.0"' in source
    assert 'text="RÉPARTITION PRÉVISIONNELLE DU STOCK"' not in source
    assert 'text="HAUT COMMANDEMENT"' not in source
    assert 'text="RAPPORTS LOGISTIQUES"' not in source
    assert 'text="MODÈLE DE RÉPARTITION"' not in source
    assert 'text="RÉINITIALISATION COMPLÈTE"' not in source
    assert 'text="MODIFICATION DIRECTE DU STOCK"' not in source


def verifier_reception_ravitaillement_robuste():
    """
    Vérifie que les sécurités du ravitaillement vivent désormais
    dans stock_engine.py et que le watcher reste protégé dans l'interface.
    """
    source_interface = (
        Path(__file__).with_name(
            "interface.py"
        ).read_text(
            encoding="utf-8"
        )
    )

    source_moteur = (
        Path(__file__).with_name(
            "stock_engine.py"
        ).read_text(
            encoding="utf-8"
        )
    )

    assert "def appliquer_delta_carriere_temps_reel(" in source_moteur
    assert "type_changement\": \"deja_applique\"" in source_moteur
    assert "reference_verrouillee == nouvelle_valeur" in source_moteur
    assert "PRAGMA busy_timeout = 5000" in source_moteur
    assert "BEGIN IMMEDIATE" in source_moteur

    debut_watcher = source_interface.index(
        "def traiter_resultats_surveillance():"
    )

    fin_watcher = source_interface.index(
        "def cycle_lecture_carriere():",
        debut_watcher
    )

    bloc_watcher = source_interface[
        debut_watcher:fin_watcher
    ]

    assert "finally:" in bloc_watcher
    assert "fenetre.after(" in bloc_watcher
    assert "Enregistrement rapport de ravitaillement" in bloc_watcher
    assert "Traitement résultat watcher carrière" in bloc_watcher

    assert "def _executer_rafraichissement_interface_securise(" in source_interface
    assert "fenetre.after_idle(" in source_interface


def verifier_absence_auto_verrouillage_sqlite():
    """
    Le callback de répartition doit être appelé avant le premier
    BEGIN IMMEDIATE du delta à chaud.
    """
    source = (
        Path(__file__).with_name(
            "stock_engine.py"
        ).read_text(
            encoding="utf-8"
        )
    )

    debut = source.index(
        "def appliquer_delta_carriere_temps_reel("
    )

    fin = source.index(
        "# CONSOMMATION DE MISSION",
        debut
    )

    bloc = source[
        debut:fin
    ]

    position_calcul = bloc.index(
        "ajouts = calculer_repartition("
    )

    position_begin = bloc.index(
        '"BEGIN IMMEDIATE"'
    )

    assert position_calcul < position_begin

    partie_verrouillee = bloc[
        position_begin:
    ]

    assert "ajouts = calculer_repartition(" not in partie_verrouillee

    assert bloc.count(
        "SELECT ammo_qty"
    ) >= 2

    assert "PRAGMA busy_timeout = 5000" in bloc

def verifier_performance_ui_v0957():
    source = Path(__file__).with_name("interface.py").read_text(encoding="utf-8")
    assert "VERSION_APPLICATION = \"v1.1.0\"" in source
    assert "def charger_image_pil_cache(" in source
    assert "def creer_photoimage_cache(" in source
    assert "_CACHE_DONUTS_PIL" in source
    assert "ui_performance.log" in source
    assert source.count("journaliser_performance_ui(") >= 9


def verifier_adaptation_multi_ecran_v110():
    source = Path(__file__).with_name("interface.py").read_text(
        encoding="utf-8"
    )

    assert "def _zone_travail_moniteur(" in source
    assert "MonitorFromPoint" in source
    assert "rcWork" in source
    assert "def _installer_suivi_moniteur(" in source
    assert "def adapter_fenetre_principale_ecran(" in source
    assert "def adapter_fenetre_simple_ecran(" in source
    assert "def _adapter_mise_en_page_widget_ecran(" in source

    # 24 Toplevels dans cette version : 20 utilisent le chrome custom et
    # quatre fenêtres spéciales possèdent une adaptation dédiée.
    assert source.count("tk.Toplevel(") == 24
    assert source.count("appliquer_chrome_custom(") == 21  # def + 20 appels

    bloc_liaison = source[
        source.index("def selectionner_carriere_avant_demarrage("):
        source.index("# ============================================================\n# PROFILS D'AFFICHAGE")
    ]
    assert "adapter_fenetre_simple_ecran(" in bloc_liaison

    bloc_splash = source[
        source.index("def afficher_splash("):
        source.index("# ============================================================\n# HÔTE WINDOWS PERSISTANT")
    ]
    assert "_zone_travail_moniteur(" in bloc_splash
    assert "facteur_splash" in bloc_splash

    bloc_loading = source[
        source.index("def afficher_chargement_carriere("):
        source.index("# ============================================================\n# INITIALISATION")
    ]
    assert "adapter_fenetre_simple_ecran(" in bloc_loading

    debut_preset = source.index("def ouvrir_selecteur_preset(")
    fin_preset = source.index("def actualiser_menu_presets(", debut_preset)
    bloc_preset = source[debut_preset:fin_preset]
    assert "_zone_travail_moniteur(" in bloc_preset


def main():
    verifier_performance_ui_v0957()
    verifier_adaptation_multi_ecran_v110()
    verifier_catalogue()
    verifier_i18n()
    verifier_chargement_carriere_systematique_v0959()
    verifier_centrage_chargement_v09591()
    verifier_anglais_par_defaut_v09592()
    verifier_career_linked_v09593()
    verifier_donnees_utilisateur_localappdata_v101()
    verifier_updater_github_v102()
    verifier_logistique()
    verifier_lecture_carriere()
    verifier_base_locale()
    verifier_points_commandement_journaliers()
    verifier_migration_usine_points_existants()
    verifier_ordre_demarrage_ravitaillement()
    verifier_stock_engine_phase2b()
    verifier_consolidation_stock_engine()
    verifier_traduction_complete_v0956()
    verifier_reception_ravitaillement_robuste()
    verifier_absence_auto_verrouillage_sqlite()
    print("SMOKE TESTS v1.1.0 : OK")


if __name__ == "__main__":
    main()
