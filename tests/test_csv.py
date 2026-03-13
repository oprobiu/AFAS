"""Test CSV format validation."""

import os, sys, tempfile, csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from templates.fields import DEFAULT_CSV_COLUMNS


def write_csv(path, rows, fieldnames=None):
    fieldnames = fieldnames or DEFAULT_CSV_COLUMNS
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_row(**overrides):
    base = {f: "" for f in DEFAULT_CSV_COLUMNS}
    base["note_id"] = "1"
    base["de_word"] = "der Test"
    base["ro_word"] = "test"
    base["tags"] = "NOUN"
    base.update(overrides)
    return base


def test_csv_columns_defined():
    assert len(DEFAULT_CSV_COLUMNS) == 9
    assert "note_id" in DEFAULT_CSV_COLUMNS
    assert "tags" in DEFAULT_CSV_COLUMNS


def test_csv_roundtrip():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name
    try:
        rows = [make_row(note_id="1"), make_row(note_id="2")]
        write_csv(path, rows)
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            loaded = list(reader)
        assert len(loaded) == 2
        assert loaded[0]["note_id"] == "1"
        assert set(reader.fieldnames) == set(DEFAULT_CSV_COLUMNS)
    finally:
        os.unlink(path)


def test_csv_unicode():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name
    try:
        rows = [make_row(de_word="die Straße", ro_word="strada", de_sentence="Äpfel und Öl")]
        write_csv(path, rows)
        with open(path, encoding="utf-8") as f:
            loaded = list(csv.DictReader(f))
        assert loaded[0]["de_word"] == "die Straße"
        assert loaded[0]["de_sentence"] == "Äpfel und Öl"
    finally:
        os.unlink(path)
