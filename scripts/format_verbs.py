#!/usr/bin/env python3
"""
Fetch Präteritum forms for German verbs and format wort_de to match DAF1 style.

Reads verbs from notes.csv (identified by non-empty 'verbformen' column),
queries the german-verbs-api for Präteritum 3rd person singular,
and formats wort_de as: infinitiv, <b>Präteritum</b>, hat/ist <b>Partizip</b>

For regular (weak) verbs, no bolding is applied.

Usage:
  python3 format_verbs.py --config data/deck.json [--dry-run] [--write-csv]
"""

import argparse, csv, json, os, re, ssl, sys, time, urllib.request, urllib.error

API_BASE = "https://german-verbs-api.onrender.com/german-verbs-api"
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def extract_infinitive(wort_de):
    """Extract the base infinitive from wort_de, stripping HTML, reflexive, etc."""
    clean = re.sub(r'<[^>]+>', '', wort_de).strip()
    # Remove reflexive prefix
    clean = re.sub(r'^sich\s+', '', clean)
    clean = re.sub(r'^\(sich\)\s*', '', clean)
    # Take first word/phrase before comma
    clean = clean.split(',')[0].strip()
    return clean


def fetch_prateritum(verb, retries=3):
    """Fetch Präteritum S3 from the API. Returns the form or None."""
    encoded = urllib.request.quote(verb)
    url = f"{API_BASE}?verb={encoded}&tense=PRATERITUM"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15, context=SSL_CTX) as resp:
                data = json.loads(resp.read())
                if data.get("success") and "data" in data:
                    s3 = data["data"].get("S3", [])
                    return " ".join(s3) if s3 else None
        except (urllib.error.HTTPError, urllib.error.URLError, Exception) as e:
            if attempt < retries - 1:
                wait = 3 * (attempt + 1)
                print(f"    RETRY {verb} in {wait}s ({e})", flush=True)
                time.sleep(wait)
            else:
                print(f"    FAILED {verb}: {e}", flush=True)
                return None
        time.sleep(0.5)  # rate limit
    return None


def fix_separable(prateritum, infinitive, verbformen):
    """Fix separable verb forms: 'anbot' -> 'bot an' for 'anbieten'.
    Uses verbformen to detect if verb is actually separable."""
    # Check if verbformen shows separated form (e.g. "bietet an, hat angeboten")
    first_part = verbformen.split(',')[0].strip()
    words = first_part.split()
    if len(words) < 2:
        return prateritum  # not separable

    # The last word in the first part is the separated prefix
    separated_prefix = words[-1]

    # Common separable prefixes
    prefixes = ['ab', 'an', 'auf', 'aus', 'bei', 'ein', 'fest', 'her', 'hin',
                'los', 'mit', 'nach', 'statt', 'um', 'vor', 'weg', 'weiter',
                'zu', 'zurück', 'zusammen', 'vorbei', 'teil', 'fern',
                'spazieren', 'kennen']

    if separated_prefix not in prefixes:
        return prateritum

    # Verify the infinitive starts with this prefix
    if not infinitive.startswith(separated_prefix):
        return prateritum

    # Strip prefix from prateritum
    if prateritum.startswith(separated_prefix):
        stem = prateritum[len(separated_prefix):]
        if stem:
            return f"{stem} {separated_prefix}"

    return prateritum


def is_regular(infinitive, prateritum):
    """Heuristic: regular verbs have Präteritum ending in -te(st/n/t)."""
    clean = prateritum.split()[-1] if ' ' in prateritum else prateritum
    return bool(re.search(r'te$', clean))


def format_verb(wort_de, prateritum, verbformen, infinitive):
    """Format wort_de in DAF1 style: infinitiv, Präteritum, hat/ist Partizip."""
    # Extract hat/ist + Partizip from verbformen
    # verbformen looks like: "bietet an, hat angeboten" or "kommt an, ist angekommen"
    parts = verbformen.split(',')
    if len(parts) >= 2:
        aux_partizip = parts[-1].strip()  # "hat angeboten" or "ist angekommen"
    else:
        aux_partizip = verbformen.strip()

    # Extract just the Partizip (last word)
    aux_parts = aux_partizip.split()
    if len(aux_parts) >= 2:
        aux = aux_parts[0]  # hat/ist
        partizip = ' '.join(aux_parts[1:])
    else:
        return wort_de  # can't parse, leave as-is

    # Determine reflexive prefix
    clean_wort = re.sub(r'<[^>]+>', '', wort_de).strip()
    reflexive = ""
    if clean_wort.startswith("sich "):
        reflexive = "sich "
    elif clean_wort.startswith("(sich) "):
        reflexive = "(sich) "

    # Bold irregular forms
    regular = is_regular(infinitive, prateritum)
    if regular:
        result = f"{reflexive}{infinitive}, {prateritum}, {aux} {partizip}"
    else:
        result = f"{reflexive}{infinitive}, <b>{prateritum}</b>, {aux} <b>{partizip}</b>"

    return result


def main():
    parser = argparse.ArgumentParser(description="Fetch Präteritum and format verbs")
    parser.add_argument("--config", required=True, help="Path to deck.json")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--write-csv", action="store_true", help="Write changes to CSV")
    args = parser.parse_args()

    config_path = os.path.abspath(args.config)
    root = os.path.dirname(os.path.dirname(config_path))
    notes_csv = os.path.join(root, "data", "notes.csv")

    with open(notes_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)

    verbs = [(i, r) for i, r in enumerate(rows) if r.get('verbformen', '').strip()]
    print(f"\n=== Format Verbs ===\n")
    print(f"  Notes:  {len(rows)}")
    print(f"  Verbs:  {len(verbs)}")
    if args.dry_run:
        print(f"  Mode:   DRY RUN")
    print()

    fetched = skipped = failed = 0
    for idx, (i, row) in enumerate(verbs):
        infinitive = extract_infinitive(row['wort_de'])
        verbformen = row['verbformen'].strip()

        # Skip if already formatted (has <b> tags)
        if '<b>' in row['wort_de']:
            skipped += 1
            continue

        prat = fetch_prateritum(infinitive)
        if prat is None:
            failed += 1
            print(f"  [{idx+1}/{len(verbs)}] MISS: {infinitive}", flush=True)
            continue

        prat = fix_separable(prat, infinitive, verbformen)
        formatted = format_verb(row['wort_de'], prat, verbformen, infinitive)

        print(f"  [{idx+1}/{len(verbs)}] {infinitive}: {re.sub(r'<[^>]+>', '', formatted)}", flush=True)

        if not args.dry_run:
            rows[i]['wort_de'] = formatted
        fetched += 1

    print(f"\n  Fetched: {fetched}  Skipped: {skipped}  Failed: {failed}\n")

    if args.write_csv and not args.dry_run:
        with open(notes_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
        print(f"  OK: Updated {notes_csv}")


if __name__ == "__main__":
    main()
