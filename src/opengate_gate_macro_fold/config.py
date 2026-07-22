"""Tool runtime configuration.

The module defines :class:`RunConfig`, which stores parsed runtime arguments:
input/output paths, optional output title, and operation mode flags.

Public objects
--------------
RunConfig
    Immutable set of parameters for a single tool run.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunConfig:
    """Parameters for a single tool run.

    Attributes
    ----------
    fold : bool
        Flag indicating whether to combine a set of macro files into one mono macro file.
    unfold : bool
        Flag indicating whether to split a mono macro file into a set of macro files.
    input_mono_macro_file : Path
        Path to the mono macro file to split into a set of macro files.
    input_macros_dir : Path
        Path to the directory with macro files to combine into one mono macro file.
    output_dir : Path
        Path to the directory where outputs will be written.
    title : str | None
        Optional mono macro title.
    """

    fold: bool
    unfold: bool
    input_mono_macro_file: Path | None
    input_macros_dir: Path | None
    output_dir: Path
    title: str | None = None
