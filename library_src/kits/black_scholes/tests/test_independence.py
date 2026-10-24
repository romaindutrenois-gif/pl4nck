"""The prototype must be independent of the library it is checked against."""
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
IMPORT = re.compile(r"^\s*(import|from)\s+QuantLib\b", re.MULTILINE)


def test_prototype_does_not_import_quantlib():
    offenders = [str(p.relative_to(SRC)) for p in SRC.rglob("*.py") if IMPORT.search(p.read_text())]
    assert not offenders, f"these files import QuantLib: {offenders}"
