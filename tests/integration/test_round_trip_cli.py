"""Integration test: round-trip a mono macro file through two CLI invocations.

This is the highest-complexity CLI-level check: it chains ``--unfold``
followed by ``--fold``, both driven exclusively through ``cli.main``, and
asserts the fixture mono macro file survives the full trip unchanged.
"""

from pathlib import Path

import pytest

from opengate_gate_macro_fold import cli

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.mark.parametrize(
    "fixture_group",
    ["full-stack", "partial-stack", "full-statc-without-text", "partial-stack-actor-example"],
)
def test_main_round_trips_unfold_then_fold(fixture_group: str, tmp_path: Path) -> None:
    """Unfolding then folding a fixture mono file through the CLI should reproduce it."""
    # Arrange
    mono_path = FIXTURES_DIR / fixture_group / "mono" / "macro.mac"
    unfolded_dir = tmp_path / "unfolded"
    folded_dir = tmp_path / "folded"

    # Act
    unfold_exit_code = cli.main(
        [
            "--unfold",
            "--input-mono-macro-file",
            str(mono_path),
            "--output-dir",
            str(unfolded_dir),
        ]
    )
    fold_exit_code = cli.main(
        [
            "--fold",
            "--input-macros-dir",
            str(unfolded_dir),
            "--output-dir",
            str(folded_dir),
            "--title",
            "macro",
        ]
    )

    # Assert
    assert unfold_exit_code == 0
    assert fold_exit_code == 0
    assert (folded_dir / "macro.mac").read_bytes() == mono_path.read_bytes()
