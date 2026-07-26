"""Split a mono macro file into a set of macro files.

Public objects
--------------
unfold
    Split a mono macro file into a main macro file and a list of block
    macro files.
"""

from ..io.macrofile import MacroContent, MacroFile
from .document import ExecuteBlock, parse_document, render_document

_CONTENT_TYPE_BY_NAME: dict[str, MacroContent] = {
    "detector.mac": MacroContent.DETECTOR,
    "application.mac": MacroContent.APPLICATION,
    "output.mac": MacroContent.OUTPUT,
    "phantom.mac": MacroContent.PHANTOM,
    "physics.mac": MacroContent.PHYSICS,
    "random.mac": MacroContent.RANDOM,
    "source.mac": MacroContent.SOURCE,
    "visualisation.mac": MacroContent.VISUALIZATION,
}


def unfold(
    mono_macro: MacroFile, main_file_name: str = "main.mac"
) -> tuple[MacroFile, list[MacroFile]]:
    """Split a mono macro file into a main macro file and its execute blocks.

    Parameters
    ----------
    mono_macro : MacroFile
        The mono macro file to split.
    main_file_name : str
        Name to give the produced main macro file.

    Returns
    -------
    tuple[MacroFile, list[MacroFile]]
        The main macro file (with ``/control/execute`` calls) and the list
        of block macro files it refers to.
    """
    document = parse_document(mono_macro.content)

    block_files = [
        MacroFile(
            content=segment.body,
            name=segment.name,
            content_type=_CONTENT_TYPE_BY_NAME.get(segment.name),
        )
        for segment in document
        if isinstance(segment, ExecuteBlock)
    ]

    main_file = MacroFile(
        content=render_document(document, as_control_execute=True),
        name=main_file_name,
        content_type=MacroContent.MAIN,
    )

    return main_file, block_files
