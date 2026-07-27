"""Combine a set of macro files into a single mono macro file.

Folding replaces every ``/control/execute`` call in the main macro file with
the content of the referenced macro file. References are resolved by exact
file name first and case-insensitively as a fallback; references to files
that were not provided stay verbatim, since a macro may legitimately call
external macros that are not part of the folded set.

Public objects
--------------
fold
    Combine a main macro file and its block macro files into a mono macro
    file.
"""

import re

from ..io.macrofile import MacroContent, MacroFile

_EXECUTE_RE = re.compile(r"^/control/execute\s+(\S+)\s*$")


def fold(main_file: MacroFile, block_files: list[MacroFile]) -> MacroFile:
    """Combine a main macro file and its block macro files into one mono macro file.

    Parameters
    ----------
    main_file : MacroFile
        The main macro file, referring to block macro files through
        ``/control/execute`` calls.
    block_files : list[MacroFile]
        The macro files that may be referenced by ``main_file``.

    Returns
    -------
    MacroFile
        The combined mono macro file. Its ``name`` is left unset; the
        caller is expected to assign one.
    """
    by_name: dict[str, MacroFile] = {
        block_file.name: block_file for block_file in block_files if block_file.name is not None
    }
    by_lower_name: dict[str, MacroFile] = {name.lower(): file for name, file in by_name.items()}

    content: list[str] = []
    for line in main_file.content:
        match = _EXECUTE_RE.match(line)
        block_file = None
        if match is not None:
            reference = match.group(1)
            block_file = by_name.get(reference) or by_lower_name.get(reference.lower())
        if block_file is None:
            content.append(line)
        else:
            content.extend(_stripped_content(block_file))

    return MacroFile(
        content=content,
        is_mono_macro=True,
        content_type=MacroContent.MONO_MACRO,
    )


def _stripped_content(block_file: MacroFile) -> list[str]:
    """Content of a block file without leading/trailing blank lines.

    The surrounding spacing lives in the main macro file, so outer blank
    lines of the block file must not be duplicated into the mono macro. The
    last line is completed with a newline, since the spliced content is
    always followed by further main macro lines.
    """
    lines = list(block_file.content)
    while lines and lines[0].strip() == "":
        lines = lines[1:]
    while lines and lines[-1].strip() == "":
        lines = lines[:-1]
    if lines and not lines[-1].endswith("\n"):
        lines[-1] = f"{lines[-1]}\n"
    return lines
