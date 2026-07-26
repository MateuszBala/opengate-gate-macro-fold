"""Macro file content

Public objects
--------------
MacroFile
    Represents a macro file with its path and content.
"""

import enum
from dataclasses import dataclass, field
from pathlib import Path


class MacroContent(enum.Enum):
    """Enumeration of macro content types."""

    MONO_MACRO = "mono_macro"
    DETECTOR = "detector"
    MAIN = "main"
    APPLICATION = "application"
    OUTPUT = "output"
    PHANTOM = "phantom"
    PHYSICS = "physics"
    RANDOM = "random"
    SOURCE = "source"
    VISUALIZATION = "visualization"


@dataclass(frozen=True)
class MacroFile:
    """Represents a macro file with its path and content.

    Attributes
    ----------
    path : Path
        Path to the macro file.
    content : List[str]
        Content of the macro file,each line as a separate string in the list.
    is_mono_macro : bool
        Flag indicating whether the macro file is a mono macro file.
    """

    path: Path | None = None
    content: list[str] = field(default_factory=list)
    is_mono_macro: bool = False
    content_type: MacroContent | None = None
