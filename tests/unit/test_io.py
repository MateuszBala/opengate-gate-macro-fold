"""Unit tests for macro file I/O helpers."""

from pathlib import Path

from opengate_gate_macro_fold.io.macrofile import MacroFile
from opengate_gate_macro_fold.io.readers import read_macro_file, read_macrs_from_directory
from opengate_gate_macro_fold.io.writers import write_macro_file


def test_read_macro_file_reads_content_and_metadata(tmp_path: Path) -> None:
    """read_macro_file should load file content and infer mono macro metadata."""
    # Arrange
    mono_dir = tmp_path / "mono"
    mono_dir.mkdir()
    macro_path = mono_dir / "example.mac"
    macro_path.write_text("line 1\nline 2\n", encoding="utf-8")

    # Act
    macro_file = read_macro_file(str(macro_path))

    # Assert
    assert macro_file == MacroFile(
        path=macro_path,
        content=["line 1\n", "line 2\n"],
        is_mono_macro=True,
        name="example.mac",
    )


def test_read_macrs_from_directory_reads_files_in_sorted_order(tmp_path: Path) -> None:
    """read_macrs_from_directory should return files sorted by file name."""
    # Arrange
    macro_directory = tmp_path / "set"
    macro_directory.mkdir()
    (macro_directory / "b.mac").write_text("b\n", encoding="utf-8")
    (macro_directory / "a.mac").write_text("a\n", encoding="utf-8")
    (macro_directory / "nested").mkdir()

    # Act
    macro_files = read_macrs_from_directory(str(macro_directory))

    # Assert
    assert [macro_file.name for macro_file in macro_files] == ["a.mac", "b.mac"]
    assert [macro_file.content for macro_file in macro_files] == [["a\n"], ["b\n"]]
    assert all(macro_file.is_mono_macro is False for macro_file in macro_files)


def test_write_macro_file_writes_content_to_named_file(tmp_path: Path) -> None:
    """write_macro_file should create a file named after the MacroFile instance."""
    # Arrange
    output_directory = tmp_path / "output"
    output_directory.mkdir()
    macro_file = MacroFile(
        content=["first line\n", "second line\n"],
        name="output.mac",
    )

    # Act
    write_macro_file(macro_file, output_directory)

    # Assert
    assert (output_directory / "output.mac").read_text(encoding="utf-8") == (
        "first line\nsecond line\n"
    )


def test_write_macro_file_round_trips_reader_output(tmp_path: Path) -> None:
    """write_macro_file should preserve the content produced by read_macro_file."""
    # Arrange
    source_directory = tmp_path / "mono"
    source_directory.mkdir()
    source_path = source_directory / "roundtrip.mac"
    source_path.write_text("alpha\nbeta\n", encoding="utf-8")
    output_directory = tmp_path / "written"
    output_directory.mkdir()

    # Act
    macro_file = read_macro_file(str(source_path))
    write_macro_file(macro_file, output_directory)

    # Assert
    assert (output_directory / "roundtrip.mac").read_text(encoding="utf-8") == "alpha\nbeta\n"
