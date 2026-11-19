"""Prepare the outdoor-display knapsack example for the tutorial slides.

Build a two-period weakly coupled Markov decision process, solve its restricted
delayed-allocation linear programs, and enumerate pricing candidates. Export
validated solutions for static browser replay; no solver runs in the audience UI.

Key Components:
    - build_example: Define product demand learning and the display-space budget.
    - prepare: Validate the LP/refinement trace and export policy choices.
    - main: Write assets/data/assortment.js.

Usage Example:
    conda run -n informstutorial python scripts/prepare_assortment.py

Notes:
    - Rewards are expected incremental profit in dollars; display capacity is 8.
    - Displaying a product reveals its persistent low/high demand type exactly.
    - This teaching instance is distinct from the manuscript's resource example.
    - Requires the supplied research implementation and Gurobi during authoring.
"""
from __future__ import annotations

import json
from itertools import product
from pathlib import Path
from typing import Any

import gurobipy as gp
import numpy as np

from prepare_data import (
    DelayedAllocationModel, build_component, build_linking_constraints,
    build_wmdp,
)

ROOT = Path(__file__).resolve().parents[1]
NAMES = ["Backpack", "Cooler", "Tent"]
LOW = [2., 4., 0.]
HIGH = [10., 12., 24.]
SPACE = [2, 3, 6]
CAPACITY = 8
INITIAL = [(0, 0, 0), (1, 1, 0), (0, 0, 1)]


def build_example() -> Any:
    """Build independent demand-information transitions under a knapsack budget."""
    components = []
    for j, (low, high) in enumerate(zip(LOW, HIGH)):
        prior = (low + high) / 2
        rewards = [[("unknown", {0: 0., 1: prior})],
                   [(s, {0: 0., 1: r}) for s, r in [("unknown", prior), ("low", low), ("high", high)]],
                   [(s, {0: 0., 1: 0.}) for s in ["unknown", "low", "high"]]]
        transitions = [{("unknown", 0, "unknown"): 1., ("unknown", 1, "low"): .5,
                        ("unknown", 1, "high"): .5},
                       {(s, a, s): 1. for s in ["unknown", "low", "high"] for a in [0, 1]}]
        components.append(build_component(component=j, actions=[0, 1],
                          state_data_by_period=rewards, transitions_by_period=transitions))
    links = build_linking_constraints(action_sets=[[0, 1]] * 3,
        constraint_coefficients=[{(j, 1): float(w) for j, w in enumerate(SPACE)}],
        rhs_values=[float(CAPACITY)])
    return build_wmdp(components=components, linking_constraints=links)


def _bellman(mdp: Any, actions: list[tuple[int, ...]]) -> float:
    """Evaluate the exact two-period optimal profit by state enumeration."""
    start = mdp.generate_states(0)[0]
    values = []
    for action in actions:
        value = sum(s.reward[action[j]] for j, s in enumerate(start))
        for state in mdp.generate_states(1):
            mass = np.prod([mdp.state_space.S[j].P[0].get(
                (start[j].label, action[j], state[j].label), 0.) for j in range(3)])
            value += mass * max(sum(s.reward[a[j]] for j, s in enumerate(state))
                                for a in actions)
        values.append(float(value))
    return max(values)


def _randomized_value(mdp: Any, weights: list) -> float:
    """Evaluate independent whole-assortment draws from period-level LP weights."""
    distribution = {tuple(mdp.generate_states(0)[0]): 1.}
    value = 0.
    for t in range(2):
        following = {}
        for state, mass in distribution.items():
            for action, weight in weights[t]:
                value += mass * weight * sum(s.reward[action[j]] for j, s in enumerate(state))
                options = [[(n, mdp.state_space.S[j].P[t].get((s.label, action[j], n.label), 0.))
                            for n in mdp.state_space.S[j].states[t+1]] for j, s in enumerate(state)]
                for joint in product(*options):
                    nxt = tuple(pair[0] for pair in joint)
                    probability = mass * weight * float(np.prod([pair[1] for pair in joint]))
                    following[nxt] = following.get(nxt, 0.) + probability
        assert abs(sum(following.values()) - 1) < 1e-7
        distribution = following
    return value


def _snapshot(mdp: Any, model: Any, result: Any, actions: list) -> dict:
    """Export an LP solution, its pricing scores, and its extracted policy."""
    assert model.model.Status == gp.GRB.OPTIMAL
    assert max(abs(c.Slack) for c in model.model.getConstrs()) < 1e-7
    pricing = []
    for t in range(2):
        duals = [[result.duals.linking[t][j, a] for a in [0, 1]] for j in range(3)]
        scores = [sum(duals[j][a[j]] for j in range(3)) - result.duals.simplex[t]
                  for a in actions]
        pricing.append({"duals": duals, "simplex": result.duals.simplex[t], "scores": scores})
        assert abs(sum(w for _, w in result.positive_pi_actions[t]) - 1) < 1e-7
        assert all(sum(w*b for w, b in zip(SPACE, a)) <= CAPACITY for a in model.action_set[t])
    weights = [result.positive_pi_actions[t] for t in range(2)]
    return {"objective": result.objective_value, "policy_value": _randomized_value(mdp, weights),
            "support": [model.action_set[t].copy() for t in range(2)],
            "weights": weights,
            "flows": [[t, j, s, a, v] for (t, j, s, a), v in result.marginal_flows.items()],
            "pricing": pricing}


def prepare() -> dict:
    """Solve, price, validate, and export the teaching example.

    Returns:
        Model inputs and a trace ending at an exact pricing certificate.
    """
    mdp = build_example()
    actions = sorted(tuple(a) for a, _ in mdp.generate_feasible_actions())
    model = DelayedAllocationModel(mdp, initial_actions={t: INITIAL for t in range(mdp.T)})
    model.model.setParam("Threads", 1)
    trace = []
    for _ in range(8):
        row = _snapshot(mdp, model, model.optimize(), actions)
        trace.append(row)
        additions = []
        for t in range(2):
            scores = row["pricing"][t]["scores"]
            best = int(np.argmax(scores))
            if scores[best] > 1e-7:
                assert actions[best] not in model.action_set[t]
                additions.append({"period": t, "action": actions[best], "score": scores[best]})
                model.add_action(t, actions[best])
        row["additions"] = additions
        if not additions:
            break
    assert not trace[-1]["additions"], "Pricing has not converged."
    assert all(b["objective"] >= a["objective"] - 1e-7 for a, b in zip(trace, trace[1:]))
    exact = _bellman(mdp, actions)
    assert all(row["policy_value"] <= exact + 1e-7 for row in trace)
    assert trace[-1]["objective"] >= exact - 1e-7
    return {"products": NAMES, "low": LOW, "high": HIGH, "high_probability": .5,
            "prior": [(l+h)/2 for l, h in zip(LOW, HIGH)], "space": SPACE,
            "capacity": CAPACITY, "actions": actions, "trace": trace, "exact_mdp": exact,
            "source": "Teaching specialization; supplied delayedallocation.py; Gurobi "
                      + ".".join(map(str, gp.gurobi.version())),
            "policy": "At each period, sample one whole assortment according to its optimized weight mu_t, independently of observed states. Exact evaluation averages over both policy draws and demand types. Choosing a highest-weight assortment instead is a deterministic variant."}


def main() -> None:
    """Write the validated replay as a local JavaScript data asset."""
    data = prepare()
    destination = ROOT / "assets/data/assortment.js"
    destination.write_text("/* Generated by scripts/prepare_assortment.py. */\nwindow.ASSORTMENT_DATA = "
                           + json.dumps(data, separators=(",", ":"), allow_nan=False) + ";\n")
    print(json.dumps({"exact_mdp": data["exact_mdp"], "trace": [
        {key: row[key] for key in ["objective", "policy_value", "weights", "additions"]}
        for row in data["trace"]]}, indent=2))


if __name__ == "__main__":
    main()
