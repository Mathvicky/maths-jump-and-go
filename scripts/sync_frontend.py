"""Publish the canonical frontend to the GitHub Pages directory."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
for name in ("index.html", "styles.css", "script.js", "config.js"):
    shutil.copyfile(root / "app" / name, root / "docs" / name)
shutil.copytree(root / "app/assets", root / "docs/assets", dirs_exist_ok=True)
print("Updated docs from app; preserved docs/CNAME.")
