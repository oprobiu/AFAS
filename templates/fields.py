"""Default Anki card field definitions.

These are used as fallback when deck.json does not specify fields.
fo_ = foreign language, na_ = native language.
"""

DEFAULT_FIELDS = [
    {"name": "fo_word", "csv": "fo_word"},
    {"name": "fo_sentence", "csv": "fo_sentence"},
    {"name": "na_word", "csv": "na_word"},
    {"name": "na_sentence", "csv": "na_sentence"},
    {"name": "na_note", "csv": "na_note"},
    {"name": "fo_sentence_audio", "csv": "fo_sentence_audio"},
    {"name": "fo_word_audio", "csv": "fo_word_audio"},
]

# CSV column order (includes tags which is not an Anki field)
DEFAULT_CSV_COLUMNS = [f["csv"] for f in DEFAULT_FIELDS] + ["tags"]
