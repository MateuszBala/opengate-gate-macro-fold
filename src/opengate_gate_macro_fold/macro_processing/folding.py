"""Combine a set of macro files into a single mono macro file.

Public objects
--------------
fold
    Combine a main macro file and its block macro files into a mono macro
    file.
"""

from ..io.macrofile import MacroContent, MacroFile
from .document import ExecuteBlock, parse_document, render_document


def fold(main_file: MacroFile, block_files: list[MacroFile]) -> MacroFile:
    """Combine a main macro file and its block macro files into one mono macro file.

    Parameters
    ----------
    main_file : MacroFile
        The main macro file, referring to block macro files through
        ``/control/execute`` calls inside ``BEGIN EXECUTE``/``END EXECUTE``
        blocks.
    block_files : list[MacroFile]
        The macro files referenced by ``main_file``.

    Returns
    -------
    MacroFile
        The combined mono macro file. Its ``name`` is left unset; the
        caller is expected to assign one.

    Raises
    ------
    ValueError
        If ``main_file`` references a block macro file that is not present
        in ``block_files``.
    """
    blocks_by_name: dict[str, MacroFile] = {
        block_file.name: block_file for block_file in block_files if block_file.name is not None
    }

    document = parse_document(main_file.content)
    folded_document = [
        ExecuteBlock(name=segment.name, body=_resolve_body(segment.name, blocks_by_name))
        if isinstance(segment, ExecuteBlock)
        else segment
        for segment in document
    ]

    return MacroFile(
        content=render_document(folded_document, as_control_execute=False),
        is_mono_macro=True,
        content_type=MacroContent.MONO_MACRO,
    )


def _resolve_body(name: str, blocks_by_name: dict[str, MacroFile]) -> list[str]:
    """Return the content of the block macro file named ``name``.

    A missing trailing newline on the last line is completed, since the
    block body is followed by the ``# END EXECUTE`` marker line rather than
    the end of the file.
    """
    block_file = blocks_by_name.get(name)
    if block_file is None:
        raise ValueError(f"Missing macro file for execute block '{name}'.")

    body = block_file.content
    if body and not body[-1].endswith("\n"):
        body = [*body[:-1], f"{body[-1]}\n"]
    return body
