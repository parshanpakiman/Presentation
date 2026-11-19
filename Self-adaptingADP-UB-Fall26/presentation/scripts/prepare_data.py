"""Prepare reproducible, static numerical assets for the browser presentation.

Export a small delayed-allocation run using the supplied research implementation,
and inventory expectation tables using deterministic quadrature. Python and Gurobi
run only during authoring; the generated JavaScript is served as static data.

Key Components:
    - inventory_table: Compute expected costs and next-state moments.
    - allocation_trace: Solve and price the manuscript's three-product example.
    - main: Write assets/data/prepared.js with settings and provenance.

Usage Example:
    conda run -n informstutorial python scripts/prepare_data.py

Notes:
    - Run from presentation or any directory; paths are resolved from this file.
    - Requires the sibling research code and the informstutorial environment.
    - Grid minima are numerical illustrations, not continuous certificates.
"""
from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import truncnorm

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT.parent / "code/Code/weakly-coupled-mdp"
sys.path.insert(0, str(RESEARCH))
from wmdp import build_component, build_linking_constraints, build_wmdp
from delayedallocation import DelayedAllocationModel, LinkingIPSeparation


def inventory_table() -> dict[str, Any]:
    """Compute a state/action grid with 256-node Gauss–Legendre expectations."""
    nodes, weights = np.polynomial.legendre.leggauss(256)
    demand = (nodes + 1) * 5
    weights = weights * 5 * truncnorm.pdf(demand, -6 / 3.5, 4 / 3.5, loc=6, scale=3.5)
    assert abs(weights.sum() - 1) < 1e-10
    states, actions = np.linspace(-4, 12, 81), np.linspace(0, 6, 41)
    rows = []
    for state in states:
        for action in actions:
            raw = state + action - demand
            nxt = np.clip(raw, -4, 12)
            cost = 20 * action + np.maximum(nxt, 0) + 25 * np.maximum(-nxt, 0)
            cost += 5 * np.maximum(raw - 12, 0) + 3000 * np.maximum(-4 - raw, 0)
            rows.append([float(cost @ weights), float(nxt @ weights), float((nxt**2) @ weights)])
    return {"states": states.tolist(), "actions": actions.tolist(), "moments": rows,
            "gamma": .95, "quadrature_nodes": 256,
            "source": "Tutorial section 4, inventory example; truncated Normal(6,3.5²) on [0,10]."}


def build_example() -> Any:
    """Build the two-decision-period manuscript example with a terminal period."""
    components = []
    for j, (r0, r1, prob) in enumerate(zip([1, 22, .5], [42, 32, 11], [.5, .5, 1])):
        rewards = [[("s0", {0: 0., 1: r0})],
                   [("s0", {0: 0., 1: r0}), ("s1", {0: 0., 1: r1})],
                   [("s0", {0: 0., 1: 0.}), ("s1", {0: 0., 1: 0.})]]
        transitions = [{("s0", 0, "s0"): 1., ("s0", 1, "s0"): 1-prob,
                        ("s0", 1, "s1"): prob},
                       {(s, a, s): 1. for s in ["s0", "s1"] for a in [0, 1]}]
        components.append(build_component(component=j, actions=[0, 1],
                          state_data_by_period=rewards, transitions_by_period=transitions))
    links = build_linking_constraints(action_sets=[[0, 1]] * 3,
        constraint_coefficients=[{(j, 1): c for j, c in enumerate(cs)}
                                 for cs in [[2, 10, 8], [3, 18, 15]]], rhs_values=[14., 20.])
    return build_wmdp(components=components, linking_constraints=links)


def policy_value(mdp: Any, policy: Any) -> float:
    """Evaluate a deterministic policy exactly over the two decision periods."""
    distribution = {tuple(mdp.generate_states(0)[0]): 1.}
    value = 0.
    for t in [0, 1]:
        following: dict[Any, float] = {}
        for state, mass in distribution.items():
            action = policy.get_action(period=t, state=list(state))
            value += mass * sum(s.reward[action[j]] for j, s in enumerate(state))
            options = [[(n, mdp.state_space.S[j].P[t].get((s.label, action[j], n.label), 0.))
                        for n in mdp.state_space.S[j].states[t+1]] for j, s in enumerate(state)]
            for joint in product(*options):
                nxt = tuple(pair[0] for pair in joint)
                probability = mass * float(np.prod([pair[1] for pair in joint]))
                following[nxt] = following.get(nxt, 0.) + probability
        distribution = following
    return value


def allocation_trace() -> dict[str, Any]:
    """Export real LP solutions, dual prices, and exact enumerated pricing scores."""
    mdp = build_example()
    model = DelayedAllocationModel(mdp, initial_actions={t: [(0, 0, 0)] for t in range(mdp.T)})
    model.model.setParam("OutputFlag", 0)
    result = model.optimize()
    actions = [tuple(a) for a, _ in mdp.generate_feasible_actions()]
    trace = []
    for iteration in range(4):
        pricing = []
        for t in [0, 1]:
            scores = [sum(result.duals.linking[t][j, a[j]] for j in range(3))
                      - result.duals.simplex[t] for a in actions]
            pricing.append({"period": t, "scores": scores,
                            "duals": [[result.duals.linking[t][j, a] for a in [0, 1]] for j in range(3)],
                            "simplex": result.duals.simplex[t]})
        trace.append({"iteration": iteration, "objective": result.objective_value,
                      "policy": policy_value(mdp, result.policy), "pricing": pricing,
                      "support": [list(model.action_set[t]) for t in [0, 1]],
                      "weights": [result.positive_pi_actions[t] for t in [0, 1]]})
        if iteration < 3:
            result = model.refine(result.duals, LinkingIPSeparation(), verbose=False)
    assert np.allclose([r["objective"] for r in trace], [0, 23.5, 49, 49])
    assert all(max(p["scores"]) < 1e-7 for p in trace[-1]["pricing"])
    return {"actions": actions, "trace": trace, "source": "Supplied text_example.ipynb instance; regenerated with research delayedallocation.py.",
            "evaluation": "Exact state enumeration for the implementation's deterministic vertex policy.",
            "solver": "Gurobi 13.0.1, default tolerances", "periods": 2}


def main() -> None:
    """Write self-contained browser data and print validation results."""
    data = {"inventory": inventory_table(), "allocation": allocation_trace()}
    path = ROOT / "assets/data/prepared.js"
    path.write_text("/* Authoring output; regenerate with scripts/prepare_data.py. */\nwindow.TUTORIAL_DATA = "
                    + json.dumps(data, separators=(",", ":"), allow_nan=False) + ";\n")
    print(f"Validated inventory expectations and allocation trace; wrote {path.name}.")


if __name__ == "__main__":
    main()
