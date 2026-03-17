"""Default Anki card templates (front/back HTML).

Used as fallback when deck.json does not specify templates.
"""

DEFAULT_TEMPLATES = [
    {
        "name": "FO→NA",
        "front": "{{fo_word}} {{fo_word_audio}}\n{{#fo_sentence}}\n<br><br>\n<i>{{fo_sentence}}</i>\n{{/fo_sentence}}",
        "back": "{{FrontSide}}\n\n<hr id=answer>\n\n{{na_word}}\n{{#na_sentence}}\n<br><br>\n<i>{{na_sentence}}</i>\n{{/na_sentence}}\n{{#na_note}}\n<br><br>\n<small>{{na_note}}</small>\n{{/na_note}}",
    },
    {
        "name": "NA→FO",
        "front": "{{na_word}}\n{{#na_sentence}}\n<br><br>\n<i>{{na_sentence}}</i>\n{{/na_sentence}}\n{{#na_note}}\n<br><br>\n<small>{{na_note}}</small>\n{{/na_note}}",
        "back": "{{FrontSide}}\n\n<hr id=answer>\n\n{{fo_word}} {{fo_word_audio}}\n{{#fo_sentence}}\n<br><br>\n<i>{{fo_sentence}}</i>\n{{/fo_sentence}}",
    },
]
