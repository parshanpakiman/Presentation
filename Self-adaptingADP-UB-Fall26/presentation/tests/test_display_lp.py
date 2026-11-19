"""Validate the browser LP helper against independently prepared teaching cases.

Key Components:
    - test_reference_cases: Check Gurobi reference objectives and policy profits.
    - test_changed_costs: Check an expensive tent and the zero-display optimum.
    - test_invalid_costs: Reject invalid educational inputs explicitly.

Usage Example:
    conda run -n informstutorial pytest tests/test_display_lp.py

Notes:
    Uses SciPy locally; check_browser.py executes the same file under Pyodide.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

SPEC = importlib.util.spec_from_file_location(
    "display_lp", Path(__file__).resolve().parents[1] / "assets/python/delayed_allocation.py")
MODEL = importlib.util.module_from_spec(SPEC)
_write_bytecode = sys.dont_write_bytecode
try:
    # Keep native .pyc files out of the browser's published Python assets.
    sys.dont_write_bytecode = True
    SPEC.loader.exec_module(MODEL)
finally:
    sys.dont_write_bytecode = _write_bytecode


@pytest.mark.parametrize("expanded,objective,policy", [(False, 31.5, 26.5), (True, 40, 34)])
def test_reference_cases(expanded: bool, objective: float, policy: float) -> None:
    """Match the independently generated Gurobi teaching instance."""
    result = MODEL.solve_display_lp(add_backpack_tent=expanded)
    assert result["objective"] == pytest.approx(objective)
    assert result["policy_profit"] == pytest.approx(policy)
    assert result["residual"] < 1e-8
    for period in result["weights"]:
        assert sum(row["probability"] for row in period) == pytest.approx(1)
        assert all(sum(w * a for w, a in zip((2, 3, 6), row["action"])) <= 8 for row in period)


def test_changed_costs() -> None:
    """Make the tent dominated, then make every nonempty display unprofitable."""
    for expanded in (False, True):
        result = MODEL.solve_display_lp([0, 0, 25], add_backpack_tent=expanded)
        assert result["objective"] == pytest.approx(28)
        assert result["policy_profit"] == pytest.approx(28)
        assert all(row["action"] == [1, 1, 0] for period in result["weights"]
                   for row in period if row["probability"] > 1e-8)
    result = MODEL.solve_display_lp([100, 100, 100])
    assert result["objective"] == pytest.approx(0)
    assert result["policy_profit"] == pytest.approx(0)


@pytest.mark.parametrize("costs", [[-1, 0, 0], [0, 0], [0, 0, float("nan")], [0, 0, float("inf")]])
def test_invalid_costs(costs: list[float]) -> None:
    """Reject missing or invalid costs before passing them to the solver."""
    with pytest.raises(ValueError, match="finite, nonnegative"):
        MODEL.solve_display_lp(costs)
