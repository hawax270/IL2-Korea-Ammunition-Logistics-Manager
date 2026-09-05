# IL-2 Korea Ammunition Logistics Manager

**Version 1.0**  
Créé par **hawax270**  
Développement assisté par **OpenAI ChatGPT**

Outil communautaire non officiel de gestion logistique pour le mode carrière d'IL-2 Korea.

L'application lit les données de carrière IL-2 en **lecture seule** et utilise
sa propre base logistique locale. Elle ne modifie pas la base carrière IL-2.

## Fonctionnalités principales

- stocks persistants de munitions concrètes ;
- compatibilité des munitions par appareil ;
- consommation des emports par mission ;
- synchronisation avec `ammoQty` d'IL-2 ;
- modèles de répartition STANDARD et personnalisés ;
- prévisions logistiques ;
- priorités mensuelles ;
- demandes au Haut Commandement ;
- points de commandement ;
- livraisons urgentes ;
- boosts temporaires ;
- directives permanentes ;
- rapports logistiques et de mission ;
- données locales isolées par carrière ;
- interface française et anglaise ;
- anglais par défaut sur une nouvelle installation ;
- thèmes clair / sombre ;
- mise à l'échelle de l'interface ;
- outils Admin ;
- bannières de chargement par appareil.

## Appareils pris en charge

- F-51D
- F-80C-10
- F-84E
- F-86A-5
- MiG-15bis
- La-11
- Yak-9P
- IL-10

## Règle importante de stock

`ammoQty` d'IL-2 reste la référence pour le ravitaillement normal.

Une baisse de `ammoQty` ne retire **pas** directement un type de munition
concrète du stock local, car la base carrière IL-2 n'indique pas quelle
munition précise a été consommée.

La consommation concrète provient des missions enregistrées dans l'application.

## Langue

Une nouvelle installation démarre en **anglais**.

Le français est disponible dans Options.

Les préférences de langue existantes sont conservées.

## Lancer depuis le code source

Prérequis :

- Windows 10 / 11 x64
- Python 3.14
- Pillow

Installation de Pillow si nécessaire :

```text
python -m pip install Pillow
```

Lancement :

```text
python interface.py
```

## Construire l'exécutable Windows

Une configuration PyInstaller et un script de build sont inclus :

```text
build_windows.bat
IL2_Korea_Ammunition_Logistics_Manager.spec
```

Sous Windows :

```text
build_windows.bat
```

Le script installe/met à jour PyInstaller puis construit l'application.

L'exécutable doit ensuite être testé sur un Windows propre avant distribution publique.

## Bannières de chargement

Les illustrations de chargement sont stockées dans :

```text
images/loading_banners/
```

Si une bannière manque, l'application utilise automatiquement le fond standard.

## Données utilisateur

La release publique ne contient pas :
- de base carrière IL-2 personnelle ;
- de base locale de carrière ;
- de `config.json` personnel ;
- de logs d'exécution.

## Licence

Le code source est publié sous **licence MIT**.

Copyright (c) 2026 hawax270

Les ressources tierces ou issues du jeu restent soumises à leurs droits respectifs.

## Avertissement

Projet communautaire non officiel, sans affiliation ni approbation des
développeurs ou éditeurs d'IL-2 Sturmovik.


## Emplacement des données utilisateur

Les données modifiables sont stockées en dehors du dossier d'installation.

Sous Windows :

```text
%LOCALAPPDATA%\hawax270\IL2 Korea Ammunition Logistics Manager\
    config.json
    careers\
    logs\
```

Cela permet de conserver les préférences et les stocks de carrière lors d'une
installation dans `Program Files` ou d'une mise à jour du logiciel.

Lors du passage depuis une ancienne version portable/source, l'application
essaie automatiquement de recopier les anciens `config.json`, `careers`,
`logs` et `stock.db`, sans écraser une donnée déjà présente.

## Mises à jour

Après le démarrage, l'application vérifie en arrière-plan la dernière Release publique GitHub.

- aucune télémétrie n'est envoyée ;
- les erreurs réseau de la vérification automatique restent silencieuses ;
- une vérification manuelle est disponible dans **Options → Mises à jour** ;
- seul l'installeur Windows officiel dont la version correspond à la Release est accepté ;
- format officiel du nom de l'installeur : `IL2_Korea_ALM_SetupvX.Y.Z.exe` ;
- les carrières et préférences dans `%LOCALAPPDATA%` ne sont pas remplacées par l'updateur.

Source officielle :

```text
github.com/hawax270/IL2-Korea-Ammunition-Logistics-Manager/releases
```
