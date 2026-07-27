"""Classify GATE macro lines by the simulation section they belong to.

Classification is based purely on GATE 9 command paths; comments are never
interpreted, only carried along. Geometry commands need an extra whole-file
volume-tree pass: a volume belongs to the detector when it (or any
descendant) is attached to a system, declares a system type, or gets a
crystal sensitive detector; it belongs to the phantom when it (or any
descendant) gets a phantom sensitive detector.

Public objects
--------------
Category
    Simulation section a command belongs to.
command_of
    Extract the command text of a line, or ``None`` for comments/blanks.
CommandClassifier
    Classifies the commands of one mono macro file.
"""

import enum


class Category(enum.Enum):
    """Simulation section a GATE command belongs to."""

    DETECTOR = "detector"
    PHANTOM = "phantom"
    GEOMETRY_COMMON = "geometry_common"
    PHYSICS = "physics"
    DIGITIZER = "digitizer"
    ACTOR = "actor"
    SOURCE = "source"
    OUTPUT = "output"
    RANDOM = "random"
    APPLICATION = "application"
    VISUALISATION = "visualisation"
    STRUCTURAL = "structural"


_PREFIX_CATEGORIES: dict[str, Category] = {
    "/gate/physics": Category.PHYSICS,
    "/gate/digitizer": Category.DIGITIZER,
    "/gate/actor": Category.ACTOR,
    "/gate/source": Category.SOURCE,
    "/gate/output": Category.OUTPUT,
    "/gate/random": Category.RANDOM,
    "/gate/application": Category.APPLICATION,
    "/gate/geometry": Category.GEOMETRY_COMMON,
    "/gate/systems": Category.DETECTOR,
    "/gate/run": Category.STRUCTURAL,
    "/vis": Category.VISUALISATION,
    "/control": Category.STRUCTURAL,
}


def command_of(line: str) -> str | None:
    """Return the command text of a macro line, or ``None`` if there is none.

    A trailing inline comment (``#...``) is stripped for classification
    purposes only; comment-only and blank lines yield ``None``.
    """
    text = line.split("#", 1)[0].strip()
    return text or None


class CommandClassifier:
    """Classifies the commands of one mono macro file.

    The constructor runs the whole-file volume-tree pass; ``classify`` must
    then be called on the commands in file order, because
    ``/gate/<parent>/daughters/insert`` lines are resolved through the child
    volume named by the preceding ``daughters/name`` command.
    """

    def __init__(self, lines: list[str]) -> None:
        """Resolve volume names to DETECTOR / PHANTOM over the whole macro."""
        self._volume_classes = _classify_volumes(lines)
        self._last_defined_child = ""

    def classify(self, command: str) -> Category:
        """Map a GATE command to its ``Category``.

        Unknown commands are treated as ``STRUCTURAL`` so that they always
        stay in the main macro file.
        """
        if command == "exit":
            return Category.STRUCTURAL

        for prefix, category in _PREFIX_CATEGORIES.items():
            if command == prefix or command.startswith(f"{prefix}/"):
                return category

        if command.startswith("/gate/"):
            return self._classify_volume_command(command)

        return Category.STRUCTURAL

    def _classify_volume_command(self, command: str) -> Category:
        """Classify a ``/gate/<volume>/...`` command via the volume tree."""
        tokens = command.split()
        path = tokens[0].split("/")

        if len(path) >= 4 and path[3] == "daughters":
            # Daughters commands describe the child volume being defined.
            if len(path) >= 5 and path[4] == "name" and len(tokens) >= 2:
                self._last_defined_child = tokens[1]
            child = self._last_defined_child
            return self._volume_classes.get(child, Category.GEOMETRY_COMMON)

        volume = path[2] if len(path) >= 3 else ""
        return self._volume_classes.get(volume, Category.GEOMETRY_COMMON)


def _classify_volumes(lines: list[str]) -> dict[str, Category]:
    """Resolve volume names to DETECTOR or PHANTOM over a whole macro."""
    parents: dict[str, str] = {}
    evidence: dict[str, Category] = {}
    last_defined_child = ""

    for line in lines:
        command = command_of(line)
        if command is None:
            continue
        tokens = command.split()
        path = tokens[0].split("/")
        # path[0] is the empty string before the leading slash.
        if len(path) < 4 or path[1] != "gate":
            continue
        if path[3] == "daughters":
            if len(path) >= 5 and path[4] == "name" and len(tokens) >= 2:
                last_defined_child = tokens[1]
                parents[last_defined_child] = path[2]
            if len(path) >= 5 and path[4] == "systemType" and last_defined_child:
                evidence[last_defined_child] = Category.DETECTOR
        elif path[2] == "systems":
            if path[-1] == "attach" and len(tokens) >= 2:
                evidence[tokens[1]] = Category.DETECTOR
        elif path[3] == "attachCrystalSD":
            evidence[path[2]] = Category.DETECTOR
        elif path[3] == "attachPhantomSD":
            evidence.setdefault(path[2], Category.PHANTOM)

    classes: dict[str, Category] = {}
    for volume, category in evidence.items():
        # Propagate evidence up the volume tree, stopping at the world and
        # never overriding a volume that carries its own evidence.
        current: str | None = volume
        while current is not None and current != "world":
            classes.setdefault(current, evidence.get(current, category))
            current = parents.get(current)
    return classes
