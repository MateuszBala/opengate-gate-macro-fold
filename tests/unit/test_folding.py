"""Unit tests for combining a set of macro files into a mono macro file (``fold``)."""

from pathlib import Path

import pytest

from opengate_gate_macro_fold.io.macrofile import MacroContent, MacroFile
from opengate_gate_macro_fold.io.readers import read_macro_file, read_macrs_from_directory
from opengate_gate_macro_fold.macro_processing.folding import fold
from opengate_gate_macro_fold.macro_processing.unfolding import unfold

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

ALL_GROUPS = [
    "full-stack",
    "partial-stack",
    "full-statc-without-text",
    "partial-stack-actor-example",
]


def _read_set(fixture_group: str) -> tuple[MacroFile, list[MacroFile]]:
    """Read a fixture set directory, split into the main file and block files."""
    macro_files = read_macrs_from_directory(str(FIXTURES_DIR / fixture_group / "set"))
    main_file = next(macro_file for macro_file in macro_files if macro_file.name == "main.mac")
    block_files = [macro_file for macro_file in macro_files if macro_file.name != "main.mac"]
    return main_file, block_files


@pytest.mark.parametrize("fixture_group", ALL_GROUPS)
def test_fold_produces_expected_mono_content(fixture_group: str) -> None:
    """fold should reproduce the fixture's mono/macro.mac content from its set files."""
    # Arrange
    main_file, block_files = _read_set(fixture_group)
    expected_mono = read_macro_file(str(FIXTURES_DIR / fixture_group / "mono" / "macro.mac"))

    # Act
    mono_macro = fold(main_file, block_files)

    # Assert
    assert mono_macro.content == expected_mono.content
    assert mono_macro.is_mono_macro is True
    assert mono_macro.content_type == MacroContent.MONO_MACRO


def test_fold_resolves_references_case_insensitively() -> None:
    """fold should match /control/execute references to file names ignoring case."""
    # Arrange
    main_file = MacroFile(content=["/control/execute Geometry.mac\n"])
    block_files = [
        MacroFile(content=["/gate/world/geometry/setXLength 300. cm\n"], name="geometry.mac")
    ]

    # Act
    mono_macro = fold(main_file, block_files)

    # Assert
    assert mono_macro.content == ["/gate/world/geometry/setXLength 300. cm\n"]


def test_fold_keeps_unresolved_references_verbatim() -> None:
    """A /control/execute call without a matching provided file must stay unchanged."""
    # Arrange
    main_file = MacroFile(content=["/control/execute external.mac\n"])

    # Act
    mono_macro = fold(main_file, block_files=[])

    # Assert
    assert mono_macro.content == ["/control/execute external.mac\n"]


def test_fold_strips_outer_blank_lines_of_block_files() -> None:
    """Outer blank lines of a block file must not leak into the mono macro."""
    # Arrange
    main_file = MacroFile(content=["/control/execute physics.mac\n"])
    block_files = [
        MacroFile(
            content=["\n", "/gate/physics/addProcess Compton gamma\n", "\n"], name="physics.mac"
        )
    ]

    # Act
    mono_macro = fold(main_file, block_files)

    # Assert
    assert mono_macro.content == ["/gate/physics/addProcess Compton gamma\n"]


@pytest.mark.parametrize("fixture_group", ALL_GROUPS)
def test_fold_of_unfold_round_trips_mono_content(fixture_group: str) -> None:
    """fold(*unfold(mono)) should reproduce the original mono macro content."""
    # Arrange
    mono_macro = read_macro_file(str(FIXTURES_DIR / fixture_group / "mono" / "macro.mac"))

    # Act
    main_file, block_files = unfold(mono_macro)
    refolded = fold(main_file, block_files)

    # Assert
    assert refolded.content == mono_macro.content
