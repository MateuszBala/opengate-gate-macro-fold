"""Unit tests for command-line interface (``cli``)."""

from pathlib import Path
from typing import Any

import pytest

from opengate_gate_macro_fold import cli


class _DummyLogger:
    """Minimal logger stub used to assert log messages in tests."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.infos: list[str] = []

    def error(self, message: str, *args: Any) -> None:
        self.errors.append(message % args if args else message)

    def info(self, message: str, *args: Any) -> None:
        self.infos.append(message % args if args else message)


def test_build_parser_parses_default_values() -> None:
    """Parser should accept empty arguments and apply defaults."""
    # Arrange
    parser = cli.build_parser()

    # Act
    args = parser.parse_args([])

    # Assert
    assert args.fold is False
    assert args.unfold is False
    assert args.input_mono_macro_file is None
    assert args.input_macros_dir is None
    assert args.output_dir is None
    assert args.title is None


def test_build_parser_parses_known_flags() -> None:
    """Parser should parse all supported CLI options."""
    # Arrange
    parser = cli.build_parser()

    # Act
    args = parser.parse_args(
        [
            "--fold",
            "--input-macros-dir",
            "macros",
            "--output-dir",
            "out",
            "--title",
            "example",
        ]
    )

    # Assert
    assert args.fold is True
    assert args.unfold is False
    assert args.input_macros_dir == "macros"
    assert args.output_dir == "out"
    assert args.title == "example"


def test_config_from_args_builds_run_config() -> None:
    """_config_from_args should map parsed values into RunConfig."""
    # Arrange
    parser = cli.build_parser()
    args = parser.parse_args(
        [
            "--unfold",
            "--input-mono-macro-file",
            "mono.mac",
            "--output-dir",
            "results",
        ]
    )

    # Act
    config = cli._config_from_args(args)

    # Assert
    assert config.fold is False
    assert config.unfold is True
    assert config.input_mono_macro_file == Path("mono.mac")
    assert config.input_macros_dir is None
    assert config.output_dir == Path("results")


def test_parser_error_message_uses_english_error_prefix(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Parser should report invalid arguments with the English error prefix."""
    # Arrange
    parser = cli.build_parser()

    # Act / Assert
    with pytest.raises(SystemExit):
        parser.parse_args(["--unknown-option"])
    assert "error:" in capsys.readouterr().err


def test_main_returns_one_when_processing_placeholder_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """main should return 1 while processing placeholder returns no output path."""
    # Arrange
    logger = _DummyLogger()
    monkeypatch.setattr(cli, "configure_logging", lambda: None)
    monkeypatch.setattr(cli, "get_logger", lambda _name: logger)

    # Act
    exit_code = cli.main(["--output-dir", "out"])

    # Assert
    assert exit_code == 1
    assert logger.errors == ["No output path returned from processing."]


def test_main_returns_one_when_config_build_raises_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """main should handle ValueError from config construction and return 1."""
    # Arrange
    logger = _DummyLogger()
    monkeypatch.setattr(cli, "configure_logging", lambda: None)
    monkeypatch.setattr(cli, "get_logger", lambda _name: logger)

    def _raise_value_error(_args: object) -> object:
        raise ValueError("invalid configuration")

    monkeypatch.setattr(cli, "_config_from_args", _raise_value_error)

    # Act
    exit_code = cli.main([])

    # Assert
    assert exit_code == 1
    assert logger.errors == ["Error: invalid configuration"]
