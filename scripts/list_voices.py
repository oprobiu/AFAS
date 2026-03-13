#!/usr/bin/env python3
"""
List available edge-tts voices, optionally filtered by language.

Usage:
  python3 list_voices.py                  # all voices
  python3 list_voices.py --language de    # German voices
  python3 list_voices.py --language it    # Italian voices
"""

import argparse, asyncio

try:
    import edge_tts
except ImportError:
    import sys
    print("ERROR: 'edge-tts' not installed. Run: pip install -r requirements.txt")
    sys.exit(1)


async def run(lang_filter):
    voices = await edge_tts.list_voices()
    voices.sort(key=lambda v: v["ShortName"])

    if lang_filter:
        lang_filter = lang_filter.lower()
        voices = [v for v in voices if lang_filter in v["Locale"].lower()]

    if not voices:
        print(f"No voices found for '{lang_filter}'")
        return

    print(f"{'Voice':<45} {'Gender':<8} {'Locale'}")
    print(f"{'-'*45} {'-'*8} {'-'*10}")
    for v in voices:
        print(f"{v['ShortName']:<45} {v['Gender']:<8} {v['Locale']}")
    print(f"\n{len(voices)} voices found")
    print(f"Full list: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts#supported-languages")


def main():
    parser = argparse.ArgumentParser(description="List edge-tts voices")
    parser.add_argument("--language", "-l", help="Filter by language code (e.g. de, it, zh, en)")
    args = parser.parse_args()
    asyncio.run(run(args.language))


if __name__ == "__main__":
    main()
