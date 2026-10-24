"""Assemble the frozen validation kits, test them in a clean environment, and zip them.

Run from the repo root:
    python3 tools/library/build_kits.py            # assemble, test, zip every kit
    python3 tools/library/build_kits.py --no-test  # assemble and zip only

A kit's own files live in library_src/kits/<id>/. The build adds the shared
parts: the conventions module and its tests, and the model's QuantLib
reference values. Output: public/library/kits/<id>_validation_kit.zip.
Tests run in a fresh virtual environment WITHOUT QuantLib, as a user would.
Documentation is written once in Markdown (docs/*.md, with LaTeX math) and
shipped as Word (.docx, native equations) and LaTeX (docs/latex/*.tex); the
LaTeX is compiled once at build time to make sure it builds.
"""
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "library_src" / "kits"
CONV = ROOT / "public" / "library" / "conventions"
MODELS = ROOT / "public" / "library" / "models"
OUT = ROOT / "public" / "library" / "kits"
SKIP = {"__pycache__", ".pytest_cache", ".venv"}


def assemble(kit_id: str, dest: Path) -> Path:
    kit = dest / f"{kit_id}_validation_kit"
    shutil.copytree(SRC / kit_id, kit, ignore=shutil.ignore_patterns(*SKIP, "*.pyc"))
    shutil.copytree(CONV / "pl4nck_conventions", kit / "src" / "pl4nck_conventions", ignore=shutil.ignore_patterns(*SKIP, "*.pyc"))
    (kit / "tests" / "conventions" / "reference").mkdir(parents=True, exist_ok=True)
    shutil.copy(CONV / "tests" / "test_conventions.py", kit / "tests" / "conventions" / "test_conventions.py")
    shutil.copy(CONV / "tests" / "reference" / "conventions_quantlib.json", kit / "tests" / "conventions" / "reference")
    (kit / "tests" / "reference").mkdir(parents=True, exist_ok=True)
    shutil.copy(MODELS / kit_id / "reference_quantlib.json", kit / "tests" / "reference" / f"{kit_id}_quantlib.json")
    return kit


DOCS = Path(__file__).parent / "docs"


def build_docs(kit: Path) -> None:
    """docs/*.md -> docs/*.docx and docs/latex/*.tex; the Markdown sources are not shipped."""
    latex_dir = kit / "docs" / "latex"
    latex_dir.mkdir(parents=True, exist_ok=True)
    for md in sorted((kit / "docs").glob("*.md")):
        common = ["pandoc", str(md), "--from", "markdown", "--lua-filter", str(DOCS / "kitdocs.lua")]
        subprocess.run(common + ["--reference-doc", str(DOCS / "reference.docx"), "-o", str(md.with_suffix(".docx"))], check=True)
        tex = latex_dir / md.with_suffix(".tex").name
        subprocess.run(common + ["--standalone", "-H", str(DOCS / "latex-header.tex"), "-V", "geometry:margin=2.2cm",
                                 "-V", "fontsize=10pt", "-V", "colorlinks=true", "-V", "fontfamily=helvet", "-V", "fontfamilyoptions=scaled=0.92", "-o", str(tex)], check=True)
        if shutil.which("pdflatex"):
            with tempfile.TemporaryDirectory() as tmp:
                r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory", tmp, str(tex)],
                                   capture_output=True, text=True)
                if r.returncode != 0:
                    raise RuntimeError(f"LaTeX build failed for {tex.name}:\n{r.stdout[-2000:]}")
        md.unlink()


def test(kit: Path) -> None:
    venv = kit.parent / ".venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    py = venv / ("Scripts" if sys.platform == "win32" else "bin") / "python"
    subprocess.run([str(py), "-m", "pip", "install", "-q", "-e", f"{kit}[test]"], check=True)
    ql = subprocess.run([str(py), "-c", "import QuantLib"], capture_output=True)
    assert ql.returncode != 0, "QuantLib must not be installed in the test environment"
    subprocess.run([str(py), "-m", "pytest", "-q", "-p", "no:cacheprovider", str(kit / "tests")], check=True, cwd=kit)
    subprocess.run([str(py), str(kit / "examples" / "run_example.py")], check=True, cwd=kit, stdout=subprocess.DEVNULL)


def zip_kit(kit: Path) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / f"{kit.name}.zip"
    files = sorted(p for p in kit.rglob("*") if p.is_file() and not SKIP & set(p.parts) and p.suffix != ".pyc"
                   and ".egg-info" not in str(p))
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, f"{kit.name}/{p.relative_to(kit)}")
    return target


if __name__ == "__main__":
    run_tests = "--no-test" not in sys.argv
    kits = sorted(p.name for p in SRC.iterdir() if p.is_dir())
    for kit_id in kits:
        with tempfile.TemporaryDirectory() as tmp:
            kit = assemble(kit_id, Path(tmp))
            build_docs(kit)
            if run_tests:
                test(kit)
            target = zip_kit(kit)
            print(f"{kit_id}: {target.relative_to(ROOT)} ({target.stat().st_size // 1024} KB){' tested' if run_tests else ''}")
