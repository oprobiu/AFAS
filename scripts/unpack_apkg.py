#!/usr/bin/env python3
"""
Unpack an .apkg file into a ready-to-use dataset directory.

Creates:
  data/notes.csv       - all notes
  data/deck.json       - config with IDs extracted from the .apkg
  data/note_meta.csv   - Anki internal note IDs/GUIDs
  data/card_meta.csv   - Anki internal card IDs
  media_files/         - all media files

Usage:
  python3 unpack_apkg.py --input deck.apkg --output-dir ./MyDataset
"""

import argparse, csv, json, os, sqlite3, sys, tempfile, zipfile


def unpack(input_path, output_dir):
    print(f"")
    print(f"=== Unpack .apkg ===")
    print(f"")
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_dir}")
    print(f"")

    os.makedirs(output_dir, exist_ok=True)
    data_dir = os.path.join(output_dir, "data")
    media_dir = os.path.join(output_dir, "media_files")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(media_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        # Extract zip
        print(f"--- Extracting archive")
        with zipfile.ZipFile(input_path, "r") as zf:
            zf.extractall(tmp)
            print(f"  Extracted {len(zf.namelist())} entries")

        # Read media map
        media_map_path = os.path.join(tmp, "media")
        if os.path.exists(media_map_path):
            with open(media_map_path) as f:
                media_map = json.load(f)
        else:
            media_map = {}

        # Copy media files
        print(f"\n--- Copying {len(media_map)} media files")
        copied = 0
        for idx_str, filename in media_map.items():
            src = os.path.join(tmp, idx_str)
            dst = os.path.join(media_dir, filename)
            if os.path.exists(src):
                with open(src, "rb") as sf, open(dst, "wb") as df:
                    df.write(sf.read())
                copied += 1
        print(f"  OK: {copied} files copied")

        # Read SQLite
        db_path = os.path.join(tmp, "collection.anki2")
        if not os.path.exists(db_path):
            db_path = os.path.join(tmp, "collection.anki21")
        if not os.path.exists(db_path):
            print(f"  ERROR: No collection database found")
            return 1

        print(f"\n--- Reading database")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Get deck info
        cur.execute("SELECT decks FROM col")
        decks = json.loads(cur.fetchone()[0])
        deck_id = None
        deck_name = None
        for did, d in decks.items():
            if d["name"] != "Default" or len(decks) == 1:
                deck_id = int(did)
                deck_name = d["name"]
                break
        if deck_id is None:
            deck_id = int(list(decks.keys())[0])
            deck_name = list(decks.values())[0]["name"]
        print(f"  Deck: {deck_name} (ID: {deck_id})")

        # Get model info
        cur.execute("SELECT models FROM col")
        models = json.loads(cur.fetchone()[0])
        mid = list(models.keys())[0]
        model = models[mid]
        notetype_id = int(mid)
        notetype_name = model["name"]
        field_defs = model["flds"]
        field_names = [f["name"] for f in field_defs]
        template_defs = model["tmpls"]
        css = model.get("css", "")
        print(f"  Notetype: {notetype_name} (ID: {notetype_id})")
        print(f"  Fields: {', '.join(field_names)}")
        print(f"  Templates: {len(template_defs)}")

        # Get notes
        cur.execute("SELECT id, guid, mid, mod, tags, flds, sfld FROM notes")
        rows = cur.fetchall()
        print(f"  Notes: {len(rows)}")

        # Get cards
        cur.execute("SELECT id, nid, ord FROM cards")
        cards = cur.fetchall()
        print(f"  Cards: {len(cards)}")

        conn.close()

        # --- Write notes.csv ---
        print(f"\n--- Writing CSV")
        csv_names = [n.lower().replace(" ", "_") for n in field_names] + ["tags"]

        notes_path = os.path.join(data_dir, "notes.csv")
        with open(notes_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=csv_names, lineterminator='\n')
            writer.writeheader()
            for note_id, guid, mid_val, mod, tags, flds, sfld in rows:
                values = flds.split("\x1f")
                row = {}
                for j, name in enumerate(csv_names[:-1]):
                    row[name] = values[j] if j < len(values) else ""
                row["tags"] = tags.strip()
                writer.writerow(row)
        print(f"  OK: {notes_path}")

        # --- Write note_meta.csv ---
        meta_path = os.path.join(data_dir, "note_meta.csv")
        with open(meta_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["anki_note_id", "field_note_id", "guid", "mod"], lineterminator='\n')
            writer.writeheader()
            for note_id, guid, mid_val, mod, tags, flds, sfld in rows:
                values = flds.split("\x1f")
                writer.writerow({
                    "anki_note_id": note_id,
                    "field_note_id": values[0] if values else "",
                    "guid": guid,
                    "mod": mod,
                })
        print(f"  OK: {meta_path}")

        # --- Write card_meta.csv ---
        card_meta_path = os.path.join(data_dir, "card_meta.csv")
        with open(card_meta_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["card_id", "anki_note_id", "ord"], lineterminator='\n')
            writer.writeheader()
            for card_id, nid, ord_num in cards:
                writer.writerow({"card_id": card_id, "anki_note_id": nid, "ord": ord_num})
        print(f"  OK: {card_meta_path}")

        # --- Write deck.json ---
        print(f"\n--- Generating deck.json")
        deck_config = {
            "deck_name": deck_name,
            "deck_id": deck_id,
            "notetype_id": notetype_id,
            "notetype_name": notetype_name,
            "tools_repo": "oprobiu/AFAS",
            "tools_version": "v1.0.0",
            "fields": [
                {"name": fn, "csv": fn.lower().replace(" ", "_")}
                for fn in field_names
            ],
            "templates": [
                {
                    "name": t["name"],
                    "front": t["qfmt"],
                    "back": t["afmt"],
                }
                for t in template_defs
            ],
            "css": css,
        }

        config_path = os.path.join(data_dir, "deck.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(deck_config, f, indent=2, ensure_ascii=False)
        print(f"  OK: {config_path}")

    # --- Summary ---
    afas_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    abs_config = os.path.abspath(config_path)
    print(f"\n{'='*50}")
    print(f"  Unpacked to {output_dir}")
    print(f"")
    print(f"    data/deck.json     -- deck config (IDs, fields, templates)")
    print(f"    data/notes.csv     -- {len(rows)} notes")
    print(f"    data/note_meta.csv -- Anki internal IDs")
    print(f"    data/card_meta.csv -- Anki card IDs")
    print(f"    media_files/       -- {copied} files")
    print(f"")
    print(f"  Next steps (run from the AFAS directory: {afas_dir}):")
    print(f"    1. Review data/deck.json -- edit deck_name, add tts config")
    print(f"    2. Review data/notes.csv -- edit/add cards")
    print(f"    3. python3 scripts/validate.py --config {abs_config} --tools-dir {afas_dir}")
    print(f"    4. python3 scripts/build_apkg.py --config {abs_config} --tools-dir {afas_dir}")
    print(f"")
    print(f"  To add TTS audio, add a 'tts' section to deck.json.")
    print(f"  Run: python3 scripts/list_voices.py --language <code>")
    print(f"  See GUIDE.md for details.")
    print(f"{'='*50}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Unpack .apkg to dataset directory")
    parser.add_argument("--input", required=True, help="Path to .apkg file")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    args = parser.parse_args()
    sys.exit(unpack(args.input, args.output_dir))


if __name__ == "__main__":
    main()
