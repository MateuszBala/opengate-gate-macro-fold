"""Package command-line interface.

The module defines the entry point used by ``python -m
opengate_gate_macro_fold`` and the ``opengate-gate-macro-fold``
console script.

Public functions
----------------
build_parser() -> argparse.ArgumentParser
    Builds the command-line argument parser.
main(argv: list[str] | None = None) -> int
    Parses arguments, runs the processing pipeline, and returns an exit code.
"""

import argparse
import sys
from dataclasses import replace
from pathlib import Path
from typing import Final, NoReturn

from .config import RunConfig
from .io.macrofile import MacroFile
from .io.readers import read_macro_file, read_macrs_from_directory
from .io.writers import write_macro_file
from .logging_setup import configure_logging, get_logger
from .macro_processing.classification import EXECUTE_RE
from .macro_processing.folding import fold
from .macro_processing.unfolding import unfold

# Program name displayed in help output.
PROG_NAME: Final[str] = "opengate-gate-macro-fold"

# Name of the entry-point macro file inside a set of macro files,
# matched case-insensitively.
MAIN_MACRO_FILE_NAME: Final[str] = "main.mac"

# Default name for the mono macro file produced by --fold when --title is
# not provided.
DEFAULT_MONO_MACRO_FILE_NAME: Final[str] = "mono.mac"


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
        output_path = _run(config)
    except (OSError, ValueError) as error:
        # OSError covers wrong path types (IsADirectoryError,
        # NotADirectoryError) and permission problems; UnicodeDecodeError
        # from non-text inputs is a ValueError subclass.
        logger.error("Error: %s", error)
        return 1

    if output_path.is_file():
        logger.info("Done. Output saved to file: %s", output_path)
    else:
        logger.info("Done. Output saved to directory: %s", output_path)
    return 0


def _run(config: RunConfig) -> Path:
    """Run fold or unfold according to ``config`` and return the output path.

    Raises
    ------
    ValueError
        If the configuration is invalid (wrong flag combination, missing
        required paths, or a macro file referenced by the input is
        missing).
    """
    if config.fold == config.unfold:
        raise ValueError("Exactly one of --fold or --unfold must be specified.")
    if config.output_dir is None:
        raise ValueError("--output-dir is required.")

    if config.unfold:
        return _run_unfold(config, config.output_dir)
    return _run_fold(config, config.output_dir)


def _run_unfold(config: RunConfig, output_dir: Path) -> Path:
    """Split a mono macro file into a main macro file and its blocks."""
    if config.input_mono_macro_file is None:
        raise ValueError("--input-mono-macro-file is required for --unfold.")

    mono_macro = read_macro_file(str(config.input_mono_macro_file))
    main_file, block_files = unfold(mono_macro, main_file_name=MAIN_MACRO_FILE_NAME)

    output_dir.mkdir(parents=True, exist_ok=True)
    for macro_file in (main_file, *block_files):
        write_macro_file(macro_file, output_dir)

    return output_dir


def _run_fold(config: RunConfig, output_dir: Path) -> Path:
    """Combine a main macro file and its blocks into a mono macro file."""
    if config.input_macros_dir is None:
        raise ValueError("--input-macros-dir is required for --fold.")

    macro_files = read_macrs_from_directory(str(config.input_macros_dir))
    main_file = next(
        (
            macro_file
            for macro_file in macro_files
            if macro_file.name is not None and macro_file.name.lower() == MAIN_MACRO_FILE_NAME
        ),
        None,
    )
    if main_file is None:
        raise ValueError(f"No '{MAIN_MACRO_FILE_NAME}' file found in '{config.input_macros_dir}'.")
    block_files = [macro_file for macro_file in macro_files if macro_file is not main_file]

    output_name = _output_file_name(config.title)
    mono_macro = replace(fold(main_file, block_files), name=output_name)
    _warn_about_unused_files(main_file, block_files)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_macro_file(mono_macro, output_dir)

    return output_dir / output_name


def _output_file_name(title: str | None) -> str:
    """File name of the folded mono macro, derived from ``--title``.

    Raises
    ------
    ValueError
        If the title contains path separators or is a relative path
        component; the output must stay inside ``--output-dir``.
    """
    if not title:
        return DEFAULT_MONO_MACRO_FILE_NAME
    if "/" in title or "\\" in title or title in (".", ".."):
        raise ValueError(f"--title must be a plain file name, got: '{title}'.")
    return title if title.endswith(".mac") else f"{title}.mac"


def _warn_about_unused_files(main_file: MacroFile, block_files: list[MacroFile]) -> None:
    """Log block files that the main macro file never references."""
    logger = get_logger(__name__)
    referenced = {
        match.group(1).lower()
        for line in main_file.content
        if (match := EXECUTE_RE.match(line)) is not None
    }
    for block_file in block_files:
        if block_file.name is not None and block_file.name.lower() not in referenced:
            logger.warning(
                "File '%s' is not referenced by '%s' and was not folded in.",
                block_file.name,
                main_file.name,
            )


def _config_from_args(args: argparse.Namespace) -> RunConfig:
    """Build :class:`RunConfig` from parsed arguments."""
    return RunConfig(
        fold=args.fold,
        unfold=args.unfold,
        input_mono_macro_file=(
            Path(args.input_mono_macro_file) if args.input_mono_macro_file else None
        ),
        input_macros_dir=Path(args.input_macros_dir) if args.input_macros_dir else None,
        output_dir=Path(args.output_dir) if args.output_dir else None,
        title=args.title,
    )
