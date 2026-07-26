"""Unit tests for splitting a mono macro file into a set of macro files (``unfold``)."""

from pathlib import Path

import pytest

from opengate_gate_macro_fold.io.macrofile import MacroContent
from opengate_gate_macro_fold.io.readers import read_macro_file, read_macrs_from_directory
from opengate_gate_macro_fold.macro_processing.unfolding import unfold

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.mark.parametrize("fixture_group", ["full-stack", "partial-stack"])
def test_unfold_produces_expected_main_file(fixture_group: str) -> None:
    """unfold should produce a main file matching the fixture's set/main.mac content."""
    # Arrange
    mono_macro = read_macro_file(str(FIXTURES_DIR / fixture_group / "mono" / "macro.mac"))
    expected_main = read_macro_file(str(FIXTURES_DIR / fixture_group / "set" / "main.mac"))

    # Act
    main_file, _block_files = unfold(mono_macro)

    # Assert
    assert main_file.name == "main.mac"
    assert main_file.content == expected_main.content
    assert main_file.content_type == MacroContent.MAIN


@pytest.mark.parametrize("fixture_group", ["full-stack", "partial-stack"])
def test_unfold_produces_expected_block_files(fixture_group: str) -> None:
    """unfold should produce block files matching every fixture set/*.mac file."""
    # Arrange
    mono_macro = read_macro_file(str(FIXTURES_DIR / fixture_group / "mono" / "macro.mac"))
    expected_files = {
        macro_file.name: macro_file.content
        for macro_file in read_macrs_from_directory(str(FIXTURES_DIR / fixture_group / "set"))
        if macro_file.name != "main.mac"
    }

    # Act
    _main_file, block_files = unfold(mono_macro)

    # Assert
    assert {block_file.name: block_file.content for block_file in block_files} == expected_files
