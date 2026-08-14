from __future__ import annotations

from pathlib import Path


def test_import_package() -> None:
    import praxicraft

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    expected = next(
        line.split("=", 1)[1].strip().strip('"')
        for line in pyproject.read_text().splitlines()
        if line.startswith("version = ")
    )
    assert praxicraft.__version__ == expected
    assert hasattr(praxicraft, "Client")
