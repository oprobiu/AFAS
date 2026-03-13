# Pushing to GitHub

To add GitHub Actions (automated build + release on tag push), Makefile, and bootstrap.sh:

```bash
python3 scripts/init_repo.py ~/MyDeck
```

Then push and tag:
```bash
cd ~/MyDeck
git init && git add -A && git commit -m "initial"
git remote add origin https://github.com/you/your-dataset.git
git push -u origin main
git tag v1.0.0 && git push origin v1.0.0
```

The tag triggers the GitHub Action which builds the .apkg and attaches it to a Release.
