"""Integration test: combine a set of macro files through the CLI (``cli.main``).

This drives the tool exclusively through its public entry point instead of
calling ``fold`` directly, using the real, multi-block fixture files.
"""

from pathlib import Path

import pytest

from opengate_gate_macro_fold import cli

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.mark.parametrize("fixture_group", ["full-stack", "partial-stack"])
def test_main_fold_reproduces_fixture_mono_file(fixture_group: str, tmp_path: Path) -> None:
    """--fold on a fixture set/ directory should reproduce its mono/macro.mac exactly."""
    # Arrange
    macros_dir = FIXTURES_DIR / fixture_group / "set"
    expected_mono = FIXTURES_DIR / fixture_group / "mono" / "macro.mac"
    output_dir = tmp_path / "mono"

    # Act
    exit_code = cli.main(
        [
            "--fold",
            "--input-macros-dir",
            str(macros_dir),
            "--output-dir",
            str(output_dir),
            "--title",
            "macro",
        ]
    )

    # Assert
    assert exit_code == 0
    assert (output_dir / "macro.mac").read_bytes() == expected_mono.read_bytes()
