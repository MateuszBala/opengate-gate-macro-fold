# opengate-gate-macro-fold

[![CI](https://github.com/MateuszBala/opengate-gate-macro-fold/actions/workflows/ci.yaml/badge.svg)](https://github.com/MateuszBala/opengate-gate-macro-fold/actions/workflows/ci.yaml)
[![Version](https://img.shields.io/badge/version-0.0.0-informational)](https://github.com/MateuszBala/opengate-gate-macro-fold/releases)
[![Standard Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)]()
[![Standard Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)]()
[![Standard Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)]()
[![Standard Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)]()
[![license](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

`opengate-gate-macro-fold` is a utility for managing [GATE 9](https://github.com/OpenGATE/Gate) simulation macro files. It supports:

- **Folding**: combining a directory of macro files into a single mono macro file.
- **Unfolding**: splitting a mono macro file into a directory of macro files.

This workflow is practical when switching between batch execution environments (for example, clusters) and local or interactive simulation workflows.

## Quick Start

### Install From PyPI

```bash
pip3 install opengate-gate-macro-fold
```

### Install From Source

```bash
make init
make install
```

### Fold A Macro Set Into A Mono Macro

```bash
opengate-gate-macro-fold \
  --fold \
  --input-macros-dir=path/to/macros/directory \
  --output-dir=path/to/output/directory \
  [--title="my-mono-macro.mac"]
```

### Unfold A Mono Macro Into A Macro Set

```bash
opengate-gate-macro-fold \
  --unfold \
  --input-mono-macro-file=path/to/mono/macro.mac \
  --output-dir=path/to/output/directory
```

## Command-Line Options

- `--fold`: enable fold mode (macro set -> mono macro).
- `--unfold`: enable unfold mode (mono macro -> macro set).
- `--input-macros-dir`: source directory used in fold mode.
- `--input-mono-macro-file`: source mono macro file used in unfold mode.
- `--output-dir`: destination directory for generated output.
- `--title`: optional title metadata for mono macro output.

## Development

Common development commands:

```bash
make lint
make format
make typecheck
make test
make check
```

Project conventions and contribution standards:

- [Coding conventions](docs/CODING_CONVENTIONS.md)
- [Testing conventions](docs/TESTING_CONVENTIONS.md)
- [Commit conventions](docs/COMMIT_CONVENTIONS.md)
- [Contribution guide](docs/CONTRIBUTION.md)

## License

MIT License

Contact: [GitHub](https://github.com/MateuszBala)

## Author

The project was designed and implemented by Mateusz Jakub Bała.

Contact: [GitHub](https://github.com/MateuszBala)


## Contribution

To contribute new functionality:

- create a branch from `develop`
- follow the [commit conventions](docs/COMMIT_CONVENTIONS.md)
- open a PR using the [PR template](.github/PULL_REQUEST_TEMPLATE.md)
- follow the [contribution guide](docs/CONTRIBUTION.md)