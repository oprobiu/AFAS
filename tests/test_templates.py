"""Test card templates and CSS defaults."""

import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from templates.card_css import DEFAULT_CSS, COLOR_DER, COLOR_DIE, COLOR_DAS
from templates.card_templates import DEFAULT_TEMPLATES
from templates.fields import DEFAULT_FIELDS, DEFAULT_CSV_COLUMNS


def test_css_not_empty():
    assert len(DEFAULT_CSS) > 50


def test_css_has_card_class():
    assert ".card" in DEFAULT_CSS


def test_css_has_replay_button():
    assert ".replay-button" in DEFAULT_CSS


def test_css_has_sent_sep():
    assert "hr.sent-sep" in DEFAULT_CSS


def test_colors_are_hex():
    for color in [COLOR_DER, COLOR_DIE, COLOR_DAS]:
        assert color.startswith("#")
        assert len(color) == 7


def test_default_templates_count():
    assert len(DEFAULT_TEMPLATES) == 2


def test_templates_have_required_keys():
    for tmpl in DEFAULT_TEMPLATES:
        assert "name" in tmpl
        assert "front" in tmpl
        assert "back" in tmpl


def test_templates_reference_fields():
    all_text = "".join(t["front"] + t["back"] for t in DEFAULT_TEMPLATES)
    for field in ["fo_word", "fo_sentence", "na_word", "fo_word_audio"]:
        assert f"{{{{{field}}}}}" in all_text, f"Field {field} not in templates"


def test_default_fields_count():
    assert len(DEFAULT_FIELDS) == 7


def test_default_fields_have_name_and_csv():
    for f in DEFAULT_FIELDS:
        assert "name" in f
        assert "csv" in f


def test_default_fields_use_fo_na():
    csvs = [f["csv"] for f in DEFAULT_FIELDS]
    assert "fo_word" in csvs
    assert "na_word" in csvs
    assert "fo_word_audio" in csvs


def test_csv_columns_include_tags():
    assert "tags" in DEFAULT_CSV_COLUMNS
    assert len(DEFAULT_CSV_COLUMNS) == len(DEFAULT_FIELDS) + 1
