"""Unit tests for GATE command classification (``macro_processing.classification``)."""

import pytest

from opengate_gate_macro_fold.macro_processing.classification import (
    Category,
    CommandClassifier,
    command_of,
)


@pytest.mark.parametrize(
    "line,expected",
    [
        ("/gate/physics/addProcess Compton gamma\n", "/gate/physics/addProcess Compton gamma"),
        ("/vis/disable # inline comment\n", "/vis/disable"),
        ("# a comment line\n", None),
        ("   \n", None),
        ("\n", None),
    ],
)
def test_command_of_extracts_command_text(line: str, expected: str | None) -> None:
    """command_of should strip comments and whitespace, returning None without a command."""
    # Act / Assert
    assert command_of(line) == expected


@pytest.mark.parametrize(
    "command,expected",
    [
        ("/gate/physics/addProcess Compton gamma", Category.PHYSICS),
        ("/gate/digitizer/Singles/insert adder", Category.DIGITIZER),
        ("/gate/actor/addActor LocalActor JPActor", Category.ACTOR),
        ("/gate/source/addSource src PositroniumSource", Category.SOURCE),
        ("/gate/output/root/enable", Category.OUTPUT),
        ("/gate/random/setEngineSeed auto", Category.RANDOM),
        ("/gate/application/startDAQ", Category.APPLICATION),
        ("/gate/geometry/setMaterialDatabase GateMaterials.db", Category.GEOMETRY_COMMON),
        ("/gate/systems/cylindricalPET/rsector/attach rsector", Category.DETECTOR),
        ("/vis/disable", Category.VISUALIZATION),
        ("/control/execute other.mac", Category.STRUCTURAL),
        ("/gate/run/initialize", Category.STRUCTURAL),
        ("exit", Category.STRUCTURAL),
    ],
)
def test_classify_maps_prefixes_to_categories(command: str, expected: Category) -> None:
    """classify should map GATE 9 command prefixes to their section category."""
    # Arrange
    classifier = CommandClassifier([])

    # Act / Assert
    assert classifier.classify(command) == expected


def test_classify_resolves_detector_volume_tree() -> None:
    """Volumes attached to a system or a crystal SD should classify as DETECTOR."""
    # Arrange
    lines = [
        "/gate/world/daughters/name scanner\n",
        "/gate/world/daughters/insert cylinder\n",
        "/gate/scanner/daughters/name crystal\n",
        "/gate/scanner/daughters/insert box\n",
        "/gate/crystal/attachCrystalSD\n",
    ]
    classifier = CommandClassifier(lines)

    # Act / Assert
    assert classifier.classify("/gate/crystal/attachCrystalSD") == Category.DETECTOR
    assert classifier.classify("/gate/scanner/setMaterial Vacuum") == Category.DETECTOR


def test_classify_resolves_phantom_volume_tree() -> None:
    """Volumes with a phantom SD should classify as PHANTOM, including daughters commands."""
    # Arrange
    lines = [
        "/gate/world/daughters/name NEMA_IQ\n",
        "/gate/world/daughters/insert box\n",
        "/gate/NEMA_IQ/attachPhantomSD\n",
    ]
    classifier = CommandClassifier(lines)

    # Act
    name_category = classifier.classify("/gate/world/daughters/name NEMA_IQ")
    insert_category = classifier.classify("/gate/world/daughters/insert box")

    # Assert
    assert name_category == Category.PHANTOM
    assert insert_category == Category.PHANTOM
    assert classifier.classify("/gate/NEMA_IQ/setMaterial Air") == Category.PHANTOM


def test_classify_resolves_system_type_volume_as_detector() -> None:
    """A daughters/systemType declaration should mark the defined child as DETECTOR."""
    # Arrange
    lines = [
        "/gate/world/daughters/name detector\n",
        "/gate/world/daughters/systemType scanner\n",
        "/gate/world/daughters/insert cylinder\n",
    ]
    classifier = CommandClassifier(lines)

    # Act / Assert
    assert classifier.classify("/gate/world/daughters/name detector") == Category.DETECTOR
    assert classifier.classify("/gate/detector/setMaterial EJ230") == Category.DETECTOR


def test_classify_treats_unresolved_volume_as_geometry_common() -> None:
    """World and volumes without SD or system evidence should be GEOMETRY_COMMON."""
    # Arrange
    classifier = CommandClassifier(["/gate/world/geometry/setXLength 300. cm\n"])

    # Act / Assert
    assert classifier.classify("/gate/world/geometry/setXLength 300. cm") == (
        Category.GEOMETRY_COMMON
    )


def test_classify_volumes_terminates_on_parent_cycle() -> None:
    """A malformed macro with a volume-parent cycle must not hang classification."""
    # Arrange
    lines = [
        "/gate/A/daughters/name A\n",
        "/gate/A/attachCrystalSD\n",
    ]

    # Act
    classifier = CommandClassifier(lines)

    # Assert
    assert classifier.classify("/gate/A/setMaterial Vacuum") == Category.DETECTOR
