# From scratch

No existing deck. Starting fresh.

## Before you start

Python 3.8+. Run everything from the AFAS directory.

```bash
pip install -r requirements.txt
cd /path/to/AFAS
```

## 1. Scaffold the dataset

```bash
python3 scripts/init_dataset.py ~/MyDeck
```

Creates `data/deck.json` with random IDs and example fields, `data/notes.csv` with 3 example cards, `.gitignore`, `README.md`, and `media_files/`. Everything builds out of the box. You can run validate and build right away to verify.

## 2. Edit deck.json

Open `~/MyDeck/data/deck.json`. Change `deck_name`, adjust the fields and templates to match your deck. The `_comment` keys explain what each part does.

The structure looks like this:

```json
{
  "deck_name": "Your Deck Name",
  "deck_id": YOUR_DECK_ID,
  "notetype_id": YOUR_NOTETYPE_ID,
  "tools_repo": "oprobiu/AFAS",
  "tools_version": "v1.0.0",
  "fields": [
    {"name": "fo_word", "csv": "fo_word"},
    {"name": "fo_sentence", "csv": "fo_sentence"},
    {"name": "na_word", "csv": "na_word"},
    {"name": "na_sentence", "csv": "na_sentence"},
    {"name": "na_note", "csv": "na_note"},
    {"name": "fo_sentence_audio", "csv": "fo_sentence_audio"},
    {"name": "fo_word_audio", "csv": "fo_word_audio"}
  ],
  "templates": [
    {
      "name": "FO→NA",
      "front": "{{fo_word}} {{fo_word_audio}}\n{{#fo_sentence}}\n<br><br>\n<i>{{fo_sentence}}</i>\n{{/fo_sentence}}",
      "back": "{{FrontSide}}\n<hr id=answer>\n{{na_word}}\n{{#na_sentence}}\n<br><br>\n<i>{{na_sentence}}</i>\n{{/na_sentence}}"
    },
    {
      "name": "NA→FO",
      "front": "{{na_word}}\n{{#na_sentence}}\n<br><br>\n<i>{{na_sentence}}</i>\n{{/na_sentence}}",
      "back": "{{FrontSide}}\n<hr id=answer>\n{{fo_word}} {{fo_word_audio}}\n{{#fo_sentence}}\n<br><br>\n<i>{{fo_sentence}}</i>\n{{/fo_sentence}}"
    }
  ]
}
```

`fields`: each entry has a `name` (shown in Anki) and `csv` (column name in notes.csv). `fo_` = foreign language, `na_` = native language.

`templates`: use `{{FieldName}}` to reference fields. `{{FrontSide}}` shows the front on the back.

No audio? Leave out the audio field and templates that reference it. No reverse cards? Use a single template.

## 3. Edit notes.csv

Columns = the `csv` values from your fields + `tags`. Leave audio columns empty.

```csv
fo_word,fo_sentence,na_word,na_sentence,na_note,fo_sentence_audio,fo_word_audio,tags
hello,,ciao,,,,GREETING
cat,The cat sleeps.,gatto,Il gatto dorme.,,,,NOUN
```

## 4. (Optional) Add TTS audio

Find voices for your language:
```bash
python3 scripts/list_voices.py --language it
python3 scripts/list_voices.py --language ja
python3 scripts/list_voices.py --language fr
python3 scripts/list_voices.py                  # all languages
```

Add a `tts` block to deck.json at the top level, next to `deck_name`. Two engines are supported:

**edge-tts** (multiple voices):
```json
"tts": {
  "engine": "edge-tts",
  "language": "it-IT",
  "voices": ["it-IT-ElsaNeural", "it-IT-DiegoNeural"],
  "targets": [
    {
      "field": "audio",
      "source": "front",
      "prefix": "word"
    }
  ]
}
```

**gtts** (Google Translate TTS, single voice):
```json
"tts": {
  "engine": "gtts",
  "language": "it",
  "voices": [],
  "targets": [
    {
      "field": "audio",
      "source": "front",
      "prefix": "word"
    }
  ]
}
```

Each target maps a text column (`source`) to an audio column (`field`). You can have multiple targets, for example word audio and sentence audio.

Generate:
```bash
python3 scripts/regenerate_tts.py --config ~/MyDeck/data/deck.json --dry-run       # preview
python3 scripts/regenerate_tts.py --config ~/MyDeck/data/deck.json --write-csv     # generate
```

## 5. Validate and build

```bash
python3 scripts/validate.py --config ~/MyDeck/data/deck.json --tools-dir .
python3 scripts/build_apkg.py --config ~/MyDeck/data/deck.json --tools-dir .
```

Import `~/MyDeck/build/Your_Deck_Name.apkg` into Anki.

Want to push this to GitHub? See [github.md](github.md).

---

## Full example: Italian vocabulary

A deck with word + sentence fields, two templates, and TTS audio in 4 Italian voices.

<details>
<summary>deck.json</summary>

```json
{
  "deck_name": "Italian Vocab",
  "deck_id": 4827193650412,
  "notetype_id": 7391058264130,
  "tools_repo": "oprobiu/AFAS",
  "tools_version": "v1.0.0",
  "fields": [
    {"name": "fo_word", "csv": "fo_word"},
    {"name": "fo_sentence", "csv": "fo_sentence"},
    {"name": "na_word", "csv": "na_word"},
    {"name": "na_sentence", "csv": "na_sentence"},
    {"name": "na_note", "csv": "na_note"},
    {"name": "fo_sentence_audio", "csv": "fo_sentence_audio"},
    {"name": "fo_word_audio", "csv": "fo_word_audio"}
  ],
  "templates": [
    {
      "name": "FO→NA",
      "front": "{{fo_word}} {{fo_word_audio}}\n{{#fo_sentence}}<br><br><i>{{fo_sentence}}</i>{{/fo_sentence}}",
      "back": "{{FrontSide}}\n<hr>\n{{na_word}}\n{{#na_sentence}}<br><br><i>{{na_sentence}}</i>{{/na_sentence}}"
    },
    {
      "name": "NA→FO",
      "front": "{{na_word}}\n{{#na_sentence}}<br><br><i>{{na_sentence}}</i>{{/na_sentence}}",
      "back": "{{FrontSide}}\n<hr>\n{{fo_word}} {{fo_word_audio}}\n{{#fo_sentence}}<br><br><i>{{fo_sentence}}</i>{{/fo_sentence}}"
    }
  ],
  "tts": {
    "engine": "edge-tts",
    "language": "it-IT",
    "voices": [
      "it-IT-ElsaNeural",
      "it-IT-DiegoNeural",
      "it-IT-IsabellaNeural",
      "it-IT-GiuseppeMultilingualNeural"
    ],
    "targets": [
      {"field": "fo_word_audio", "source": "fo_word", "prefix": "word"},
      {"field": "fo_sentence_audio", "source": "fo_sentence", "prefix": "sent"}
    ]
  }
}
```
</details>

<details>
<summary>notes.csv</summary>

```csv
fo_word,fo_sentence,na_word,na_sentence,na_note,fo_sentence_audio,fo_word_audio,tags
ciao,Ciao come stai?,hello,Hello how are you?,,,,GREETING
gatto,Il gatto dorme sul divano.,cat,The cat sleeps on the couch.,,,,NOUN
mangiare,Voglio mangiare una pizza.,to eat,I want to eat a pizza.,,,,VERB
bello,Che bel giorno!,beautiful,What a beautiful day!,,,,ADJ
casa,La mia casa è grande.,house,My house is big.,,,,NOUN
```
</details>

```bash
cd /path/to/AFAS
python3 scripts/regenerate_tts.py --config ~/ItalianDeck/data/deck.json --write-csv
python3 scripts/validate.py --config ~/ItalianDeck/data/deck.json --tools-dir .
python3 scripts/build_apkg.py --config ~/ItalianDeck/data/deck.json --tools-dir .
```
