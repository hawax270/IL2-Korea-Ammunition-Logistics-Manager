# Changelog

## v1.1.1

### Adaptive multi-monitor interface
- all application windows now fit automatically inside the usable area of the monitor they are displayed on;
- the taskbar/work area is taken into account on Windows;
- the main 1600×900 interface is proportionally reduced on smaller displays instead of being cut off;
- custom dialogs and large logistics windows are resized with their controls and text;
- windows automatically readapt when moved between monitors with different resolutions;
- splash, career-link, loading and preset popups also use screen-safe positioning.

### Reliable window sizing
- replaced content-based auto-sizing with one deterministic rule for every window: reference size → selected window profile → monitor-safe scale;
- windows no longer grow differently depending on the font rendering of the machine;
- layout geometry and monitor fitting now use one stable scale, preventing oversized windows with a small unscaled content area;
- font profiles remain visible but are safety-capped relative to the available layout so controls cannot be pushed off-screen;
- the career selection frame now always fills the real window size and keeps its action buttons anchored at the bottom;
- multi-monitor movement keeps the final content-aware callback instead of an earlier geometry-only callback;
- Canvas text follows the COMPACT / STANDARD / LARGE font profile;
- fixed a forecast period translation key that could appear literally in the interface.

## v1.1.0

### Responsive window layout
- forecast and stock windows now use fluid grid columns instead of fixed panel widths;
- unused horizontal space is distributed between panels automatically;
- donut charts and long High Command text adapt to the available panel size;
- small screens keep minimum readable panel widths instead of clipping content.
- final version

## v1.0.3
- updater fix 

## v1.0.2
- update images on loading screen

### GitHub updater
- silent background check against the latest public GitHub Release at startup;
- dedicated **UPDATE** button in the main bottom bar;
- the UPDATE button turns red when a newer GitHub Release is detected;
- automatic startup checks stay silent until the user clicks the red UPDATE button;
- custom update-available and download-progress windows;
- downloads only the official version-matched Windows installer from this repository;
- validates the downloaded file as a Windows executable before launching it;
- launches the Inno Setup installer, then closes the application;
- no telemetry;
- user career/configuration data remains in `%LOCALAPPDATA%`.
- GitHub update endpoint updated to the current `hawax270` repository owner.

### Windows branding
- added the official IL-2 Korea ALM icon to the application executable;
- the same icon is used by the Tk window/taskbar and the Inno Setup installer;
- multi-resolution `.ico` asset included for Windows shortcuts and Explorer.

## v1.0.1

### Packaging preparation
- moved writable user data to `%LOCALAPPDATA%`;
- `config.json`, career databases and logs no longer depend on the install folder;
- added automatic migration from legacy portable/source folders;
- existing destination data is never overwritten during migration;
- prepared the application for installation under `Program Files`.

## v1.0

First public stable release.

### Core logistics
- persistent concrete ammunition stock simulation;
- read-only IL-2 career database integration;
- per-career local databases;
- mission loadout consumption;
- IL-2 `ammoQty` supply synchronization;
- anti-double-application supply logic;
- stock forecasts and monthly distribution logic.

### High Command
- Command Points;
- urgent deliveries;
- temporary boosts;
- permanent directives;
- Admin-mode free actions.

### Interface
- French / English localization;
- English default for fresh installations;
- light / dark themes;
- UI scaling;
- aircraft-specific loading banners;
- five-second career loading screen;
- UI caching and performance logging.

### Reliability
- extracted stock engine;
- read-only IL-2 DB access;
- short local DB transactions;
- smoke-test coverage for critical stock/database behavior;
- feature freeze completed before v1.0.

### Credits
Created by **hawax270**.  
Development assisted by **OpenAI ChatGPT**.
