import importlib.util
from pathlib import Path


def test_frozen_parser_fixture_set_is_complete() -> None:
    path = Path(__file__).resolve().parents[1] / "experiments/parser-fixtures-001/runner.py"
    spec = importlib.util.spec_from_file_location("parser_fixture_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = module.run()
    assert len(rows) == 15
    assert {row["format"] for row in rows} == {"txt", "md", "pdf"}
    assert all(row["extraction_complete"] and row["location_accurate"] for row in rows)
