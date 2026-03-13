# Guide

Python 3.8+. Install dependencies: `pip install -r requirements.txt`

## Getting started

Pick one:

- **[From an existing .apkg](docs/from-apkg.md)** Unpack a shared deck, optionally add TTS, rebuild.
- **[From scratch](docs/from-scratch.md)** Scaffold a new dataset, define fields and templates, add cards.

## Reference

### Scripts

| Script | What it does |
|---|---|
| `init_dataset.py` | Scaffold a new dataset directory with example files |
| `init_repo.py` | Add GitHub Actions workflow, Makefile, bootstrap.sh to a dataset |
| `unpack_apkg.py` | .apkg to CSV + media + deck.json |
| `build_apkg.py` | CSV + media to .apkg |
| `validate.py` | Check CSV, audio refs, config. Use `--clean-orphans` to delete unused media |
| `regenerate_tts.py` | Generate edge-tts audio for any language. Use `--dry-run` to preview |
| `list_voices.py` | List available TTS voices. Use `--language <code>` to filter |

### deck.json

| Key | Required | What it is |
|---|---|---|
| `deck_name` | yes | Shows up in Anki |
| `deck_id` | yes | Random number, unique per collection |
| `notetype_id` | yes | Random number, unique per collection |
| `tools_repo` | yes | `oprobiu/AFAS` |
| `tools_version` | yes | Tag like `v1.0.0` |
| `fields` | no | `[{name, csv}, ...]` You define your own, or omit to get defaults |
| `templates` | no | `[{name, front, back}, ...]` You define your own, or omit to get defaults |
| `css` | no | Card styling string. Default is 20px Arial, centered, blue replay button |
| `template_files` | no | `{css: "path", templates: "path"}` to load from files instead of inline |
| `tts` | no | TTS config. Skip for decks without audio |

### TTS targets

Each entry in `tts.targets`:

| Option | Required | What it does |
|---|---|---|
| `field` | yes | CSV column where `[sound:filename.mp3]` gets written |
| `source` | yes | CSV column to read the text from |
| `prefix` | yes | Goes in the generated filename |
| `strip_html` | no | Strips HTML tags, `[sound:]` refs, and parenthetical text before speaking. Use for shared decks with messy fields |
| `dialogue` | no | Two-speaker audio: `{"enabled": true, "female_marker": "...", "male_marker": "..."}` |

### Re-generating TTS

When you regenerate after changing voices or adding cards, old audio files become orphans.

`validate.py --clean-orphans` deletes unreferenced media files. Without the flag, it lists them and prints a ready-to-run `rm` command. `build_apkg.py` also skips orphans automatically, only referenced files go into the .apkg.
