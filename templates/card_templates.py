"""Default Anki card templates (front/back HTML).

Used as fallback when deck.json does not specify templates.
"""

DEFAULT_TEMPLATES = [
    {
        "name": "DE→RO",
        "front": "{{de_word}} {{de_word_audio}}\n{{#de_sentence}}\n<br><br>\n<i>{{de_sentence}}</i>\n{{/de_sentence}}\n{{de_audio}}",
        "back": "{{FrontSide}}\n\n<hr id=answer>\n\n{{ro_word}}\n{{#ro_sentence}}\n<br><br>\n<i>{{ro_sentence}}</i>\n{{/ro_sentence}}\n{{#ro_note}}\n<br><br>\n<small>{{ro_note}}</small>\n{{/ro_note}}",
    },
    {
        "name": "RO→DE",
        "front": "{{ro_word}}\n{{#ro_sentence}}\n<br><br>\n<i>{{ro_sentence}}</i>\n{{/ro_sentence}}\n{{#ro_note}}\n<br><br>\n<small>{{ro_note}}</small>\n{{/ro_note}}",
        "back": "{{FrontSide}}\n\n<hr id=answer>\n\n{{de_word}} {{de_word_audio}}\n{{#de_sentence}}\n<br><br>\n<i>{{de_sentence}}</i>\n{{/de_sentence}}\n{{de_audio}}",
    },
]
