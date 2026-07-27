"""Unit tests for the category-based mono macro split (``unfold``)."""

from pathlib import Path

import pytest

from opengate_gate_macro_fold.io.macrofile import MacroContent, MacroFile
from opengate_gate_macro_fold.io.readers import read_macro_file, read_macrs_from_directory
from opengate_gate_macro_fold.macro_processing.unfolding import unfold

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

CANONICAL_GROUPS = ["full-stack", "partial-stack", "full-statc-without-text"]


@pytest.mark.parametrize("fixture_group", CANONICAL_GROUPS)
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


@pytest.mark.parametrize("fixture_group", CANONICAL_GROUPS)
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


def test_unfold_keeps_structural_commands_in_main() -> None:
    """Structural commands must never be extracted into category files."""
    # Arrange
    mono_macro = MacroFile(
        content=[
            "/gate/physics/addProcess Compton gamma\n",
            "/gate/run/initialize\n",
            "exit\n",
        ]
    )

    # Act
    main_file, block_files = unfold(mono_macro)

    # Assert
    assert [block_file.name for block_file in block_files] == ["physics.mac"]
    assert main_file.content == [
        "/control/execute physics.mac\n",
        "/gate/run/initialize\n",
        "exit\n",
    ]


def test_unfold_keeps_second_run_of_a_category_in_main() -> None:
    """Only the first run of a category is extracted; later runs stay in main."""
    # Arrange
    mono_macro = MacroFile(
        content=[
            "/gate/physics/addProcess Compton gamma\n",
            "/gate/run/initialize\n",
            "/gate/physics/displayCuts\n",
        ]
    )

    # Act
    main_file, block_files = unfold(mono_macro)

    # Assert
    assert [block_file.name for block_file in block_files] == ["physics.mac"]
    assert main_file.content == [
        "/control/execute physics.mac\n",
        "/gate/run/initialize\n",
        "/gate/physics/displayCuts\n",
    ]


def test_unfold_keeps_surrounding_comments_in_main() -> None:
    """Comments before and after a region stay in main; interior ones travel with it."""
    # Arrange
    mono_macro = MacroFile(
        content=[
            "# PHYSICS SECTION\n",
            "/gate/physics/addProcess Compton gamma\n",
            "# interior comment\n",
            "/gate/physics/processList Enabled\n",
            "# trailing comment\n",
        ]
    )

    # Act
    main_file, block_files = unfold(mono_macro)

    # Assert
    assert main_file.content == [
        "# PHYSICS SECTION\n",
        "/control/execute physics.mac\n",
        "# trailing comment\n",
    ]
    assert block_files[0].content == [
        "/gate/physics/addProcess Compton gamma\n",
        "# interior comment\n",
        "/gate/physics/processList Enabled\n",
    ]


def test_unfold_splits_detector_and_phantom_regions() -> None:
    """A geometry run must split where volume ownership changes to the phantom tree."""
    # Arrange
    mono_macro = MacroFile(
        content=[
            "/gate/world/daughters/name scanner\n",
            "/gate/world/daughters/insert cylinder\n",
            "/gate/scanner/attachCrystalSD\n",
            "/gate/world/daughters/name NEMA_IQ\n",
            "/gate/world/daughters/insert box\n",
            "/gate/NEMA_IQ/attachPhantomSD\n",
        ]
    )

    # Act
    main_file, block_files = unfold(mono_macro)

    # Assert
    assert [block_file.name for block_file in block_files] == ["detector.mac", "phantom.mac"]
    assert main_file.content == [
        "/control/execute detector.mac\n",
        "/control/execute phantom.mac\n",
    ]


def test_unfold_skips_runs_colliding_with_existing_execute_references() -> None:
    """A run whose file name is already referenced by /control/execute stays in main."""
    # Arrange
    mono_macro = MacroFile(
        content=[
            "/gate/physics/addProcess Compton gamma\n",
            "/gate/run/initialize\n",
            "/control/execute physics.mac\n",
        ]
    )

    # Act
    main_file, block_files = unfold(mono_macro)

    # Assert
    assert block_files == []
    assert main_file.content == mono_macro.content
