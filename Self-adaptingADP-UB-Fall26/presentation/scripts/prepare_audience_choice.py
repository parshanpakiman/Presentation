"""Solve every audience choice for the manuscript's Example 5.

The two-period delayed-allocation model follows tutorial equations (5a)-(5b).
Each period always includes the empty action and any subset of the four other
feasible actions. HiGHS solves all 256 support pairs during authoring; the browser
looks up the corresponding solved model, never substitutes a fixed trajectory.
"""
from __future__ import annotations

from itertools import product
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]
ACTIONS = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1)]
INITIAL_REWARDS = np.array([1., 22., .5])
CHANGED_REWARDS = np.array([42., 32., 11.])
TRANSITION_PROBABILITIES = np.array([.5, .5, 1.])
RESOURCES = np.array([[2, 10, 8], [3, 18, 15]])
CAPACITIES = np.array([14, 20])


def support(mask: int) -> list[int]:
    """Decode a period's represented actions, retaining the empty action."""
    if not isinstance(mask, int) or not 0 <= mask <= 15:
        raise ValueError('An action collection is an integer from 0 to 15.')
    return [0] + [a for a in range(1, 5) if mask & (1 << (a - 1))]


def evaluate_policy(weights: list[list[float]]) -> float:
    """Exactly evaluate independent whole-action draws from period LP weights."""
    value = 0.
    for i, a0 in enumerate(ACTIONS):
        # Offering a product in period 0 changes its state with the manuscript's
        # probability. An unoffered product remains in its initial state.
        expected_next_reward = INITIAL_REWARDS + np.array(a0) * TRANSITION_PROBABILITIES * (
            CHANGED_REWARDS - INITIAL_REWARDS)
        for k, a1 in enumerate(ACTIONS):
            value += weights[0][i] * weights[1][k] * (
                INITIAL_REWARDS @ a0 + expected_next_reward @ a1)
    return float(value)


def exact_mdp_value() -> float:
    """Independently enumerate joint successor states and optimal decisions."""
    outcomes = []
    for a0 in ACTIONS:
        continuation = 0.
        for state in product((0, 1), repeat=3):
            probabilities = np.array(a0) * TRANSITION_PROBABILITIES
            mass = np.prod([p if state[j] else 1 - p for j, p in enumerate(probabilities)])
            rewards = np.where(state, CHANGED_REWARDS, INITIAL_REWARDS)
            continuation += mass * max(float(rewards @ a) for a in ACTIONS)
        outcomes.append(float(INITIAL_REWARDS @ a0 + continuation))
    return max(outcomes)


def solve(masks: tuple[int, int]) -> dict:
    """Return a primal solution, exact policy evaluation, and pricing scores."""
    supports = [support(mask) for mask in masks]
    keys = [(t, j, s, b) for t in range(2) for j in range(3)
            for s in range(1 if t == 0 else 2) for b in (0, 1)]
    x = {key: i for i, key in enumerate(keys)}
    mu = {}
    for t in range(2):
        for a in supports[t]:
            mu[t, a] = len(x) + len(mu)
    size = len(x) + len(mu)
    rewards = np.zeros(size)
    for (t, j, s, b), i in x.items():
        rewards[i] = b * (CHANGED_REWARDS[j] if s else INITIAL_REWARDS[j])
    rows, targets = [], []

    def equality(coefficients: dict, target: float) -> int:
        row = np.zeros(size)
        for i, coefficient in coefficients.items():
            row[i] = coefficient
        rows.append(row)
        targets.append(target)
        return len(rows) - 1

    for j in range(3):
        equality({x[0, j, 0, b]: 1 for b in (0, 1)}, 1)
        for s in (0, 1):
            row = {x[1, j, s, b]: 1 for b in (0, 1)}
            for b in (0, 1):
                changed = b * TRANSITION_PROBABILITIES[j]
                row[x[0, j, 0, b]] = -(changed if s else 1 - changed)
            equality(row, 0)
    simplex_rows, linking_rows = {}, {}
    for t in range(2):
        simplex_rows[t] = equality({mu[t, a]: 1 for a in supports[t]}, 1)
        for j in range(3):
            for b in (0, 1):
                row = {x[t, j, s, b]: 1 for s in range(1 if t == 0 else 2)}
                row.update({mu[t, a]: -1 for a in supports[t] if ACTIONS[a][j] == b})
                linking_rows[t, j, b] = equality(row, 0)
    matrix, target = np.array(rows), np.array(targets)
    result = linprog(-rewards, A_eq=matrix, b_eq=target, bounds=(0, None), method='highs')
    if not result.success:
        raise RuntimeError(result.message)
    residual = float(np.max(np.abs(matrix @ result.x - target)))
    if residual > 1e-8 or result.x.min() < -1e-8:
        raise RuntimeError('Primal solution failed the residual check.')
    # Negate minimization multipliers to recover the max-profit convention.
    duals = -result.eqlin.marginals
    weights = [[float(max(0, result.x[mu[t, a]])) if a in supports[t] else 0.
                for a in range(5)] for t in range(2)]
    pricing = []
    for t in range(2):
        d = [[float(duals[linking_rows[t, j, b]]) for b in (0, 1)] for j in range(3)]
        xi = float(duals[simplex_rows[t]])
        scores = [float(sum(d[j][a[j]] for j in range(3)) - xi) for a in ACTIONS]
        pricing.append({'duals': d, 'simplex': xi, 'scores': scores})
    return {'objective': float(-result.fun), 'policy': evaluate_policy(weights),
            'weights': weights, 'pricing': pricing, 'variables': size,
            'constraints': len(rows), 'residual': residual}


def prepare() -> dict:
    states = {f'{m0}-{m1}': solve((m0, m1)) for m0, m1 in product(range(16), repeat=2)}
    # At the full-support optimum, reuse its optimal dual certificate. It is
    # also an optimal dual for any restricted model with the same objective:
    # deleting columns preserves dual feasibility and the RHS is unchanged.
    # This avoids presenting spurious positive scores from a degenerate dual
    # optimum after the audience has already attained the final LP objective.
    full = states['15-15']
    for row in states.values():
        if abs(row['objective'] - full['objective']) < 1e-8:
            row['pricing'] = full['pricing']
    assert abs(exact_mdp_value() - 49) < 1e-8
    # Published Example 5, with a product-2 action in period 0 and product-1+3
    # in period 1 after its first pricing step.
    assert abs(states['0-0']['objective']) < 1e-8
    assert abs(states['2-8']['objective'] - 23.5) < 1e-8
    assert abs(states['15-15']['objective'] - 49) < 1e-8
    return {'version': 1, 'source': 'Tutorial section 3.3, Example 5; equations (5a), (5b), and (6).',
            'actions': [list(a) for a in ACTIONS],
            'names': ['Offer nothing', 'Product 1 only', 'Product 2 only', 'Product 3 only', 'Products 1 and 3 together'],
            'resources': RESOURCES.tolist(), 'capacities': CAPACITIES.tolist(),
            'initialRewards': INITIAL_REWARDS.tolist(), 'changedRewards': CHANGED_REWARDS.tolist(),
            'transitionProbabilities': TRANSITION_PROBABILITIES.tolist(),
            'solver': 'SciPy / HiGHS',
            'dualSelection': 'At the full-support objective, use the full-support optimal dual certificate; it is valid for the restricted model as well.',
            'states': states}


if __name__ == '__main__':
    data = prepare()
    destination = ROOT / 'assets/demos/audience-choice-data.js'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text('/* Generated by scripts/prepare_audience_choice.py. */\n'
                           'window.AUDIENCE_CHOICE_DATA = '
                           + json.dumps(data, separators=(',', ':'), allow_nan=False) + ';\n')
    print(f'Validated and exported {len(data["states"])} solved action collections.')
