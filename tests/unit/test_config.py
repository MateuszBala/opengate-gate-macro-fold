"""Unit tests for runtime configuration (``config``)."""

import dataclasses
from pathlib import Path

import pytest

from opengate_gate_macro_fold.config import RunConfig


def test_run_config_stores_expected_values() -> None:
    """RunConfig should preserve all values passed at construction."""
    # Arrange / Act
    config = RunConfig(
        fold=True,
        unfold=False,
        input_mono_macro_file=Path("input.mono.mac"),
        input_macros_dir=Path("input-macros"),
        output_dir=Path("output"),
        title="example-title",
    )

    # Assert
    assert config.fold is True
    assert config.unfold is False
    assert config.input_mono_macro_file == Path("input.mono.mac")
    assert config.input_macros_dir == Path("input-macros")
    assert config.output_dir == Path("output")
    assert config.title == "example-title"


def test_run_config_uses_default_title_none() -> None:
    """The optional title should default to ``None``."""
    # Arrange / Act
    config = RunConfig(
        fold=False,
        unfold=True,
        input_mono_macro_file=Path("input.mono.mac"),
        input_macros_dir=None,
        output_dir=Path("output"),
    )

    # Assert
    assert config.title is None


def test_run_config_is_frozen() -> None:
    """RunConfig should be immutable (frozen dataclass)."""
    # Arrange
    config = RunConfig(
        fold=False,
        unfold=True,
        input_mono_macro_file=Path("input.mono.mac"),
        input_macros_dir=None,
        output_dir=Path("output"),
    )

    # Act / Assert
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.fold = True  # type: ignore[misc]
