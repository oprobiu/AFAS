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
    {"name": "ID", "csv": "id"},
    {"name": "Front", "csv": "front"},
    {"name": "Back", "csv": "back"},
    {"name": "Audio", "csv": "audio"}
  ],
  "templates": [
    {
      "name": "Forward",
      "front": "{{Front}} {{Audio}}",
      "back": "{{FrontSide}}\n<hr>\n{{Back}}"
    },
    {
      "name": "Reverse",
      "front": "{{Back}}",
      "back": "{{FrontSide}}\n<hr>\n{{Front}} {{Audio}}"
    }
  ]
}
```

`fields`: each entry has a `name` (shown in Anki) and `csv` (column name in notes.csv).

`templates`: use `{{FieldName}}` to reference fields. `{{FrontSide}}` shows the front on the back.

No audio? Leave out the audio field and templates that reference it. No reverse cards? Use a single template.

## 3. Edit notes.csv

Columns = the `csv` values from your fields + `tags`. Leave audio columns empty.

```csv
id,front,back,audio,tags
1,hello,ciao,,GREETING
2,cat,gatto,,NOUN
```

## 4. (Optional) Add TTS audio

Find voices for your language:
```bash
python3 scripts/list_voices.py --language it
python3 scripts/list_voices.py --language ja
python3 scripts/list_voices.py --language fr
python3 scripts/list_voices.py                  # all languages
```

Add a `tts` block to deck.json at the top level, next to `deck_name`:
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
    {"name": "ID", "csv": "id"},
    {"name": "Word", "csv": "word"},
    {"name": "Sentence", "csv": "sentence"},
    {"name": "Translation", "csv": "translation"},
    {"name": "Sentence Translation", "csv": "sentence_translation"},
    {"name": "Word Audio", "csv": "word_audio"},
    {"name": "Sentence Audio", "csv": "sentence_audio"}
  ],
  "templates": [
    {
      "name": "IT to EN",
      "front": "{{Word}} {{Word Audio}}\n{{#Sentence}}<br><br><i>{{Sentence}}</i>{{/Sentence}}\n{{Sentence Audio}}",
      "back": "{{FrontSide}}\n<hr>\n{{Translation}}\n{{#Sentence Translation}}<br><br><i>{{Sentence Translation}}</i>{{/Sentence Translation}}"
    },
    {
      "name": "EN to IT",
      "front": "{{Translation}}\n{{#Sentence Translation}}<br><br><i>{{Sentence Translation}}</i>{{/Sentence Translation}}",
      "back": "{{FrontSide}}\n<hr>\n{{Word}} {{Word Audio}}\n{{#Sentence}}<br><br><i>{{Sentence}}</i>{{/Sentence}}\n{{Sentence Audio}}"
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
      {"field": "word_audio", "source": "word", "prefix": "word"},
      {"field": "sentence_audio", "source": "sentence", "prefix": "sent"}
    ]
  }
}
```
</details>

<details>
<summary>notes.csv</summary>

```csv
id,word,sentence,translation,sentence_translation,word_audio,sentence_audio,tags
1,ciao,Ciao come stai?,hello,Hello how are you?,,,GREETING
2,gatto,Il gatto dorme sul divano.,cat,The cat sleeps on the couch.,,,NOUN
3,mangiare,Voglio mangiare una pizza.,to eat,I want to eat a pizza.,,,VERB
4,bello,Che bel giorno!,beautiful,What a beautiful day!,,,ADJ
5,casa,La mia casa è grande.,house,My house is big.,,,NOUN
```
</details>

```bash
cd /path/to/AFAS
python3 scripts/regenerate_tts.py --config ~/ItalianDeck/data/deck.json --write-csv
python3 scripts/validate.py --config ~/ItalianDeck/data/deck.json --tools-dir .
python3 scripts/build_apkg.py --config ~/ItalianDeck/data/deck.json --tools-dir .
```
