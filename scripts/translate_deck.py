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
    --columns fo_word:na_word fo_sentence:na_sentence \
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


ARTICLES = {'der', 'die', 'das', 'ein', 'eine'}
SG_PL_MARKERS = {'(sg.)', '(s.g.)', '(pl.)', '(sg)', '(pl)'}


def extract_base_word(text):
    """Extract the translatable base word from a grammar-annotated fo_word.

    Handles:
      Nouns:     'das Angebot, -e' -> 'Angebot'
      Nouns:     'die Bank (Geldinstitut), -en' -> 'Bank (Geldinstitut)'
      Nouns:     'das Alter, (S.g.)' -> 'Alter'
      Verbs:     'anbieten, bot an, hat angeboten' -> 'anbieten'
      Reflexive: 'sich anmelden, meldete an, hat angemeldet' -> 'sich anmelden'
      Adjective: 'gern, lieber, am liebsten' -> 'gern'
      Plain:     'anders' -> 'anders'
      Phrases:   'auf jeden Fall' -> 'auf jeden Fall'
    """
    text = strip_html(text).strip()

    # Split on comma — first part is the main word/phrase
    parts = [p.strip() for p in text.split(',')]
    main = parts[0]

    # If remaining parts are just plural suffixes, Sg/Pl markers, or verb forms — drop them
    # But keep the main part
    if len(parts) > 1:
        # Check if second part looks like a verb conjugation (contains 'hat'/'ist'/'hatte')
        rest = ', '.join(parts[1:])
        is_verb_forms = any(aux in rest.lower() for aux in ['hat ', 'ist ', 'hatte ', 'war '])
        is_plural_suffix = all(
            p.strip().startswith('-') or
            p.strip().startswith('"') or  # umlaut marker "- 
            p.strip().startswith('\u2033') or  # another umlaut marker
            p.strip().lower() in SG_PL_MARKERS or
            p.strip().startswith('(') and p.strip().endswith(')')
            for p in parts[1:]
        )
        is_comparative = any(w in rest.lower() for w in ['am besten', 'am liebsten', 'am meisten'])

        if is_verb_forms or is_plural_suffix or is_comparative:
            text = main
        else:
            text = main  # default: just take first part

    # Strip article from nouns
    words = text.split()
    if len(words) >= 2 and words[0].lower() in ARTICLES:
        text = ' '.join(words[1:])

    # Strip Sg/Pl markers at end
    for marker in SG_PL_MARKERS:
        if text.lower().endswith(marker):
            text = text[:len(text)-len(marker)].strip().rstrip(',')

    return text.strip()


def split_multi_sentence(text):
    """Split a multi-sentence field into individual sentences.

    Handles:
      'Satz1 [sound:x.mp3]<br><hr class="sent-sep"><br>Satz2 [sound:y.mp3]'
      -> ['Satz1', 'Satz2']
    """
    text = strip_sound_refs(text)
    # Split on the sentence separator pattern
    parts = re.split(r'<br>\s*<hr[^>]*>\s*<br>', text)
    result = []
    for p in parts:
        cleaned = strip_html(p).strip()
        if cleaned:
            result.append(cleaned)
    return result


def clean_for_translation(text, extract_word=False):
    """Clean text for translation, removing HTML, sound refs, etc.

    If extract_word=True, also strips grammar annotations (articles,
    plural suffixes, verb conjugations) to get just the translatable word.
    """
    text = strip_sound_refs(text)
    text = strip_html(text)
    text = text.strip()
    if extract_word and text:
        text = extract_base_word(text)
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


def translate_batch(texts, source_lang, target_lang, extract_word=False):
    """Translate a list of texts. Returns list of (translated, flag_reason)."""
    translator = GoogleTranslator(source=source_lang, target=target_lang)
    results = []
    for i, text in enumerate(texts):
        # Check if multi-sentence (contains separator)
        if '<hr' in text and not extract_word:
            sentences = split_multi_sentence(text)
            if len(sentences) > 1:
                translated_parts = []
                any_flag = None
                for s in sentences:
                    try:
                        t = translator.translate(s)
                        time.sleep(0.3)
                        translated_parts.append(t or '')
                    except Exception as e:
                        translated_parts.append('')
                        any_flag = f"translation error: {e}"
                translated = '\n'.join(translated_parts)
                if not any_flag:
                    any_flag = should_flag(sentences[0], translated_parts[0], source_lang, target_lang)
                results.append((translated, any_flag))
                status = "⚠ FLAGGED" if any_flag else "✓"
                display = sentences[0][:30] + f" (+{len(sentences)-1} more)"
                print(f"  [{i+1}/{len(texts)}] {status}: {display} → {translated_parts[0][:30]}", flush=True)
                continue

        clean = clean_for_translation(text, extract_word=extract_word)
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

        status = "⚠ FLAGGED" if flag else "✓"
        print(f"  [{i+1}/{len(texts)}] {status}: {clean[:40]} → {(translated or '???')[:40]}", flush=True)

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
                        help="Column mappings as source:target (e.g. fo_word:na_word)")
    parser.add_argument("--strip-grammar", nargs='*', default=[],
                        help="Source columns to strip grammar from before translating (articles, plurals, verb forms)")
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

    strip_grammar_cols = set(args.strip_grammar) if args.strip_grammar else set()

    print(f"\n=== Translate Deck ===\n")
    print(f"  Notes:       {len(rows)}")
    print(f"  Direction:   {args.source_lang} -> {args.target_lang}")
    print(f"  Columns:     {', '.join(f'{s}->{t}' for s, t in col_maps)}")
    if strip_grammar_cols:
        print(f"  Strip grammar: {', '.join(strip_grammar_cols)}")
    if args.dry_run:
        print(f"  Mode:        DRY RUN")
    print()

    review_queue = []

    for source_col, target_col in col_maps:
        print(f"--- Translating: {source_col} -> {target_col}")
        extract_word = source_col in strip_grammar_cols

        texts = [row.get(source_col, '') for row in rows]
        results = translate_batch(texts, args.source_lang, args.target_lang, extract_word=extract_word)

        flagged = 0
        translated = 0
        empty = 0
        for i, (trans, flag) in enumerate(results):
            source_text = clean_for_translation(texts[i], extract_word=extract_word)
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
