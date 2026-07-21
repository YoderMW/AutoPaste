import json
import os
import shutil

from paths import resource_path, user_data_path

SETTINGS_FILE = user_data_path("settings.json")

DEFAULTS = {
    "keywords": [],
    "selected_company": "Greenfield/Corsi",
    "delay": "1",
    "extra_tabs": "0",
}


def load_settings():
    """
    Return the settings dict: defaults, overlaid with the bundled seed on
    first run, overlaid with the user's saved file. Also migrates a legacy
    keywords.json (a bare list) if that's the only prior data present.
    """
    data = {**DEFAULTS, "keywords": list(DEFAULTS["keywords"])}

    if not os.path.exists(SETTINGS_FILE):
        seed = resource_path("settings.json")
        if os.path.exists(seed):
            shutil.copyfile(seed, SETTINGS_FILE)
        else:
            legacy = user_data_path("keywords.json")  # migrate old installs
            if os.path.exists(legacy):
                try:
                    with open(legacy) as f:
                        data["keywords"] = json.load(f)
                except (json.JSONDecodeError, OSError):
                    pass

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                data.update(saved)
        except (json.JSONDecodeError, OSError):
            pass  # corrupt file -> fall back to defaults

    return data


def save_settings(data):
    """Write the whole settings dict to the per-user file."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except OSError as e:
        print(f"Error saving settings: {e}")
