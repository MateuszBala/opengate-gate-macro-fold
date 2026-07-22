"""Package command-line interface.

The module defines the entry point used by ``python -m
opengate_gate_macro_fold`` and the console scripts
``opengate-gate-macro-fold`` i ``cspae``.

Public functions
----------------
build_parser() -> argparse.ArgumentParser
    Builds the command-line argument parser.
main(argv: list[str] | None = None) -> int
    Parses arguments, runs the processing pipeline, and returns an exit code.
"""

import argparse
import sys
from pathlib import Path
from typing import NoReturn

from .config import RunConfig
from .logging_setup import configure_logging, get_logger

# Program name displayed in help output.
PROG_NAME = "opengate-gate-macro-fold"


class _PolishArgumentParser(argparse.ArgumentParser):
    """Argument parser that emits error messages in English."""

    def error(self, message: str) -> NoReturn:
        """Print usage and an English error message, then exit with status 2."""
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: error: {message}\n")



def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Configured parser with all tool flags.
    """
    parser = _PolishArgumentParser(
        prog=PROG_NAME,
        description=(""),
    )

    parser.add_argument(
        "--fold",
        action="store_true",
        help="Combine a set of macro files into one mono macro file",
    )

    parser.add_argument(
        "--unfold",
        action="store_true",
        help="Split a mono macro file into a set of macro files",
    )

    parser.add_argument(
        "--input-mono-macro-file",
        help="Path to the mono macro file to split into a set of macro files",
    )

    parser.add_argument(
        "--input-macros-dir",
        help="Path to the directory with macro files to combine into one mono macro file",
    )

    parser.add_argument(
        "--output-dir",
        help="Path to the directory where outputs will be written",
    )

    parser.add_argument(
        "--title",
        help="Mono macro title",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the tool from the command line.

    Parameters
    ----------
    argv : list[str] | None
        List of arguments to parse. If ``None``, arguments from ``sys.argv``
        are used.

    Returns
    -------
    int
        Process exit code (0 means success, 1 means processing error).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging()
    logger = get_logger(__name__)

    try:
        config = _config_from_args(args)
        output_path = None  # Placeholder for the actual processing function that returns the output path or directory.
    except (FileNotFoundError, ValueError) as error:
        logger.error("Error: %s", error)
        return 1

    if output_path is None:
        logger.error("No output path returned from processing.")
        return 1
    if not output_path.exists():
        logger.error("Output path does not exist: %s", output_path)
        return 1
    if not output_path.is_file() and not output_path.is_dir():
        logger.error("Output path is neither a file nor a directory: %s", output_path)
        return 1
    if output_path.is_file():
        logger.info("Done. Output saved to file: %s", output_path)
    elif output_path.is_dir():
        logger.info("Done. Output saved to directory: %s", output_path)
    return 0


def _config_from_args(args: argparse.Namespace) -> RunConfig:
    """Build :class:`RunConfig` from parsed arguments."""
    return RunConfig(
        fold=args.fold,
        unfold=args.unfold,
        input_mono_macro_file=Path(args.input_mono_macro_file) if args.input_mono_macro_file else None,
        input_macros_dir=Path(args.input_macros_dir) if args.input_macros_dir else None,
        output_dir=Path(args.output_dir) if args.output_dir else None,
        title=args.title
    )
