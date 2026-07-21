import os
import sys


def resource_path(relative):
    """
    Absolute path to a BUNDLED, read-only file (seed data, icon, future images).

    When frozen by PyInstaller, bundled files live in a temp folder exposed as
    sys._MEIPASS. When running as a normal script, they sit next to this file.
    The same call works in both cases.
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def user_data_dir():
    """
    Per-user writable folder: %APPDATA%\\AutoPaste (created if missing).
    Survives app updates and needs no admin rights.
    """
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "AutoPaste")
    os.makedirs(path, exist_ok=True)
    return path


def user_data_path(filename):
    """Absolute path to a writable file inside the per-user folder."""
    return os.path.join(user_data_dir(), filename)
