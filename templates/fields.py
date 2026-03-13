"""Default Anki card field definitions.

These are used as fallback when deck.json does not specify fields.
"""

DEFAULT_FIELDS = [
    {"name": "Note ID", "csv": "note_id"},
    {"name": "de_word", "csv": "de_word"},
    {"name": "de_sentence", "csv": "de_sentence"},
    {"name": "ro_word", "csv": "ro_word"},
    {"name": "ro_sentence", "csv": "ro_sentence"},
    {"name": "ro_note", "csv": "ro_note"},
    {"name": "de_audio", "csv": "de_audio"},
    {"name": "de_word_audio", "csv": "de_word_audio"},
]

# CSV column order (includes tags which is not an Anki field)
DEFAULT_CSV_COLUMNS = [f["csv"] for f in DEFAULT_FIELDS] + ["tags"]
