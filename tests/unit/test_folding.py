"""Unit tests for combining a set of macro files into a mono macro file (``fold``)."""

from pathlib import Path

import pytest

from opengate_gate_macro_fold.io.macrofile import MacroContent
from opengate_gate_macro_fold.io.readers import read_macro_file, read_macrs_from_directory
from opengate_gate_macro_fold.macro_processing.folding import fold
from opengate_gate_macro_fold.macro_processing.unfolding import unfold

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.mark.parametrize("fixture_group", ["full-stack", "partial-stack"])
def test_fold_produces_expected_mono_content(fixture_group: str) -> None:
    """fold should reproduce the fixture's mono/macro.mac content from its set files."""
    # Arrange
    macro_files = read_macrs_from_directory(str(FIXTURES_DIR / fixture_group / "set"))
    main_file = next(macro_file for macro_file in macro_files if macro_file.name == "main.mac")
    block_files = [macro_file for macro_file in macro_files if macro_file.name != "main.mac"]
    expected_mono = read_macro_file(str(FIXTURES_DIR / fixture_group / "mono" / "macro.mac"))

    # Act
    mono_macro = fold(main_file, block_files)

    # Assert
    assert mono_macro.content == expected_mono.content
    assert mono_macro.is_mono_macro is True
    assert mono_macro.content_type == MacroContent.MONO_MACRO


def test_fold_raises_for_missing_block_file() -> None:
    """fold should raise ValueError when a referenced macro file is missing."""
    # Arrange
    main_file = read_macro_file(str(FIXTURES_DIR / "full-stack" / "set" / "main.mac"))

    # Act / Assert
    with pytest.raises(ValueError, match="Missing macro file for execute block 'detector.mac'"):
        fold(main_file, block_files=[])


@pytest.mark.parametrize("fixture_group", ["full-stack", "partial-stack"])
def test_fold_of_unfold_round_trips_mono_content(fixture_group: str) -> None:
    """fold(*unfold(mono)) should reproduce the original mono macro content."""
    # Arrange
    mono_macro = read_macro_file(str(FIXTURES_DIR / fixture_group / "mono" / "macro.mac"))

    # Act
    main_file, block_files = unfold(mono_macro)
    refolded = fold(main_file, block_files)

    # Assert
    assert refolded.content == mono_macro.content
