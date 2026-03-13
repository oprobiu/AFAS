#!/usr/bin/env python3
"""
Add GitHub Actions workflow and repo files to an existing dataset directory.

Run this after init_dataset.py (or unpack_apkg.py) to make the dataset
ready to push to GitHub with automated builds and releases.

Usage:
  python3 init_repo.py ~/MyDeck
"""

import argparse, json, os, sys


RELEASE_YML = """name: Release
on:
  push:
    tags: ['v*']
jobs:
  build:
    uses: {tools_repo}/.github/workflows/build-release.yml@{tools_version}
    permissions:
      contents: write
"""

BOOTSTRAP_SH = """#!/usr/bin/env bash
set -e
CONFIG="data/deck.json"
REPO=$(python3 -c "import json; print(json.load(open('$CONFIG'))['tools_repo'])")
VERSION=$(python3 -c "import json; print(json.load(open('$CONFIG'))['tools_version'])")
DEST=".tools/AFAS"

if [ -d "$DEST" ] && [ -f "$DEST/.version" ] && [ "$(cat $DEST/.version)" = "$VERSION" ]; then
    echo "Tools $VERSION already present."
    exit 0
fi

echo "Downloading AFAS $VERSION..."
rm -rf "$DEST"
mkdir -p .tools
git clone --depth 1 --branch "$VERSION" "https://github.com/$REPO.git" "$DEST"
echo "$VERSION" > "$DEST/.version"
echo "Done."
"""

MAKEFILE = """bootstrap:
\tbash bootstrap.sh

build: bootstrap
\tpython3 .tools/AFAS/scripts/build_apkg.py --config data/deck.json --tools-dir .tools/AFAS

tts: bootstrap
\tpython3 .tools/AFAS/scripts/regenerate_tts.py --config data/deck.json --write-csv

validate: bootstrap
\tpython3 .tools/AFAS/scripts/validate.py --config data/deck.json --tools-dir .tools/AFAS

clean:
\trm -rf build/ .tools/
"""


def init_repo(dataset_dir):
    dataset_dir = os.path.abspath(dataset_dir)
    config_path = os.path.join(dataset_dir, "data", "deck.json")

    if not os.path.exists(config_path):
        print(f"ERROR: {config_path} not found. Run init_dataset.py or unpack_apkg.py first.")
        return 1

    with open(config_path) as f:
        config = json.load(f)

    tools_repo = config.get("tools_repo", "oprobiu/AFAS")
    tools_version = config.get("tools_version", "v1.0.0")

    # GitHub Actions workflow
    wf_dir = os.path.join(dataset_dir, ".github", "workflows")
    wf_path = os.path.join(wf_dir, "release.yml")
    os.makedirs(wf_dir, exist_ok=True)
    with open(wf_path, "w") as f:
        f.write(RELEASE_YML.format(tools_repo=tools_repo, tools_version=tools_version).lstrip())

    # bootstrap.sh
    bs_path = os.path.join(dataset_dir, "bootstrap.sh")
    with open(bs_path, "w") as f:
        f.write(BOOTSTRAP_SH.lstrip())
    os.chmod(bs_path, 0o755)

    # Makefile
    mk_path = os.path.join(dataset_dir, "Makefile")
    with open(mk_path, "w") as f:
        f.write(MAKEFILE.lstrip())

    # Update .gitignore if it exists
    gi_path = os.path.join(dataset_dir, ".gitignore")
    if os.path.exists(gi_path):
        with open(gi_path) as f:
            existing = f.read()
        additions = []
        for entry in ["build/", ".tools/"]:
            if entry not in existing:
                additions.append(entry)
        if additions:
            with open(gi_path, "a") as f:
                for a in additions:
                    f.write(a + "\n")

    print(f"")
    print(f"=== Repo files added ===")
    print(f"")
    print(f"  {wf_path}")
    print(f"  {bs_path}")
    print(f"  {mk_path}")
    print(f"")
    print(f"  tools_repo:    {tools_repo}")
    print(f"  tools_version: {tools_version}")
    print(f"")
    print(f"GitHub Actions: push a tag like v1.0.0 to trigger a build and release.")
    print(f"Local dev: run 'make build', 'make tts', 'make validate'.")
    print(f"")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Add GitHub Actions and repo files to a dataset")
    parser.add_argument("dataset_dir", help="Path to the dataset directory")
    args = parser.parse_args()
    sys.exit(init_repo(args.dataset_dir))


if __name__ == "__main__":
    main()
