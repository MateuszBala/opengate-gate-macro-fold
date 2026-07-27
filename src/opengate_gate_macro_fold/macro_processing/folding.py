"""Combine a set of macro files into a single mono macro file.

Folding replaces every ``/control/execute`` call in the main macro file with
the content of the referenced macro file. References are resolved by exact
file name first and case-insensitively as a fallback; references to files
that were not provided stay verbatim (with a logged warning), since a macro
may legitimately call external macros that are not part of the folded set.

Public objects
--------------
fold
    Combine a main macro file and its block macro files into a mono macro
    file.
"""

from ..io.macrofile import MacroContent, MacroFile
from ..logging_setup import get_logger
from .classification import EXECUTE_RE


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
    logger = get_logger(__name__)
    by_name: dict[str, MacroFile] = {
        block_file.name: block_file for block_file in block_files if block_file.name is not None
    }
    by_lower_name = _unambiguous_lower_names(by_name)

    content: list[str] = []
    for line in main_file.content:
        match = EXECUTE_RE.match(line)
        if match is None:
            content.append(line)
            continue
        reference = match.group(1)
        block_file = by_name.get(reference) or by_lower_name.get(reference.lower())
        if block_file is None:
            logger.warning("Unresolved /control/execute reference '%s' kept verbatim.", reference)
            content.append(line)
        else:
            content.extend(_stripped_content(block_file, ensure_newline=line.endswith("\n")))

    return MacroFile(
        content=content,
        is_mono_macro=True,
        content_type=MacroContent.MONO_MACRO,
    )


def _unambiguous_lower_names(by_name: dict[str, MacroFile]) -> dict[str, MacroFile]:
    """Case-insensitive lookup map, excluding names that collide when lowered."""
    lowered: dict[str, list[str]] = {}
    for name in by_name:
        lowered.setdefault(name.lower(), []).append(name)
    return {lower: by_name[names[0]] for lower, names in lowered.items() if len(names) == 1}


def _stripped_content(block_file: MacroFile, *, ensure_newline: bool) -> list[str]:
    """Content of a block file without leading/trailing blank lines.

    The surrounding spacing lives in the main macro file, so outer blank
    lines of the block file must not be duplicated into the mono macro.
    When ``ensure_newline`` is set, the last line is completed with a
    newline because further main macro lines follow the spliced content.
    """
    lines = block_file.content
    first = 0
    while first < len(lines) and lines[first].strip() == "":
        first += 1
    last = len(lines) - 1
    while last >= first and lines[last].strip() == "":
        last -= 1
    lines = lines[first : last + 1]
    if ensure_newline and lines and not lines[-1].endswith("\n"):
        lines = [*lines[:-1], f"{lines[-1]}\n"]
    return lines
