# From an existing .apkg

You have an Anki deck (.apkg file) from AnkiWeb, exported from Anki, etc.

## Before you start

Python 3.8+. Run everything from the AFAS directory.

```bash
pip install -r requirements.txt
cd /path/to/AFAS
```

## 1. Unpack it

```bash
python3 scripts/unpack_apkg.py --input MyDeck.apkg --output-dir ~/MyDataset
```

You get:
```
MyDataset/
├── data/
│   ├── deck.json       config with IDs, fields, templates from the .apkg
│   ├── notes.csv       your cards
│   ├── note_meta.csv   Anki internal IDs
│   └── card_meta.csv
└── media_files/
```

## 2. Look at deck.json

It has the deck ID, notetype ID, field names, and card templates from your .apkg. Make sure it looks right.

Field names come from the Anki notetype. They can be anything: `word`, `front`, `de_word`, whatever. The scripts just need CSV columns to match what deck.json says.

## 3. (Optional) Add TTS audio

If you want text-to-speech audio on your cards, add an audio field and a `tts` block to deck.json.

Add an audio field to the `fields` array and reference it in your template:
```json
"fields": [
  {"name": "Front", "csv": "front"},
  {"name": "Back", "csv": "back"},
  {"name": "Audio", "csv": "audio"}
],
"templates": [
  {
    "name": "Card 1",
    "front": "{{Front}} {{Audio}}",
    "back": "{{FrontSide}}\n<hr>\n{{Back}}"
  }
]
```

Then add the `tts` block at the top level of deck.json, next to `deck_name`. Pick voices from:
```bash
python3 scripts/list_voices.py --language it    # or de, fr, ja, zh, etc.
```

```json
"tts": {
  "engine": "edge-tts",
  "language": "it-IT",
  "voices": ["it-IT-ElsaNeural", "it-IT-DiegoNeural"],
  "targets": [
    {
      "field": "audio",
      "source": "front",
      "prefix": "word",
      "strip_html": true
    }
  ]
}
```

Shared decks often have HTML, images, links, and promo text mixed into fields. `strip_html` cleans all of that before speaking. It strips HTML tags, `[sound:]` refs, and cuts at the first parenthesis so only the actual word or phrase gets spoken. Use it whenever the source field might contain more than plain text.

The `audio` column gets added to notes.csv automatically when you run `--write-csv`. Generate:
```bash
python3 scripts/regenerate_tts.py --config ~/MyDataset/data/deck.json --dry-run       # preview
python3 scripts/regenerate_tts.py --config ~/MyDataset/data/deck.json --write-csv     # generate
```

## 4. Edit notes.csv

Add, remove, change cards. Column names match the `csv` values in deck.json.

## 5. Validate and build

```bash
python3 scripts/validate.py --config ~/MyDataset/data/deck.json --tools-dir .
python3 scripts/build_apkg.py --config ~/MyDataset/data/deck.json --tools-dir .
```

Output goes to `MyDataset/build/`. Import the .apkg into Anki.

Want to push this to GitHub? See [github.md](github.md).
