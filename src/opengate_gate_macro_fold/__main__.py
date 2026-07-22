"""Entry point for ``python -m opengate_gate_macro_fold``.

Delegates execution to :func:`opengate_gate_macro_fold.cli.main`.
"""

import sys

from opengate_gate_macro_fold.cli import main

if __name__ == "__main__":
    sys.exit(main())
