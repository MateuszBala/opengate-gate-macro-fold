"""Unit tests for the shared macro document parsing model (``macro_processing.document``)."""

import pytest

from opengate_gate_macro_fold.macro_processing.document import (
    ExecuteBlock,
    parse_document,
    render_document,
)


def test_parse_document_splits_literal_lines_and_execute_blocks() -> None:
    """parse_document should separate literal lines from execute block bodies."""
    # Arrange
    lines = [
        "# HEADER\n",
        "# BEGIN EXECUTE detector.mac\n",
        "/gate/geometry/setMaterialDatabase GateMaterials.db\n",
        "# END EXECUTE detector.mac\n",
        "\n",
        "/gate/run/initialize\n",
    ]

    # Act
    document = parse_document(lines)

    # Assert
    assert document == [
        "# HEADER\n",
        "# BEGIN EXECUTE detector.mac\n",
        ExecuteBlock(
            name="detector.mac",
            body=["/gate/geometry/setMaterialDatabase GateMaterials.db\n"],
        ),
        "# END EXECUTE detector.mac\n",
        "\n",
        "/gate/run/initialize\n",
    ]


def test_parse_document_raises_for_unterminated_block() -> None:
    """parse_document should raise ValueError when an END marker is missing."""
    # Arrange
    lines = [
        "# BEGIN EXECUTE detector.mac\n",
        "/gate/geometry/setMaterialDatabase GateMaterials.db\n",
    ]

    # Act / Assert
    with pytest.raises(ValueError, match="Unterminated EXECUTE block for 'detector.mac'"):
        parse_document(lines)


def test_parse_document_raises_for_mismatched_end_marker() -> None:
    """parse_document should raise ValueError when the END marker name does not match."""
    # Arrange
    lines = [
        "# BEGIN EXECUTE detector.mac\n",
        "/gate/geometry/setMaterialDatabase GateMaterials.db\n",
        "# END EXECUTE phantom.mac\n",
    ]

    # Act / Assert
    with pytest.raises(ValueError, match="Mismatched EXECUTE markers"):
        parse_document(lines)


def test_render_document_reproduces_original_lines_by_default() -> None:
    """render_document should reproduce the original content when not rendering placeholders."""
    # Arrange
    lines = [
        "# BEGIN EXECUTE detector.mac\n",
        "/gate/geometry/setMaterialDatabase GateMaterials.db\n",
        "# END EXECUTE detector.mac\n",
    ]
    document = parse_document(lines)

    # Act
    rendered = render_document(document, as_control_execute=False)

    # Assert
    assert rendered == lines


def test_render_document_renders_control_execute_call() -> None:
    """render_document should replace block bodies with /control/execute calls."""
    # Arrange
    lines = [
        "# BEGIN EXECUTE detector.mac\n",
        "/gate/geometry/setMaterialDatabase GateMaterials.db\n",
        "# END EXECUTE detector.mac\n",
    ]
    document = parse_document(lines)

    # Act
    rendered = render_document(document, as_control_execute=True)

    # Assert
    assert rendered == [
        "# BEGIN EXECUTE detector.mac\n",
        "\n",
        "/control/execute detector.mac\n",
        "\n",
        "# END EXECUTE detector.mac\n",
    ]
