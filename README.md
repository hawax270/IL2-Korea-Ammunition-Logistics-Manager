# IL-2 Korea Ammunition Logistics Manager

**Version 1.0**  
Created by **hawax270**  
Development assisted by **OpenAI ChatGPT**

An unofficial community logistics tool for IL-2 Korea career mode.

The application reads IL-2 career data in **read-only mode** and maintains its
own local logistics database. It does not modify the IL-2 career database.

## Main features

- persistent concrete ammunition stocks;
- aircraft-specific ammunition compatibility;
- mission loadout consumption;
- synchronization with IL-2 `ammoQty`;
- STANDARD and custom distribution models;
- logistics forecasting;
- monthly priorities;
- High Command requests;
- Command Points;
- urgent deliveries;
- temporary boosts;
- permanent directives;
- logistics and mission reports;
- isolated local data per career;
- French and English interface;
- English default language for fresh installations;
- light / dark themes;
- interface scaling;
- Admin tools;
- aircraft-specific career loading banners.

## Supported aircraft

- F-51D
- F-80C-10
- F-84E
- F-86A-5
- MiG-15bis
- La-11
- Yak-9P
- IL-10

## Important stock rule

IL-2's `ammoQty` remains the source of truth for normal supply.

A decrease in `ammoQty` does **not** directly remove a concrete ammunition type
from the local stock because the IL-2 career database does not identify which
munition was actually consumed.

Concrete ammunition consumption is driven by missions recorded in this tool.

## Language

Fresh installations start in **English**.

French is available in the Options menu.

Existing language preferences are preserved.

## Running from source

Requirements:

- Windows 10 / 11 x64
- Python 3.14
- Pillow

Install Pillow if needed:

```text
python -m pip install Pillow
```

Run:

```text
python interface.py
```

## Building the Windows executable

A PyInstaller configuration and build script are included:

```text
build_windows.bat
IL2_Korea_Ammunition_Logistics_Manager.spec
```

On Windows:

```text
build_windows.bat
```

The script installs/updates PyInstaller and builds the application.

The executable must still be tested on a clean Windows machine before public distribution.

## Loading banners

Aircraft-specific loading artwork is stored in:

```text
images/loading_banners/
```

If a banner is unavailable, the application uses the standard fallback background.

## User data

The public source release does not include:
- personal IL-2 career databases;
- local career databases;
- personal `config.json`;
- runtime logs.

## License

Source code is released under the **MIT License**.

Copyright (c) 2026 hawax270

Third-party and game-derived assets remain subject to their respective rights.

## Disclaimer

This is an unofficial community project and is not affiliated with or endorsed
by the developers or publishers of IL-2 Sturmovik.


## User data location

Writable user data is stored outside the application installation directory.

On Windows:

```text
%LOCALAPPDATA%\hawax270\IL2 Korea Ammunition Logistics Manager\
    config.json
    careers\
    logs\
```

This keeps user preferences and career logistics data safe when the application
is installed under `Program Files` or updated to a newer version.

When upgrading from an older portable/source build, the application attempts to
copy legacy `config.json`, `careers`, `logs` and `stock.db` data automatically
without overwriting data that already exists in the new location.

## Updates

The application checks the latest public GitHub Release in the background after startup.

- no telemetry is sent;
- network errors during the automatic startup check remain silent;
- manual checks are available from **Options → Updates**;
- only the official version-matched Windows installer asset from this repository is accepted;
- official installer filename format: `IL2_Korea_ALM_SetupvX.Y.Z.exe`;
- career/configuration data in `%LOCALAPPDATA%` is not replaced by the updater.

Official update source:

```text
github.com/hawax270/IL2-Korea-Ammunition-Logistics-Manager/releases
```
