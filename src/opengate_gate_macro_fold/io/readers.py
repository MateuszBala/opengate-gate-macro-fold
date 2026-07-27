"""Load macro files

Public objects
--------------
read_macro_file
    Read a macro file and return its content as a MacroFile object.
read_macrs_from_directory
    Read all macro files from a directory and return their content as a list of MacroFile objects
"""

from pathlib import Path

from .macrofile import MacroFile


def read_macro_file(file_path: str) -> MacroFile:
    """Read a macro file and return its content as a MacroFile object.

    Parameters
    ----------
    file_path : str
        Path to the macro file.

    Returns
    -------
    MacroFile
        An object containing the path and content of the macro file.
    """
    macro_path = Path(file_path)
    with macro_path.open("r", encoding="utf-8") as macro_file:
        content = macro_file.readlines()

    return MacroFile(
        path=macro_path,
        content=content,
        is_mono_macro=macro_path.parent.name == "mono",
        name=macro_path.name,
    )


def read_macrs_from_directory(macros_directory_path: str) -> list[MacroFile]:
    """Read all macro files from a directory and return their content as a list of MacroFile
    objects.

    Parameters
    ----------
    macros_directory_path : str
        Path to the directory containing macro files.

    Returns
    -------
    List[MacroFile]
        A list of MacroFile objects, each containing the path and content of a macro file.
    """
    macros_directory = Path(macros_directory_path)
    return [
        read_macro_file(str(macro_path))
        for macro_path in sorted(macros_directory.iterdir())
        if macro_path.is_file()
    ]
