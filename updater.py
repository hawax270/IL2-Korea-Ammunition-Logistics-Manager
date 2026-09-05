"""GitHub Releases updater for IL2 Korea Ammunition Logistics Manager."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request


GITHUB_OWNER = "hawax270-eng"
GITHUB_REPOSITORY = "IL2-Korea-Ammunition-Logistics-Manager"

GITHUB_API_LATEST_RELEASE = (
    "https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPOSITORY}/releases/latest"
)

GITHUB_RELEASE_DOWNLOAD_PREFIX = (
    "https://github.com/"
    f"{GITHUB_OWNER}/{GITHUB_REPOSITORY}/releases/download/"
)

INSTALLER_NAME_PATTERN = re.compile(
    r"^IL2_Korea_ALM_Setupv"
    r"(?P<version>\d+(?:\.\d+){1,3})\.exe$",
    re.IGNORECASE,
)

USER_AGENT = "IL2-Korea-Ammunition-Logistics-Manager-Updater"


class UpdaterError(RuntimeError):
    pass


def normaliser_version(version):
    texte = str(version or "").strip()

    if texte.lower().startswith("v"):
        texte = texte[1:]

    correspondance = re.match(
        r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:\.(\d+))?",
        texte
    )

    if correspondance is None:
        raise UpdaterError(
            f"Invalid version: {version!r}"
        )

    return tuple(
        int(valeur or 0)
        for valeur in correspondance.groups()
    )


def version_plus_recente(distante, locale):
    return normaliser_version(distante) > normaliser_version(locale)


def _requete_github(url, timeout=6.0):
    requete = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": USER_AGENT,
        }
    )

    try:
        return urllib.request.urlopen(
            requete,
            timeout=timeout
        )
    except urllib.error.HTTPError as erreur:
        raise UpdaterError(
            f"GitHub returned HTTP {erreur.code}."
        ) from erreur
    except urllib.error.URLError as erreur:
        raise UpdaterError(
            "Unable to contact GitHub."
        ) from erreur


def extraire_asset_installeur(release):
    tag = str(release.get("tag_name", "") or "").strip()

    if not tag:
        raise UpdaterError(
            "The GitHub release has no version tag."
        )

    version_tag = normaliser_version(tag)

    for asset in release.get("assets", []):
        nom = str(asset.get("name", "") or "")

        correspondance = INSTALLER_NAME_PATTERN.match(nom)

        if correspondance is None:
            continue

        if normaliser_version(
            correspondance.group("version")
        ) != version_tag:
            continue

        url = str(
            asset.get(
                "browser_download_url",
                ""
            )
            or ""
        )

        if not url.startswith(
            GITHUB_RELEASE_DOWNLOAD_PREFIX
        ):
            continue

        return {
            "name": nom,
            "download_url": url,
            "size": int(
                asset.get(
                    "size",
                    0
                )
                or 0
            ),
        }

    raise UpdaterError(
        "No official Windows installer was found in the latest GitHub release."
    )


def verifier_derniere_version(
    version_locale,
    timeout=6.0
):
    with _requete_github(
        GITHUB_API_LATEST_RELEASE,
        timeout=timeout
    ) as reponse:
        try:
            release = json.load(reponse)
        except Exception as erreur:
            raise UpdaterError(
                "GitHub returned an invalid release response."
            ) from erreur

    if release.get("draft"):
        raise UpdaterError(
            "The latest GitHub release is a draft."
        )

    tag = str(release.get("tag_name", "") or "").strip()

    if not tag:
        raise UpdaterError(
            "The latest GitHub release has no tag."
        )

    disponible = version_plus_recente(
        tag,
        version_locale
    )

    resultat = {
        "status": (
            "available"
            if disponible
            else "up_to_date"
        ),
        "current_version": str(version_locale),
        "latest_version": tag,
        "tag": tag,
        "release_url": str(
            release.get(
                "html_url",
                ""
            )
            or ""
        ),
        "notes": str(
            release.get(
                "body",
                ""
            )
            or ""
        ),
        "installer": None,
    }

    if disponible:
        resultat["installer"] = extraire_asset_installeur(
            release
        )

    return resultat


def _fichier_est_executable_windows(chemin):
    try:
        with Path(chemin).open("rb") as fichier:
            return fichier.read(2) == b"MZ"
    except OSError:
        return False


def telecharger_installeur(
    info_mise_a_jour,
    dossier_destination,
    progression=None,
    timeout=20.0
):
    installer = info_mise_a_jour.get("installer")

    if not isinstance(installer, dict):
        raise UpdaterError(
            "No installer is attached to this update."
        )

    nom = str(installer.get("name", "") or "")

    if INSTALLER_NAME_PATTERN.match(nom) is None:
        raise UpdaterError(
            "Unexpected installer filename."
        )

    url = str(
        installer.get(
            "download_url",
            ""
        )
        or ""
    )

    if not url.startswith(
        GITHUB_RELEASE_DOWNLOAD_PREFIX
    ):
        raise UpdaterError(
            "Unexpected installer download address."
        )

    destination_dir = Path(dossier_destination)
    destination_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    destination = destination_dir / nom
    temporaire = destination.with_suffix(
        destination.suffix + ".part"
    )

    if (
        destination.exists()
        and _fichier_est_executable_windows(destination)
    ):
        if progression is not None:
            taille = destination.stat().st_size
            progression(taille, taille)
        return destination

    destination.unlink(missing_ok=True)
    temporaire.unlink(missing_ok=True)

    requete = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/octet-stream",
        }
    )

    try:
        reponse = urllib.request.urlopen(
            requete,
            timeout=timeout
        )
    except urllib.error.HTTPError as erreur:
        raise UpdaterError(
            f"Installer download failed with HTTP {erreur.code}."
        ) from erreur
    except urllib.error.URLError as erreur:
        raise UpdaterError(
            "Unable to download the installer."
        ) from erreur

    try:
        total = int(
            reponse.headers.get(
                "Content-Length",
                installer.get("size", 0) or 0
            )
            or 0
        )

        telecharge = 0

        with temporaire.open("wb") as fichier:
            while True:
                bloc = reponse.read(
                    256 * 1024
                )

                if not bloc:
                    break

                fichier.write(bloc)
                telecharge += len(bloc)

                if progression is not None:
                    progression(
                        telecharge,
                        total
                    )

    except Exception:
        temporaire.unlink(missing_ok=True)
        raise
    finally:
        try:
            reponse.close()
        except Exception:
            pass

    if not _fichier_est_executable_windows(temporaire):
        temporaire.unlink(missing_ok=True)
        raise UpdaterError(
            "The downloaded file is not a valid Windows executable."
        )

    temporaire.replace(destination)
    return destination


def lancer_installeur(chemin):
    chemin = Path(chemin).resolve()

    if not chemin.exists():
        raise UpdaterError(
            "The downloaded installer no longer exists."
        )

    if not _fichier_est_executable_windows(chemin):
        raise UpdaterError(
            "The downloaded installer is invalid."
        )

    try:
        if os.name == "nt":
            os.startfile(str(chemin))
        else:
            subprocess.Popen(
                [str(chemin)],
                cwd=str(chemin.parent)
            )
    except Exception as erreur:
        raise UpdaterError(
            "Unable to launch the update installer."
        ) from erreur
