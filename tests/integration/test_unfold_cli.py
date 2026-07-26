"""Integration test: split a mono macro file through the CLI (``cli.main``).

This drives the tool exclusively through its public entry point instead of
calling ``unfold`` directly, using the real, multi-block fixture files.
"""

from pathlib import Path

import pytest

from opengate_gate_macro_fold import cli

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.mark.parametrize("fixture_group", ["full-stack", "partial-stack"])
def test_main_unfold_reproduces_fixture_set_directory(fixture_group: str, tmp_path: Path) -> None:
    """--unfold on a fixture mono file should reproduce its set/ directory exactly."""
    # Arrange
    mono_path = FIXTURES_DIR / fixture_group / "mono" / "macro.mac"
    expected_dir = FIXTURES_DIR / fixture_group / "set"
    output_dir = tmp_path / "set"

    # Act
    exit_code = cli.main(
        [
            "--unfold",
            "--input-mono-macro-file",
            str(mono_path),
            "--output-dir",
            str(output_dir),
        ]
    )

    # Assert
    assert exit_code == 0
    expected_files = {path.name: path.read_bytes() for path in expected_dir.iterdir()}
    actual_files = {path.name: path.read_bytes() for path in output_dir.iterdir()}
    assert actual_files == expected_files
