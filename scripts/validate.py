#!/usr/bin/env python3
"""
Validate a dataset repo. Fully config-driven.

Reads field definitions from deck.json to know what CSV columns to expect.
Reads tts.targets to know which fields contain audio refs.
If no tts key, skips audio validation.

Usage:
  python3 validate.py --config data/deck.json --tools-dir .tools/AFAS
  python3 validate.py --config data/deck.json --tools-dir .tools/AFAS --clean-orphans
"""

import argparse, csv, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_loader import load_config


def collect_all_media_refs(notes, fields):
    """Collect all media filenames referenced by any note field."""
    refs = set()
    for row in notes:
        for f in fields:
            val = row.get(f["csv"], "")
            for m in re.findall(r'\[sound:([^\]]+)\]', val):
                refs.add(m)
            for m in re.findall(r'<img src="([^"]+)"', val):
                refs.add(m)
    return refs


def validate(config_path, tools_dir, clean_orphans=False):
    config = load_config(config_path, tools_dir)
    root = config["_root"]

    notes_csv = os.path.join(root, "data", "notes.csv")
    media_dir = os.path.join(root, "media_files")

    print(f"")
    print(f"=== Validate Dataset ===")
    print(f"")
    print(f"  Config: {config_path}")
    print(f"  Deck:   {config['deck_name']}")
    print(f"")

    errors = 0
    warnings = 0

    # --- Check CSV exists and has correct fields ---
    print(f"--- Checking CSV structure")
    if not os.path.exists(notes_csv):
        print(f"  ERROR: {notes_csv} not found")
        return 1

    with open(notes_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        actual_fields = reader.fieldnames
        notes = list(reader)

    print(f"  Notes: {len(notes)}")
    print(f"  Fields: {', '.join(actual_fields)}")

    expected = set(config["csv_columns"])
    actual = set(actual_fields)
    missing_fields = expected - actual
    extra_fields = actual - expected
    if missing_fields:
        print(f"  ERROR: Missing fields: {missing_fields}")
        errors += 1
    if extra_fields:
        print(f"  WARN:  Extra fields: {extra_fields}")
        warnings += 1
    if not missing_fields and not extra_fields:
        print(f"  OK:    Fields match config schema")

    # --- Check unique note IDs ---
    id_field = config["fields"][0]["csv"]
    print(f"\n--- Checking IDs (field: {id_field})")
    ids = [r.get(id_field, "") for r in notes]
    dupes = len(ids) - len(set(ids))
    empty_ids = sum(1 for i in ids if not i.strip())
    if dupes:
        print(f"  ERROR: {dupes} duplicate values")
        errors += 1
    if empty_ids:
        print(f"  ERROR: {empty_ids} empty values")
        errors += 1
    if not dupes and not empty_ids:
        print(f"  OK:    {len(ids)} unique IDs")

    # --- Collect all media refs from all fields ---
    all_refs = collect_all_media_refs(notes, config["fields"])
    media_on_disk = set(os.listdir(media_dir)) if os.path.isdir(media_dir) else set()

    # --- Check audio refs per TTS target ---
    tts_cfg = config.get("tts")
    if tts_cfg and tts_cfg.get("targets"):
        print(f"\n--- Checking audio references")
        print(f"  Files on disk: {len(media_on_disk)}")

        for target in tts_cfg["targets"]:
            field = target["field"]
            source = target["source"]
            label = target.get("prefix", field)

            ok = missing_file = missing_ref = stale = 0
            for r in notes:
                ref = r.get(field, "").strip()
                source_text = re.sub(r"<[^>]+>", "", r.get(source, "")).strip()

                if not source_text or source_text == "-":
                    if ref:
                        stale += 1
                    continue
                if not ref:
                    missing_ref += 1
                    continue
                fname = ref.replace("[sound:", "").replace("]", "")
                if fname in media_on_disk:
                    ok += 1
                else:
                    missing_file += 1

            print(f"  {label} ({field}):")
            print(f"    OK:           {ok}")
            print(f"    Missing ref:  {missing_ref}")
            print(f"    Missing file: {missing_file}")
            print(f"    Stale ref:    {stale}")
            if missing_file:
                errors += missing_file
            if missing_ref:
                warnings += missing_ref
    else:
        print(f"\n--- No TTS config -- skipping audio validation")

    # --- Orphan check (uses all_refs from ALL fields, not just TTS) ---
    print(f"\n--- Checking for orphan media files")
    orphans = media_on_disk - all_refs
    if orphans:
        print(f"  WARN:  {len(orphans)} media files not referenced by any card")
        if clean_orphans:
            for f in sorted(orphans):
                os.remove(os.path.join(media_dir, f))
            print(f"  OK:    Deleted {len(orphans)} orphan files")
        else:
            print(f"")
            for f in sorted(orphans):
                print(f"    {f}")
            print(f"")
            print(f"  To delete them:")
            print(f"    cd {media_dir} && rm {' '.join(sorted(orphans)[:10])}", end="")
            if len(orphans) > 10:
                print(f" ... ({len(orphans) - 10} more)")
            else:
                print()
            print(f"  Or rerun with --clean-orphans")
            warnings += 1
    else:
        print(f"  OK:    All media files referenced")

    # --- Check deck.json required keys ---
    print(f"\n--- Checking deck.json")
    required_keys = ["deck_name", "deck_id", "notetype_id", "tools_repo", "tools_version"]
    missing_keys = [k for k in required_keys if k not in config]
    if missing_keys:
        for k in missing_keys:
            print(f"  ERROR: Missing key: {k}")
            errors += 1
    else:
        print(f"  OK:    All required keys present")

    # --- Summary ---
    print(f"\n{'='*50}")
    if errors == 0 and warnings == 0:
        print(f"  PASS: No issues found.")
    elif errors == 0:
        print(f"  PASS: {warnings} warning(s).")
    else:
        print(f"  FAIL: {errors} error(s), {warnings} warning(s).")
    print(f"{'='*50}")

    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description="Validate dataset")
    parser.add_argument("--config", required=True, help="Path to deck.json")
    parser.add_argument("--tools-dir", required=True, help="Path to AFAS tools directory")
    parser.add_argument("--clean-orphans", action="store_true",
                        help="Delete media files not referenced by any card")
    args = parser.parse_args()
    sys.exit(validate(args.config, args.tools_dir, args.clean_orphans))


if __name__ == "__main__":
    main()
