#!/usr/bin/env python3
"""
Build .apkg Anki deck from a dataset repo.

Reads fields, templates, and CSS from deck.json. Falls back to AFAS defaults
if not specified. Supports any number of templates and any field layout.

Usage:
  python3 build_apkg.py --config data/deck.json --tools-dir .tools/AFAS
"""

import argparse, csv, json, os, sys, time

try:
    import genanki
except ImportError:
    print("ERROR: 'genanki' not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

# Allow importing config_loader from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_loader import load_config


def build(config_path, tools_dir):
    start = time.time()
    config = load_config(config_path, tools_dir)
    root = config["_root"]

    notes_csv = os.path.join(root, "data", "notes.csv")
    media_dir = os.path.join(root, "media_files")
    build_dir = os.path.join(root, "build")

    print(f"")
    print(f"=== Build .apkg ===")
    print(f"")
    print(f"  Config:     {config_path}")
    print(f"  Deck:       {config['deck_name']}")
    print(f"  Tools:      {tools_dir}")
    print(f"  Fields:     {len(config['anki_fields'])}")
    print(f"  Templates:  {len(config['templates'])}")
    print(f"")

    # Read notes
    print(f"--- Reading notes from {notes_csv}")
    with open(notes_csv, encoding="utf-8") as f:
        notes = list(csv.DictReader(f))
    print(f"  Found {len(notes)} notes")

    # Audio stats
    audio_fields = [f["csv"] for f in config["fields"] if any(
        "[sound:" in r.get(f["csv"], "") for r in notes[:10]
    )]
    for af in audio_fields:
        count = sum(1 for r in notes if "[sound:" in r.get(af, ""))
        print(f"  With {af}: {count}")

    tags = {}
    for r in notes:
        t = r.get("tags", "").strip()
        if t:
            tags[t] = tags.get(t, 0) + 1
    if tags:
        print(f"  Tags: {', '.join(f'{t}={c}' for t, c in sorted(tags.items()))}")

    # Build model
    print(f"\n--- Building Anki model")
    genanki_templates = []
    for tmpl in config["templates"]:
        genanki_templates.append({
            "name": tmpl["name"],
            "qfmt": tmpl["front"],
            "afmt": tmpl["back"],
        })

    model = genanki.Model(
        config["notetype_id"],
        config.get("notetype_name", "afas-deck"),
        fields=[{"name": n} for n in config["anki_fields"]],
        templates=genanki_templates,
        css=config["css"],
    )
    for tmpl in config["templates"]:
        print(f"  Template: {tmpl['name']}")

    # Build deck
    n_templates = len(config["templates"])
    print(f"\n--- Building deck '{config['deck_name']}'")
    deck = genanki.Deck(config["deck_id"], config["deck_name"])

    csv_to_anki = {f["csv"]: f["name"] for f in config["fields"]}
    for row in notes:
        fields = [row.get(f["csv"], "") for f in config["fields"]]
        note = genanki.Note(
            model=model,
            fields=fields,
            tags=[row.get("tags", "").strip()] if row.get("tags", "").strip() else [],
        )
        deck.add_note(note)
    total_cards = len(notes) * n_templates
    print(f"  Added {len(notes)} notes ({total_cards} cards)")

    # Collect media — only files referenced by notes
    print(f"\n--- Collecting media from {media_dir}")
    referenced = set()
    for row in notes:
        for f in config["fields"]:
            val = row.get(f["csv"], "")
            if "[sound:" in val:
                referenced.add(val.replace("[sound:", "").replace("]", ""))
            if "<img src=" in val:
                import re as _re
                for m in _re.findall(r'<img src="([^"]+)"', val):
                    referenced.add(m)

    all_media = set(os.listdir(media_dir)) if os.path.isdir(media_dir) else set()
    media_files = sorted(referenced & all_media)
    skipped = len(all_media) - len(media_files)
    media_paths = [os.path.join(media_dir, f) for f in media_files]
    print(f"  Referenced: {len(media_files)} files")
    if skipped:
        print(f"  Skipped:    {skipped} orphan files (not referenced by any card)")

    # Package
    print(f"\n--- Packaging .apkg")
    os.makedirs(build_dir, exist_ok=True)
    deck_filename = config["deck_name"].replace(" ", "_") + ".apkg"
    out_path = os.path.join(build_dir, deck_filename)
    genanki.Package(deck, media_files=media_paths).write_to_file(out_path)

    size_mb = os.path.getsize(out_path) / 1024 / 1024
    elapsed = time.time() - start
    print(f"\n{'='*50}")
    print(f"  Output: {out_path}")
    print(f"  Size:   {size_mb:.1f} MB")
    print(f"  Notes:  {len(notes)}")
    print(f"  Cards:  {total_cards}")
    print(f"  Media:  {len(media_files)}")
    print(f"  Time:   {elapsed:.1f}s")
    print(f"{'='*50}")


def main():
    parser = argparse.ArgumentParser(description="Build .apkg Anki deck")
    parser.add_argument("--config", required=True, help="Path to deck.json")
    parser.add_argument("--tools-dir", required=True, help="Path to AFAS tools directory")
    args = parser.parse_args()
    build(args.config, args.tools_dir)


if __name__ == "__main__":
    main()
