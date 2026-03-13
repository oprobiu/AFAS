"""
Shared config loader for AFAS scripts.

Reads deck.json and resolves fields, templates, CSS, and TTS config.
Falls back to AFAS defaults when not specified in config.
"""

import json, os, sys


def load_config(config_path, tools_dir=None):
    """Load deck.json and resolve all config with defaults."""
    with open(config_path) as f:
        config = json.load(f)

    root = os.path.dirname(os.path.abspath(config_path))
    if root.endswith("data"):
        root = os.path.dirname(root)
    config["_root"] = root

    # Load defaults from AFAS templates
    if tools_dir:
        sys.path.insert(0, tools_dir)
    else:
        # Assume we're inside AFAS/scripts/
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    from templates.fields import DEFAULT_FIELDS, DEFAULT_CSV_COLUMNS
    from templates.card_css import DEFAULT_CSS
    from templates.card_templates import DEFAULT_TEMPLATES

    # --- Fields ---
    if "fields" not in config:
        config["fields"] = DEFAULT_FIELDS
    # Derive csv_columns from fields + tags
    config["csv_columns"] = [f["csv"] for f in config["fields"]] + ["tags"]
    # Anki field names (no tags)
    config["anki_fields"] = [f["name"] for f in config["fields"]]

    # --- Templates ---
    if "templates" not in config:
        if "template_files" in config:
            tf = config["template_files"]
            tpath = os.path.join(root, tf["templates"])
            with open(tpath) as f:
                config["templates"] = json.load(f)
        else:
            config["templates"] = DEFAULT_TEMPLATES

    # --- CSS ---
    if "css" not in config:
        if "template_files" in config and "css" in config["template_files"]:
            css_path = os.path.join(root, config["template_files"]["css"])
            with open(css_path) as f:
                config["css"] = f.read()
        else:
            config["css"] = DEFAULT_CSS

    return config
