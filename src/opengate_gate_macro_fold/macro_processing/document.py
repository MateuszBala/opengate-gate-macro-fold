"""Shared parsing model for mono macro and main macro files.

A mono macro file and a main macro file share the same structure: a
sequence of literal lines interleaved with "execute blocks" delimited by
``# BEGIN EXECUTE <name>`` / ``# END EXECUTE <name>`` markers. In a mono
macro file, an execute block body holds the real macro commands for
``<name>``. In a main macro file, the same block body holds a single
``/control/execute <name>`` call.

Public objects
--------------
ExecuteBlock
    The body of a single ``BEGIN EXECUTE`` / ``END EXECUTE`` block.
Document
    An ordered sequence of literal lines and ``ExecuteBlock`` instances.
parse_document
    Parse macro file lines into a ``Document``.
render_document
    Render a ``Document`` back into macro file lines.
"""

import re
from dataclasses import dataclass

_BEGIN_RE = re.compile(r"^# BEGIN EXECUTE (\S+)\s*$")
_END_RE = re.compile(r"^# END EXECUTE (\S+)\s*$")


@dataclass(frozen=True)
class ExecuteBlock:
    """The body of a single ``BEGIN EXECUTE`` / ``END EXECUTE`` block.

    Attributes
    ----------
    name : str
        Name of the referenced macro file, e.g. ``detector.mac``.
    body : list[str]
        Content lines between the ``BEGIN`` and ``END`` markers.
    """

    name: str
    body: list[str]


Document = list[str | ExecuteBlock]


def parse_document(lines: list[str]) -> Document:
    """Parse macro file lines into a ``Document``.

    Parameters
    ----------
    lines : list[str]
        Lines of a mono macro file or a main macro file, each ending with
        a newline character (except possibly the last one).

    Returns
    -------
    Document
        Literal lines interleaved with parsed ``ExecuteBlock`` instances,
        in their original order.

    Raises
    ------
    ValueError
        If a ``BEGIN EXECUTE`` marker is not closed by a matching
        ``END EXECUTE`` marker before the end of the input.
    """
    document: Document = []
    index = 0
    while index < len(lines):
        line = lines[index]
        begin_match = _BEGIN_RE.match(line.rstrip("\n"))
        if begin_match is None:
            document.append(line)
            index += 1
            continue

        name = begin_match.group(1)
        document.append(line)
        index += 1

        body: list[str] = []
        end_line: str | None = None
        while index < len(lines):
            candidate = lines[index]
            end_match = _END_RE.match(candidate.rstrip("\n"))
            if end_match is not None:
                if end_match.group(1) != name:
                    raise ValueError(
                        f"Mismatched EXECUTE markers: expected "
                        f"'# END EXECUTE {name}' but found "
                        f"'# END EXECUTE {end_match.group(1)}'."
                    )
                end_line = candidate
                index += 1
                break
            body.append(candidate)
            index += 1

        if end_line is None:
            raise ValueError(
                f"Unterminated EXECUTE block for '{name}': missing '# END EXECUTE {name}' marker."
            )

        document.append(ExecuteBlock(name=name, body=body))
        document.append(end_line)

    return document


def render_document(document: Document, *, as_control_execute: bool) -> list[str]:
    """Render a ``Document`` back into macro file lines.

    Parameters
    ----------
    document : Document
        Literal lines interleaved with ``ExecuteBlock`` instances.
    as_control_execute : bool
        When ``True``, each ``ExecuteBlock`` is rendered as a single
        ``/control/execute <name>`` call surrounded by blank lines, instead
        of its real body. Use this to produce a main macro file.

    Returns
    -------
    list[str]
        Rendered macro file lines.
    """
    lines: list[str] = []
    for segment in document:
        if isinstance(segment, ExecuteBlock):
            if as_control_execute:
                lines.extend(["\n", f"/control/execute {segment.name}\n", "\n"])
            else:
                lines.extend(segment.body)
        else:
            lines.append(segment)
    return lines
