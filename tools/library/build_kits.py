"""Assemble the frozen validation kits, test them in a clean environment, and zip them.

Run from the repo root:
    python3 tools/library/build_kits.py            # assemble, test, zip every kit
    python3 tools/library/build_kits.py --no-test  # assemble and zip only

A kit's own files live in library_src/kits/<id>/. The build adds the shared
parts: the conventions module and its tests, and the model's QuantLib
reference values. Output: public/library/kits/<id>_validation_kit.zip.
Tests run in a fresh virtual environment WITHOUT QuantLib, as a user would.
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
            if run_tests:
                test(kit)
            target = zip_kit(kit)
            print(f"{kit_id}: {target.relative_to(ROOT)} ({target.stat().st_size // 1024} KB){' tested' if run_tests else ''}")
