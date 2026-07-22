"""
Self-updater for AutoPaste.

Stdlib only (no new dependencies, no credentials) so it works against a PUBLIC
GitHub repo. On launch the app calls check_for_update() on a background thread;
if a newer release exists it prompts, downloads the new exe, and hands off to a
tiny .bat that swaps the running exe and relaunches it.

Only ever does anything when running as a frozen PyInstaller exe. From source
(python gui.py) it no-ops, since there is no exe to replace.
"""

import json
import os
import subprocess
import sys
import tempfile
import urllib.request

from version import __version__

# The public repo the releases are published to.
REPO = "YoderMW/AutoPaste"
LATEST_RELEASE_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
ASSET_NAME = "AutoPaste.exe"

# Short so a slow/blocked network can't stall launch for long.
HTTP_TIMEOUT = 5


def is_frozen():
    """True when running as the packaged exe, False when running from source."""
    return getattr(sys, "frozen", False)


def _version_tuple(text):
    """'v1.10.0' / '1.10.0' -> (1, 10, 0). Non-numeric parts become 0."""
    text = text.lstrip("vV").strip()
    parts = []
    for chunk in text.split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def is_newer(latest_tag, current=__version__):
    """True if latest_tag represents a strictly higher version than current."""
    return _version_tuple(latest_tag) > _version_tuple(current)


def get_latest_release():
    """
    Return (tag, asset_url) for the latest GitHub release, or None on any
    problem (offline, rate-limited, malformed, no matching asset). Never raises.
    """
    try:
        req = urllib.request.Request(
            LATEST_RELEASE_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "AutoPaste-Updater",
            },
        )
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None  # offline / DNS / timeout / HTTP error / bad JSON

    tag = data.get("tag_name")
    if not tag:
        return None

    asset_url = None
    for asset in data.get("assets", []):
        if asset.get("name") == ASSET_NAME:
            asset_url = asset.get("browser_download_url")
            break
    if not asset_url:
        return None

    return tag, asset_url


def download_exe(url, dest):
    """
    Stream the release asset to dest. Returns True on success, False on failure
    (and cleans up a partial file). Never raises.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AutoPaste-Updater"})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT * 6) as resp, open(dest, "wb") as f:
            while True:
                chunk = resp.read(64 * 1024)
                if not chunk:
                    break
                f.write(chunk)
        return True
    except Exception:
        try:
            if os.path.exists(dest):
                os.remove(dest)
        except OSError:
            pass
        return False


def apply_update_and_restart(new_exe):
    """
    Swap the running exe for new_exe and relaunch. A running Windows exe can't
    overwrite itself, so we spawn a detached .bat that waits for this process to
    exit, replaces the file, restarts it, then deletes itself.

    Call sys.exit() right after this returns. No-op (returns False) from source.
    """
    if not is_frozen():
        return False

    current_exe = sys.executable  # the running AutoPaste.exe
    backup_exe = current_exe + ".bak"
    bat_path = os.path.join(tempfile.gettempdir(), "autopaste_update.bat")

    # Safe swap: rename the running exe aside (don't delete it), move the new
    # one into place, and only then discard the backup. If the move fails for
    # any reason, restore the backup so the user is never left without a working
    # exe. ping = a portable ~2s sleep so the parent fully exits before we touch
    # its file; quoting guards paths with spaces.
    script = (
        "@echo off\r\n"
        "ping 127.0.0.1 -n 3 >nul\r\n"
        f'move /y "{current_exe}" "{backup_exe}" >nul\r\n'
        f'move /y "{new_exe}" "{current_exe}" >nul\r\n'
        "if errorlevel 1 (\r\n"
        f'    move /y "{backup_exe}" "{current_exe}" >nul\r\n'
        ") else (\r\n"
        f'    del "{backup_exe}" >nul 2>&1\r\n'
        ")\r\n"
        f'start "" "{current_exe}"\r\n'
        'del "%~f0"\r\n'
    )

    try:
        with open(bat_path, "w") as f:
            f.write(script)
    except OSError:
        return False

    DETACHED_PROCESS = 0x00000008
    CREATE_NO_WINDOW = 0x08000000
    try:
        subprocess.Popen(
            ["cmd", "/c", bat_path],
            creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
            close_fds=True,
        )
    except Exception:
        return False

    return True
