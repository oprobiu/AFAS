# AFAS

Tools for building Anki flashcard decks from CSV files, with optional text-to-speech audio generation.

## Quick start

Requires Python 3.8+.

```bash
pip install -r requirements.txt

# Start a new dataset from scratch:
python3 scripts/init_dataset.py ~/MyDeck

# Or unpack an existing .apkg:
python3 scripts/unpack_apkg.py --input MyDeck.apkg --output-dir ~/MyDataset

# Edit data/notes.csv, then:
python3 scripts/validate.py --config ~/MyDataset/data/deck.json --tools-dir .
python3 scripts/build_apkg.py --config ~/MyDataset/data/deck.json --tools-dir .
```

Full walkthrough in **[GUIDE.md](GUIDE.md)**.

## Scripts

| Script | What it does |
|---|---|
| `init_dataset.py` | Scaffold a new dataset directory with example files |
| `init_repo.py` | Add GitHub Actions workflow, Makefile, bootstrap.sh to a dataset |
| `unpack_apkg.py` | .apkg to CSV + media + deck.json |
| `build_apkg.py` | CSV + media to .apkg |
| `validate.py` | Checks CSV, audio refs, config |
| `regenerate_tts.py` | Generates TTS audio (edge-tts or gTTS) for any language |
| `list_voices.py` | Lists available TTS voices |

## CI for dataset repos

Dataset repos can call the reusable workflow here instead of writing their own:

```yaml
name: Release
on:
  push:
    tags: ['v*']
jobs:
  build:
    uses: oprobiu/AFAS/.github/workflows/build-release.yml@v0.0.3
    with:
      tools-version: v0.0.3
    permissions:
      contents: write
```

## License

AGPL-3.0
