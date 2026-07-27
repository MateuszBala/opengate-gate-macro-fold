"""Split a mono macro file into a set of macro files.

Splitting is driven by GATE command classification, never by comments:
contiguous runs of same-category commands become category macro files, and
the main macro file keeps everything else verbatim with each extracted
region replaced by a single ``/control/execute`` call. Interior comments and
blank lines travel with their region; comments and blank lines surrounding a
region stay in the main macro file.

Public objects
--------------
unfold
    Split a mono macro file into a main macro file and category macro files.
"""

from dataclasses import dataclass
from typing import Final

from ..io.macrofile import MacroContent, MacroFile
from .classification import EXECUTE_RE, Category, CommandClassifier, command_of

# File name and content type of the macro file each category is extracted to.
_CATEGORY_FILES: Final[dict[Category, tuple[str, MacroContent]]] = {
    Category.DETECTOR: ("detector.mac", MacroContent.DETECTOR),
    Category.PHANTOM: ("phantom.mac", MacroContent.PHANTOM),
    Category.GEOMETRY_COMMON: ("geometry.mac", MacroContent.GEOMETRY),
    Category.PHYSICS: ("physics.mac", MacroContent.PHYSICS),
    Category.DIGITIZER: ("digitizer.mac", MacroContent.DIGITIZER),
    Category.ACTOR: ("actor.mac", MacroContent.ACTOR),
    Category.SOURCE: ("source.mac", MacroContent.SOURCE),
    Category.OUTPUT: ("output.mac", MacroContent.OUTPUT),
    Category.RANDOM: ("random.mac", MacroContent.RANDOM),
    Category.APPLICATION: ("application.mac", MacroContent.APPLICATION),
    Category.VISUALIZATION: ("visualisation.mac", MacroContent.VISUALIZATION),
}

_GEOMETRY_FAMILY = (Category.DETECTOR, Category.PHANTOM, Category.GEOMETRY_COMMON)


@dataclass
class _Run:
    """A contiguous run of same-category commands inside the mono macro."""

    start: int
    end: int
    category: Category
    # For geometry runs: DETECTOR or PHANTOM once determined by any command.
    resolved: Category | None = None

    @property
    def effective_category(self) -> Category:
        """Category deciding the target macro file of this run."""
        if self.category in _GEOMETRY_FAMILY:
            return self.resolved or Category.GEOMETRY_COMMON
        return self.category

    @property
    def file_name(self) -> str:
        """Name of the macro file this run is extracted to."""
        return _CATEGORY_FILES[self.effective_category][0]

    @property
    def content_type(self) -> MacroContent:
        """Content type of the macro file this run is extracted to."""
        return _CATEGORY_FILES[self.effective_category][1]


def unfold(
    mono_macro: MacroFile, main_file_name: str = "main.mac"
) -> tuple[MacroFile, list[MacroFile]]:
    """Split a mono macro file into a main macro file and category files.

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
        of extracted category macro files.
    """
    lines = mono_macro.content
    runs = _extract_runs(lines)

    block_files = [
        MacroFile(
            content=lines[run.start : run.end + 1],
            name=run.file_name,
            content_type=run.content_type,
        )
        for run in runs
    ]

    main_content: list[str] = []
    position = 0
    for run in runs:
        main_content.extend(lines[position : run.start])
        # A region at the end of a file without a final newline must keep
        # the file's byte length invariant through a fold round trip.
        suffix = "\n" if lines[run.end].endswith("\n") else ""
        main_content.append(f"/control/execute {run.file_name}{suffix}")
        position = run.end + 1
    main_content.extend(lines[position:])

    main_file = MacroFile(
        content=main_content,
        name=main_file_name,
        content_type=MacroContent.MAIN,
    )

    return main_file, block_files


def _extract_runs(lines: list[str]) -> list[_Run]:
    """Find the extracted regions: the first run per category file name.

    Runs whose target file name is already referenced by a pre-existing
    ``/control/execute`` line in the mono macro are not extracted; folding
    would otherwise splice the same file into both calls.
    """
    classifier = CommandClassifier(lines)

    runs: list[_Run] = []
    current: _Run | None = None
    for index, line in enumerate(lines):
        command = command_of(line)
        if command is None:
            continue
        category = classifier.classify(command)

        if category is Category.STRUCTURAL:
            current = _close(runs, current)
            continue

        if current is not None and _extends(current, category):
            current.end = index
            if current.category in _GEOMETRY_FAMILY and category in (
                Category.DETECTOR,
                Category.PHANTOM,
            ):
                current.resolved = current.resolved or category
            continue

        current = _close(runs, current)
        current = _Run(start=index, end=index, category=category)
        if category in (Category.DETECTOR, Category.PHANTOM):
            current.resolved = category
    _close(runs, current)

    reserved = {
        match.group(1).lower() for line in lines if (match := EXECUTE_RE.match(line)) is not None
    }
    seen: set[str] = set()
    first_runs: list[_Run] = []
    for run in runs:
        if run.file_name.lower() in reserved:
            continue
        if run.file_name not in seen:
            seen.add(run.file_name)
            first_runs.append(run)
    return first_runs


def _extends(run: _Run, category: Category) -> bool:
    """Whether a command of ``category`` continues ``run``."""
    if run.category in _GEOMETRY_FAMILY:
        if category not in _GEOMETRY_FAMILY:
            return False
        if category is Category.GEOMETRY_COMMON or run.resolved is None:
            return True
        return category is run.resolved
    return category is run.category


def _close(runs: list[_Run], current: _Run | None) -> _Run | None:
    """Append the current run (if any) to ``runs`` and reset it to ``None``."""
    if current is not None:
        runs.append(current)
    return None
