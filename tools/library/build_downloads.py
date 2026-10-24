"""Package library folders as zips and list their files for the kit generator.

Run from the repo root after editing anything under public/library/:
    python3 tools/library/build_downloads.py
"""
import json
import zipfile
from pathlib import Path

LIB = Path(__file__).resolve().parents[2] / "public" / "library"
SKIP = {"__pycache__", ".pytest_cache"}

for folder, zipname in [("conventions", "pl4nck_conventions.zip")]:
    src = LIB / folder
    files = sorted(p for p in src.rglob("*") if p.is_file() and not SKIP & set(p.parts) and p.suffix != ".pyc" and p.name != "manifest.json")
    with zipfile.ZipFile(LIB / zipname, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, f"pl4nck_conventions/{p.relative_to(src)}")
    manifest = [str(p.relative_to(src)) for p in files]
    (src / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(zipname, len(files), "files", (LIB / zipname).stat().st_size // 1024, "KB")
