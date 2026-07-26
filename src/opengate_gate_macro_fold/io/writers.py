"""Write macro files

Public objects
--------------
write_macro_file
    Write a MacroFile object to the specified file path.
"""

from pathlib import Path

from .macrofile import MacroFile


def write_macro_file(macro_file: MacroFile, output_directory_path: Path) -> None:
    """Write a MacroFile object to the specified file path.

    Parameters
    ----------
    macro_file : MacroFile
        The MacroFile object containing the content to write.
    output_directory_path : Path
        The path to the directory where the file should be written.
    """
    if macro_file.name is None:
        raise ValueError("MacroFile.name is required to write a macro file.")

    file_path = output_directory_path / macro_file.name
    with open(file_path, "w") as f:
        f.writelines(macro_file.content)
