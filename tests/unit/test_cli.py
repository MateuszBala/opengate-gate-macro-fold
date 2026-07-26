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


def test_main_returns_one_when_neither_fold_nor_unfold_specified(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """main should reject a configuration where fold and unfold are both False."""
    # Arrange
    logger = _DummyLogger()
    monkeypatch.setattr(cli, "configure_logging", lambda: None)
    monkeypatch.setattr(cli, "get_logger", lambda _name: logger)

    # Act
    exit_code = cli.main(["--output-dir", str(tmp_path)])

    # Assert
    assert exit_code == 1
    assert logger.errors == ["Error: Exactly one of --fold or --unfold must be specified."]


def test_main_returns_one_when_both_fold_and_unfold_specified(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """main should reject a configuration where fold and unfold are both True."""
    # Arrange
    logger = _DummyLogger()
    monkeypatch.setattr(cli, "configure_logging", lambda: None)
    monkeypatch.setattr(cli, "get_logger", lambda _name: logger)

    # Act
    exit_code = cli.main(["--fold", "--unfold", "--output-dir", str(tmp_path)])

    # Assert
    assert exit_code == 1
    assert logger.errors == ["Error: Exactly one of --fold or --unfold must be specified."]


def test_main_unfolds_mono_macro_file_into_set_of_macro_files(tmp_path: Path) -> None:
    """main should split a mono macro file into main.mac and its block files."""
    # Arrange
    mono_path = tmp_path / "macro.mac"
    mono_path.write_text(
        "# BEGIN EXECUTE detector.mac\n"
        "/gate/geometry/setMaterialDatabase GateMaterials.db\n"
        "# END EXECUTE detector.mac\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "out"

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
    assert (output_dir / "detector.mac").read_text(encoding="utf-8") == (
        "/gate/geometry/setMaterialDatabase GateMaterials.db\n"
    )
    main_content = (output_dir / "main.mac").read_text(encoding="utf-8")
    assert "/control/execute detector.mac" in main_content


def test_main_folds_set_of_macro_files_into_mono_macro_file(tmp_path: Path) -> None:
    """main should combine main.mac and its block files into a mono macro file."""
    # Arrange
    macros_dir = tmp_path / "macros"
    macros_dir.mkdir()
    (macros_dir / "main.mac").write_text(
        "# BEGIN EXECUTE detector.mac\n"
        "\n"
        "/control/execute detector.mac\n"
        "\n"
        "# END EXECUTE detector.mac\n",
        encoding="utf-8",
    )
    (macros_dir / "detector.mac").write_text(
        "/gate/geometry/setMaterialDatabase GateMaterials.db\n",
        encoding="utf-8",
    )
    output_dir = tmp_path / "out"

    # Act
    exit_code = cli.main(
        [
            "--fold",
            "--input-macros-dir",
            str(macros_dir),
            "--output-dir",
            str(output_dir),
            "--title",
            "example",
        ]
    )

    # Assert
    assert exit_code == 0
    assert (output_dir / "example.mac").read_text(encoding="utf-8") == (
        "# BEGIN EXECUTE detector.mac\n"
        "/gate/geometry/setMaterialDatabase GateMaterials.db\n"
        "# END EXECUTE detector.mac\n"
    )


def test_main_folds_without_title_uses_default_mono_file_name(tmp_path: Path) -> None:
    """main should name the folded mono file 'mono.mac' when --title is not given."""
    # Arrange
    macros_dir = tmp_path / "macros"
    macros_dir.mkdir()
    (macros_dir / "main.mac").write_text(
        "# BEGIN EXECUTE detector.mac\n"
        "\n"
        "/control/execute detector.mac\n"
        "\n"
        "# END EXECUTE detector.mac\n",
        encoding="utf-8",
    )
    (macros_dir / "detector.mac").write_text(
        "/gate/geometry/setMaterialDatabase GateMaterials.db\n", encoding="utf-8"
    )
    output_dir = tmp_path / "out"

    # Act
    exit_code = cli.main(
        [
            "--fold",
            "--input-macros-dir",
            str(macros_dir),
            "--output-dir",
            str(output_dir),
        ]
    )

    # Assert
    assert exit_code == 0
    assert (output_dir / "mono.mac").exists()


def test_main_returns_one_when_main_macro_file_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """main should reject a --fold input directory without a main.mac file."""
    # Arrange
    logger = _DummyLogger()
    monkeypatch.setattr(cli, "configure_logging", lambda: None)
    monkeypatch.setattr(cli, "get_logger", lambda _name: logger)
    macros_dir = tmp_path / "macros"
    macros_dir.mkdir()
    (macros_dir / "detector.mac").write_text(
        "/gate/geometry/setMaterialDatabase GateMaterials.db\n", encoding="utf-8"
    )

    # Act
    exit_code = cli.main(
        [
            "--fold",
            "--input-macros-dir",
            str(macros_dir),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )

    # Assert
    assert exit_code == 1
    assert logger.errors == [f"Error: No 'main.mac' file found in '{macros_dir}'."]


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
