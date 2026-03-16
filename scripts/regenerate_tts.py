#!/usr/bin/env python3
"""
Regenerate TTS audio. Fully config-driven.

Reads tts config from deck.json:
  - tts.engine: "edge-tts" or "gtts"
  - tts.voices: list of voice names (edge-tts) or ignored (gtts)
  - tts.language: language code (used by gtts, e.g. "de")
  - tts.targets: list of {field, source, prefix, strip_html, dialogue}

If no "tts" key in config, exits cleanly (deck has no audio).

Usage:
  python3 regenerate_tts.py --config data/deck.json [--dry-run] [--limit N] [--write-csv]
"""

import asyncio, argparse, csv, hashlib, json, os, re, sys, time

edge_tts = None
gtts_mod = None

def _load_engine(engine):
    global edge_tts, gtts_mod
    if engine == "edge-tts":
        try:
            import edge_tts as _et
            edge_tts = _et
        except ImportError:
            print("ERROR: 'edge-tts' not installed. Run: pip install edge-tts")
            sys.exit(1)
    elif engine == "gtts":
        try:
            from gtts import gTTS as _gt
            gtts_mod = _gt
        except ImportError:
            print("ERROR: 'gTTS' not installed. Run: pip install gTTS")
            sys.exit(1)
    else:
        print(f"ERROR: Unknown engine '{engine}'. Supported: edge-tts, gtts")
        sys.exit(1)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_loader import load_config

SILENCE_MP3 = bytes.fromhex(("fff3e4c4" + "00" * 104) * 6)


def strip_sound_refs(text):
    return re.sub(r"\[sound:[^\]]+\]", "", text)


def strip_html(text):
    return re.sub(r"<[^>]+>", "", text)


def extract_speakable(text, do_strip_html=True):
    if do_strip_html:
        text = strip_html(text)
    raw = text.split("/")[0].strip()
    raw = raw.split(",")[0].strip()
    raw = re.sub(r"\(.*?\)-?", "", raw).strip()
    return raw.rstrip("- ")


def make_filename(prefix, text, voice, engine="edge-tts"):
    tag = "edgetts" if engine == "edge-tts" else "gtts"
    h = hashlib.sha1(f"{prefix}:{voice}:{text}".encode("utf-8")).hexdigest()
    return f"{tag}-{prefix}-{h[:8]}-{h[8:16]}-{h[16:24]}-{h[24:32]}-{h[32:40]}.mp3"


def make_dialogue_filename(prefix, text, engine="edge-tts"):
    tag = "edgetts" if engine == "edge-tts" else "gtts"
    h = hashlib.sha1(f"dialogue:{prefix}:{text}".encode("utf-8")).hexdigest()
    return f"{tag}-{prefix}-{h[:8]}-{h[8:16]}-{h[16:24]}-{h[24:32]}-{h[32:40]}.mp3"


async def generate_audio(text, voice, path, engine="edge-tts", language="de", retries=3):
    for attempt in range(retries):
        try:
            if engine == "gtts":
                tts = gtts_mod(text=text, lang=language, slow=False)
                tts.save(path)
                await asyncio.sleep(0.5)
            else:
                await edge_tts.Communicate(text, voice).save(path)
                await asyncio.sleep(0.3)
            return
        except Exception as e:
            if attempt < retries - 1:
                wait = 5 * (attempt + 1)
                print(f"       RETRY in {wait}s ({e})", flush=True)
                await asyncio.sleep(wait)
            else:
                raise


async def generate_dialogue(text, dialogue_cfg, voices, path, engine="edge-tts", language="de"):
    female_marker = dialogue_cfg.get("female_marker", "\u25cf")
    male_marker = dialogue_cfg.get("male_marker", "\u25a0")
    parts = text.split(male_marker)
    part_a = parts[0].replace(female_marker, "").strip()
    part_b = parts[1].strip() if len(parts) > 1 else ""
    female_voice = voices[0] if voices else "default"
    male_voice = voices[1] if len(voices) > 1 else female_voice
    tmp_a, tmp_b = path + ".a.mp3", path + ".b.mp3"
    try:
        await generate_audio(part_a, female_voice, tmp_a, engine, language)
        await generate_audio(part_b, male_voice, tmp_b, engine, language)
        with open(path, "wb") as out:
            with open(tmp_a, "rb") as fa:
                out.write(fa.read())
            out.write(SILENCE_MP3)
            with open(tmp_b, "rb") as fb:
                out.write(fb.read())
    finally:
        for t in (tmp_a, tmp_b):
            if os.path.exists(t):
                os.remove(t)


async def process_target(target, notes, voices, media_dir, args, engine="edge-tts", language="de"):
    """Process one TTS target (e.g. sentence audio or word audio)."""
    field = target["field"]
    source = target["source"]
    prefix = target["prefix"]
    do_strip = target.get("strip_html", False)
    dialogue_cfg = target.get("dialogue")

    print(f"--- Target: {field} (source: {source}, prefix: {prefix})")
    gen = skip = empty = clear = 0
    total = len(notes)

    for i, row in enumerate(notes):
        raw_text = row.get(source, "")
        raw_text = strip_sound_refs(raw_text)
        text = extract_speakable(raw_text, do_strip) if do_strip else strip_html(raw_text).strip()

        if not text:
            if row.get(field, "").strip():
                if not args.dry_run:
                    row[field] = ""
                clear += 1
            empty += 1
            continue

        voice = voices[i % len(voices)] if voices else "default"
        is_dlg = dialogue_cfg and dialogue_cfg.get("enabled") and dialogue_cfg["female_marker"] in text and dialogue_cfg["male_marker"] in text

        if is_dlg:
            filename = make_dialogue_filename(prefix, text, engine)
        else:
            filename = make_filename(prefix, text, voice, engine)

        path = os.path.join(media_dir, filename)

        if not args.dry_run:
            row[field] = f"[sound:{filename}]"

        if os.path.exists(path):
            skip += 1
        else:
            label = "DIALOGUE" if is_dlg else (voice.split("-")[-1] if engine == "edge-tts" else "gTTS")
            display = text[:55] + ("..." if len(text) > 55 else "")
            print(f"  [{i+1}/{total}] {label}: {display}", flush=True)
            if not args.dry_run:
                if is_dlg:
                    await generate_dialogue(text, dialogue_cfg, voices, path, engine, language)
                else:
                    await generate_audio(text, voice, path, engine, language)
            gen += 1

    print(f"\n\n  Generated: {gen}  Skipped: {skip}  Empty: {empty}  Cleared: {clear}\n")
    return gen


async def run(args):
    start = time.time()
    config = load_config(args.config, getattr(args, 'tools_dir', None))
    root = config["_root"]

    tts_cfg = config.get("tts")
    if not tts_cfg:
        print("No 'tts' config in deck.json. Nothing to generate.")
        return

    notes_csv = os.path.join(root, "data", "notes.csv")
    media_dir = os.path.join(root, "media_files")
    os.makedirs(media_dir, exist_ok=True)

    voices = tts_cfg.get("voices", [])
    targets = tts_cfg.get("targets", [])
    engine = tts_cfg.get("engine", "edge-tts")
    language = tts_cfg.get("language", "de").split("-")[0]  # "de-DE" -> "de"

    _load_engine(engine)

    with open(notes_csv, encoding="utf-8") as f:
        notes = list(csv.DictReader(f))

    print(f"")
    print(f"=== TTS Audio Regeneration ===")
    print(f"")
    print(f"  Engine:  {engine}")
    print(f"  Lang:    {tts_cfg.get('language', 'N/A')}")
    print(f"  Notes:   {len(notes)}")
    print(f"  Voices:  {len(voices)}")
    for i, v in enumerate(voices):
        print(f"    [{i}] {v}")
    print(f"  Targets: {len(targets)}")
    for t in targets:
        print(f"    {t['field']} <- {t['source']} (prefix: {t['prefix']})")
    if args.dry_run:
        print(f"  Mode:    DRY RUN")
    if args.limit:
        print(f"  Limit:   {args.limit} notes")
    print(f"")

    # Apply limit at note level (all targets process the same notes)
    process_notes = notes[:args.limit] if args.limit else notes

    # Process each target
    total_gen = 0
    for target in targets:
        total_gen += await process_target(target, process_notes, voices, media_dir, args, engine, language)

    # Write CSV
    if args.write_csv and not args.dry_run:
        fieldnames = list(notes[0].keys()) if notes else config["csv_columns"]
        with open(notes_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator='\n')
            writer.writeheader()
            writer.writerows(notes)
        print(f"  OK: Updated {notes_csv}")

    # Verify
    if not args.dry_run:
        print(f"\n--- Verification")
        missing = 0
        audio_fields = [t["field"] for t in targets]
        for row in notes:
            for field in audio_fields:
                ref = row.get(field, "").strip()
                if ref:
                    fname = ref.replace("[sound:", "").replace("]", "")
                    if not os.path.exists(os.path.join(media_dir, fname)):
                        missing += 1
        if missing:
            print(f"  ERROR: {missing} files missing!")
        else:
            print(f"  OK: All files present.")

    print(f"\n  Generated {total_gen} files in {time.time() - start:.1f}s")


def main():
    parser = argparse.ArgumentParser(description="Regenerate TTS audio")
    parser.add_argument("--config", required=True, help="Path to deck.json")
    parser.add_argument("--tools-dir", default=None, help="Path to AFAS tools directory")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--write-csv", action="store_true")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
