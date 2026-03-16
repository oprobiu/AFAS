#!/usr/bin/env python3
"""
Translate deck columns from one language to another using Google Translate.

Auto-translates all rows in batch, then presents flagged translations
for manual review at the end.

Flagged: identical to source, very short source, or source contains
special characters suggesting ambiguity.

Usage:
  python3 translate_deck.py --config data/deck.json \
    --source-lang de --target-lang ro \
    --columns wort_de:wort_ro satz1_de:satz1_ro \
    [--dry-run] [--write-csv]

Requires: pip install deep-translator
"""

import argparse, csv, json, os, re, sys, time

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("ERROR: 'deep-translator' not installed. Run: pip install deep-translator")
    sys.exit(1)


def strip_html(text):
    return re.sub(r'<[^>]+>', '', text)


def strip_sound_refs(text):
    return re.sub(r'\[sound:[^\]]+\]', '', text)


def clean_for_translation(text):
    """Clean text for translation, removing HTML, sound refs, etc."""
    text = strip_sound_refs(text)
    text = strip_html(text)
    text = text.strip()
    return text


def should_flag(source, translated, source_lang, target_lang):
    """Decide if a translation needs manual review."""
    if not translated or not translated.strip():
        return "empty translation"
    if translated.strip().lower() == source.strip().lower():
        return "identical to source"
    if len(source.strip()) <= 2:
        return "very short source"
    # Source has only numbers/symbols
    if re.match(r'^[\d\s\.\,\-\+\%]+$', source.strip()):
        return "numbers only"
    return None


def translate_batch(texts, source_lang, target_lang):
    """Translate a list of texts. Returns list of (translated, flag_reason)."""
    translator = GoogleTranslator(source=source_lang, target=target_lang)
    results = []
    for i, text in enumerate(texts):
        clean = clean_for_translation(text)
        if not clean:
            results.append(('', None))
            continue

        try:
            translated = translator.translate(clean)
            time.sleep(0.3)
        except Exception as e:
            print(f"    ERROR [{i}]: {e}", flush=True)
            translated = ''
            results.append(('', f"translation error: {e}"))
            continue

        flag = should_flag(clean, translated, source_lang, target_lang)
        results.append((translated or '', flag))

        if (i + 1) % 50 == 0:
            print(f"    [{i+1}/{len(texts)}] translated...", flush=True)

    return results


def manual_review(queue, target_col):
    """Interactive review of flagged translations."""
    if not queue:
        return

    print(f"\n{'='*60}")
    print(f"  MANUAL REVIEW: {len(queue)} flagged translations")
    print(f"  For each, type replacement or press Enter to keep.")
    print(f"  Type 's' to skip (leave empty).")
    print(f"{'='*60}\n")

    for item in queue:
        row_idx, source, auto_translated, flag_reason, col = item
        print(f"  [{col}] Source:     {source[:80]}")
        print(f"         Auto:       {auto_translated[:80]}")
        print(f"         Flag:       {flag_reason}")
        choice = input(f"         Override:   ").strip()
        if choice == 's':
            item.append('')  # skip = empty
        elif choice:
            item.append(choice)
        else:
            item.append(auto_translated)  # keep auto
        print()


def main():
    parser = argparse.ArgumentParser(description="Translate deck columns")
    parser.add_argument("--config", required=True, help="Path to deck.json")
    parser.add_argument("--source-lang", required=True, help="Source language code (e.g. de)")
    parser.add_argument("--target-lang", required=True, help="Target language code (e.g. ro)")
    parser.add_argument("--columns", nargs='+', required=True,
                        help="Column mappings as source:target (e.g. wort_de:wort_ro)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--write-csv", action="store_true")
    args = parser.parse_args()

    config_path = os.path.abspath(args.config)
    root = os.path.dirname(os.path.dirname(config_path))
    notes_csv = os.path.join(root, "data", "notes.csv")

    # Parse column mappings
    col_maps = []
    for c in args.columns:
        parts = c.split(':')
        if len(parts) != 2:
            print(f"ERROR: Invalid column mapping '{c}'. Use source:target format.")
            sys.exit(1)
        col_maps.append((parts[0], parts[1]))

    with open(notes_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)

    # Add target columns if they don't exist
    for _, target in col_maps:
        if target not in fields:
            fields.append(target)
            for row in rows:
                row[target] = ''

    print(f"\n=== Translate Deck ===\n")
    print(f"  Notes:       {len(rows)}")
    print(f"  Direction:   {args.source_lang} -> {args.target_lang}")
    print(f"  Columns:     {', '.join(f'{s}->{t}' for s, t in col_maps)}")
    if args.dry_run:
        print(f"  Mode:        DRY RUN")
    print()

    review_queue = []

    for source_col, target_col in col_maps:
        print(f"--- Translating: {source_col} -> {target_col}")

        texts = [row.get(source_col, '') for row in rows]
        results = translate_batch(texts, args.source_lang, args.target_lang)

        flagged = 0
        translated = 0
        empty = 0
        for i, (trans, flag) in enumerate(results):
            source_text = clean_for_translation(texts[i])
            if not source_text:
                empty += 1
                continue

            if not args.dry_run:
                rows[i][target_col] = trans

            if flag:
                review_queue.append([i, source_text, trans, flag, target_col])
                flagged += 1
            else:
                translated += 1

        print(f"\n  Translated: {translated}  Flagged: {flagged}  Empty: {empty}\n")

    # Manual review phase
    if review_queue and not args.dry_run:
        manual_review(review_queue, target_col)

        # Apply review decisions
        for item in review_queue:
            row_idx, source, auto, flag, col = item[:5]
            final = item[5] if len(item) > 5 else auto
            rows[row_idx][col] = final

    # Write
    if args.write_csv and not args.dry_run:
        with open(notes_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n  OK: Updated {notes_csv}")


if __name__ == "__main__":
    main()
