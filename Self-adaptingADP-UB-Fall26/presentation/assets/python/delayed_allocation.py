"""Solve the tutorial's two-period display LP with SciPy/HiGHS.

Build marginal state/action flows and coordinate them with distributions over
feasible whole displays. This is the same teaching instance as slides 12–22.

Key Components:
    - solve_display_lp: Assemble and solve the restricted delayed-allocation LP.

Usage Example:
    result = solve_display_lp(costs=[0, 0, 8], add_backpack_tent=True)

Notes:
    - Runs unchanged in local Python or Pyodide with NumPy and SciPy loaded.
    - Costs are additional dollars per featured product per period.
    - The LP objective is distinct from the evaluated state-independent policy.
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from scipy.optimize import linprog


def solve_display_lp(
    costs: Sequence[float] = (0, 0, 0), *, add_backpack_tent: bool = True
) -> dict[str, Any]:
    """Return optimized display weights, net LP profit, and policy profit.

    Args:
        costs: Nonnegative finite display costs, in backpack/cooler/tent order.
        add_backpack_tent: Include the display found during refinement.

    Returns:
        A JSON-compatible solution. Policy profit exactly evaluates independent
        whole-display draws from each period's weights, ignoring observed states.

    Raises:
        ValueError: Invalid cost vector or support flag.
        RuntimeError: The LP fails to solve to optimality or has large residuals.
    """
    costs = np.asarray(costs, dtype=float)
    if costs.shape != (3,) or not np.all(np.isfinite(costs)) or np.any(costs < 0):
        raise ValueError("Use three finite, nonnegative costs: backpack, cooler, tent.")
    if not isinstance(add_backpack_tent, bool):
        raise ValueError("add_backpack_tent must be True or False.")

    # u = 0: unknown, 1: known low, 2: known high. b = 1 means feature.
    profits = np.array([[6, 2, 10], [8, 4, 12], [12, 0, 24]], dtype=float)
    actions = [(0, 0, 0), (1, 1, 0), (0, 0, 1)]
    if add_backpack_tent:
        actions.append((1, 0, 1))
    names = ["Feature nothing", "Backpack + cooler", "Tent only", "Backpack + tent"]
    keys = [(t, j, u, b) for t in range(2) for j in range(3)
            for u in (range(1) if t == 0 else range(3)) for b in (0, 1)]
    x = {key: i for i, key in enumerate(keys)}
    mu = {(t, k): len(x) + t * len(actions) + k
          for t in range(2) for k in range(len(actions))}
    size = len(x) + len(mu)
    reward = np.zeros(size)
    for (t, j, u, b), i in x.items():
        reward[i] = b * (profits[j, u] - costs[j])

    rows, rhs = [], []

    def equality(coefficients: dict[int, float], value: float) -> None:
        """Append one dense equality row for this small educational model."""
        row = np.zeros(size)
        for i, coefficient in coefficients.items():
            row[i] = coefficient
        rows.append(row)
        rhs.append(value)

    for j in range(3):
        # Initially unknown with probability one.
        equality({x[0, j, 0, b]: 1 for b in (0, 1)}, 1)
        # Not featured -> unknown; featured -> low/high with probability 1/2.
        for u in range(3):
            balance = {x[1, j, u, b]: 1 for b in (0, 1)}
            balance[x[0, j, 0, int(u != 0)]] = -1 if u == 0 else -0.5
            equality(balance, 0)

    for t in range(2):
        equality({mu[t, k]: 1 for k in range(len(actions))}, 1)
        for j in range(3):
            for b in (0, 1):
                # Link a product's marginal action probability to whole displays.
                link = {x[t, j, u, b]: 1 for u in (range(1) if t == 0 else range(3))}
                link.update({mu[t, k]: -1 for k, a in enumerate(actions) if a[j] == b})
                equality(link, 0)

    matrix, target = np.array(rows), np.array(rhs)
    # linprog minimizes: negate profit. Every variable is nonnegative.
    solution = linprog(-reward, A_eq=matrix, b_eq=target, bounds=(0, None), method="highs")
    if not solution.success:
        raise RuntimeError(f"LP did not solve: {solution.message}")
    residual = float(np.max(np.abs(matrix @ solution.x - target)))
    if residual > 1e-7 or np.min(solution.x) < -1e-7:
        raise RuntimeError("Solver returned an inaccurate solution.")
    weights = [[{"name": names[k], "action": list(a),
                 "probability": max(0., float(solution.x[mu[t, k]]))}
                for k, a in enumerate(actions)] for t in range(2)]
    # Unconditional type probabilities remain 1/2. This policy ignores learning.
    policy_profit = sum(row["probability"] * float(np.dot(row["action"], profits[:, 0] - costs))
                        for period in weights for row in period)
    return {"objective": float(-solution.fun), "policy_profit": policy_profit,
            "weights": weights, "costs": costs.tolist(), "residual": residual,
            "status": "Optimal", "variables": size, "constraints": len(rows)}
