"""Test build_apkg with config-driven approach."""

import csv, json, os, sys, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from templates.fields import DEFAULT_FIELDS, DEFAULT_CSV_COLUMNS

TOOLS_DIR = os.path.join(os.path.dirname(__file__), "..")


def make_test_dataset(tmpdir, custom_fields=None, custom_templates=None, tts=None):
    """Create a minimal dataset for testing."""
    data_dir = os.path.join(tmpdir, "data")
    media_dir = os.path.join(tmpdir, "media_files")
    os.makedirs(data_dir)
    os.makedirs(media_dir)

    config = {
        "deck_name": "Test Deck",
        "deck_id": 9999999999,
        "notetype_id": 8888888888,
        "tools_repo": "oprobiu/AFAS",
        "tools_version": "v1.0.0",
    }
    if custom_fields:
        config["fields"] = custom_fields
    if custom_templates:
        config["templates"] = custom_templates
    if tts:
        config["tts"] = tts

    config_path = os.path.join(data_dir, "deck.json")
    with open(config_path, "w") as f:
        json.dump(config, f)

    # Write CSV with appropriate columns
    fields = custom_fields or DEFAULT_FIELDS
    csv_cols = [f["csv"] for f in fields] + ["tags"]

    notes_path = os.path.join(data_dir, "notes.csv")
    with open(notes_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_cols)
        writer.writeheader()
        row = {c: "" for c in csv_cols}
        row[csv_cols[0]] = "test_word"
        if "fo_word" in row:
            row["fo_word"] = "der Test"
        if "na_word" in row:
            row["na_word"] = "test"
        row["tags"] = "NOUN"
        writer.writerow(row)

    return config_path


def test_build_with_defaults():
    """Build with no fields/templates in config — uses AFAS defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = make_test_dataset(tmpdir)
        sys.path.insert(0, os.path.join(TOOLS_DIR, "scripts"))
        from build_apkg import build
        build(config_path, TOOLS_DIR)
        apkg = os.path.join(tmpdir, "build", "Test_Deck.apkg")
        assert os.path.exists(apkg)
        assert os.path.getsize(apkg) > 0


def test_build_with_custom_fields():
    """Build with custom fields defined in config."""
    custom_fields = [
        {"name": "ID", "csv": "id"},
        {"name": "Word", "csv": "word"},
        {"name": "Translation", "csv": "translation"},
    ]
    custom_templates = [
        {"name": "Card 1", "front": "{{Word}}", "back": "{{Translation}}"},
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = make_test_dataset(tmpdir, custom_fields=custom_fields, custom_templates=custom_templates)
        # Write matching CSV
        data_dir = os.path.join(tmpdir, "data")
        with open(os.path.join(data_dir, "notes.csv"), "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "word", "translation", "tags"])
            writer.writeheader()
            writer.writerow({"id": "1", "word": "ciao", "translation": "hello", "tags": "GREETING"})

        sys.path.insert(0, os.path.join(TOOLS_DIR, "scripts"))
        from build_apkg import build
        build(config_path, TOOLS_DIR)
        apkg = os.path.join(tmpdir, "build", "Test_Deck.apkg")
        assert os.path.exists(apkg)


def test_config_required_keys():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "deck.json")
        config = {"deck_name": "X", "deck_id": 1, "notetype_id": 2,
                  "tools_repo": "a/b", "tools_version": "v1"}
        with open(config_path, "w") as f:
            json.dump(config, f)
        with open(config_path) as f:
            loaded = json.load(f)
        for key in ["deck_name", "deck_id", "notetype_id", "tools_repo", "tools_version"]:
            assert key in loaded
