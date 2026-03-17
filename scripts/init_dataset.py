#!/usr/bin/env python3
"""
Scaffold a new dataset directory with example files ready to edit and build.

Usage:
  python3 init_dataset.py ~/MyDeck
  python3 init_dataset.py /path/to/NewDataset
"""

import argparse, csv, json, os, random, sys


def init_dataset(output_dir):
    output_dir = os.path.abspath(output_dir)
    data_dir = os.path.join(output_dir, "data")
    media_dir = os.path.join(output_dir, "media_files")

    if os.path.exists(os.path.join(data_dir, "deck.json")):
        print(f"ERROR: {data_dir}/deck.json already exists. Aborting.")
        return 1

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(media_dir, exist_ok=True)

    deck_id = random.randint(10**12, 10**13)
    notetype_id = random.randint(10**12, 10**13)

    # --- deck.json ---
    config = {
        "_comment": "Edit this file. See GUIDE.md in AFAS for details.",
        "deck_name": "My Deck",
        "deck_id": deck_id,
        "notetype_id": notetype_id,
        "tools_repo": "oprobiu/AFAS",
        "tools_version": "v1.0.0",
        "fields": [
            {"name": "fo_word", "csv": "fo_word", "_comment": "word or phrase in foreign language"},
            {"name": "fo_sentence", "csv": "fo_sentence", "_comment": "example sentence"},
            {"name": "na_word", "csv": "na_word", "_comment": "translation in native language"},
            {"name": "na_sentence", "csv": "na_sentence", "_comment": "translated sentence"},
            {"name": "na_note", "csv": "na_note", "_comment": "optional note"},
            {"name": "fo_sentence_audio", "csv": "fo_sentence_audio", "_comment": "leave empty -- TTS fills this in"},
            {"name": "fo_word_audio", "csv": "fo_word_audio", "_comment": "leave empty -- TTS fills this in"},
        ],
        "templates": [
            {
                "name": "FO→NA",
                "front": "{{fo_word}} {{fo_word_audio}}\n{{#fo_sentence}}\n<br><br>\n<i>{{fo_sentence}}</i>\n{{/fo_sentence}}",
                "back": "{{FrontSide}}\n<hr id=answer>\n{{na_word}}\n{{#na_sentence}}\n<br><br>\n<i>{{na_sentence}}</i>\n{{/na_sentence}}",
            },
            {
                "name": "NA→FO",
                "front": "{{na_word}}\n{{#na_sentence}}\n<br><br>\n<i>{{na_sentence}}</i>\n{{/na_sentence}}",
                "back": "{{FrontSide}}\n<hr id=answer>\n{{fo_word}} {{fo_word_audio}}\n{{#fo_sentence}}\n<br><br>\n<i>{{fo_sentence}}</i>\n{{/fo_sentence}}",
            },
        ],
        "_tts_comment": "Uncomment and edit the tts block below to enable audio generation. Run: python3 scripts/list_voices.py --language <code> to find voices.",
        "_tts_example": {
            "engine": "edge-tts",
            "language": "CHANGE-ME",
            "voices": ["CHANGE-ME-Voice1", "CHANGE-ME-Voice2"],
            "targets": [
                {
                    "field": "fo_word_audio",
                    "source": "fo_word",
                    "prefix": "word",
                    "strip_html": True,
                }
            ],
        },
    }

    config_path = os.path.join(data_dir, "deck.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    # --- notes.csv ---
    notes_path = os.path.join(data_dir, "notes.csv")
    with open(notes_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["fo_word", "fo_sentence", "na_word", "na_sentence", "na_note", "fo_sentence_audio", "fo_word_audio", "tags"], lineterminator="\n")
        writer.writeheader()
        writer.writerow({"fo_word": "hello", "fo_sentence": "", "na_word": "ciao", "na_sentence": "", "na_note": "", "fo_sentence_audio": "", "fo_word_audio": "", "tags": "GREETING"})
        writer.writerow({"fo_word": "cat", "fo_sentence": "The cat sleeps.", "na_word": "gatto", "na_sentence": "Il gatto dorme.", "na_note": "", "fo_sentence_audio": "", "fo_word_audio": "", "tags": "NOUN"})
        writer.writerow({"fo_word": "to eat", "fo_sentence": "I eat bread.", "na_word": "mangiare", "na_sentence": "Mangio il pane.", "na_note": "", "fo_sentence_audio": "", "fo_word_audio": "", "tags": "VERB"})

    # --- .gitignore ---
    gitignore_path = os.path.join(output_dir, ".gitignore")
    with open(gitignore_path, "w") as f:
        f.write("build/\n.tools/\n")

    # --- README.md ---
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write(f"# {os.path.basename(output_dir)}\n\n")
        f.write("Anki flashcard dataset. Built with [AFAS](https://github.com/oprobiu/AFAS).\n")

    # --- Summary ---
    print(f"")
    print(f"=== Dataset initialized ===")
    print(f"")
    print(f"  {config_path}")
    print(f"  {notes_path}  (3 example cards)")
    print(f"  {gitignore_path}")
    print(f"  {readme_path}")
    print(f"  {media_dir}/")
    print(f"")
    print(f"  deck_id:     {deck_id}")
    print(f"  notetype_id: {notetype_id}")
    print(f"")
    print(f"Next steps:")
    print(f"  1. Edit data/deck.json -- change deck_name, fields, templates")
    print(f"  2. Edit data/notes.csv -- add your cards")
    print(f"  3. To add TTS: rename '_tts_example' to 'tts' in deck.json,")
    print(f"     fill in language and voices")
    print(f"     Run: python3 scripts/list_voices.py --language <code>")
    print(f"  4. python3 scripts/validate.py --config {config_path} --tools-dir .")
    print(f"  5. python3 scripts/build_apkg.py --config {config_path} --tools-dir .")
    print(f"")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Scaffold a new dataset directory")
    parser.add_argument("output_dir", help="Where to create the dataset")
    args = parser.parse_args()
    sys.exit(init_dataset(args.output_dir))


if __name__ == "__main__":
    main()
