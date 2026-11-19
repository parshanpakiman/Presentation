"""Verify every audience branch, policy evaluation, and pricing certificate."""
import importlib.util
from itertools import product
from pathlib import Path
import sys

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location('audience_choice', Path(__file__).resolve().parents[1] / 'scripts/prepare_audience_choice.py')
MODEL = importlib.util.module_from_spec(SPEC)
previous = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    SPEC.loader.exec_module(MODEL)
finally:
    sys.dont_write_bytecode = previous


@pytest.fixture(scope='module')
def states():
    return MODEL.prepare()['states']


def enumerate_policy(weights):
    """Independent joint-state enumeration, not the generator's expectation shortcut."""
    result = 0.
    for a0, w0 in zip(MODEL.ACTIONS, weights[0]):
        result += w0 * float(MODEL.INITIAL_REWARDS @ a0)
        for state in product((0, 1), repeat=3):
            mass = w0
            for j in range(3):
                p = a0[j] * MODEL.TRANSITION_PROBABILITIES[j]
                mass *= p if state[j] else 1 - p
            rewards = np.where(state, MODEL.CHANGED_REWARDS, MODEL.INITIAL_REWARDS)
            for a1, w1 in zip(MODEL.ACTIONS, weights[1]):
                result += mass * w1 * float(rewards @ a1)
    return result


def test_tutorial_and_initial_choices(states):
    assert MODEL.exact_mdp_value() == pytest.approx(49)
    for key, value in [('0-0', 0), ('2-8', 23.5), ('15-15', 49),
                       ('1-1', 22.5), ('2-2', 49), ('4-4', 11.5), ('8-8', 34)]:
        assert states[key]['objective'] == pytest.approx(value)


def test_all_256_policies_and_models(states):
    assert len(states) == 256
    for key, row in states.items():
        masks = [int(s) for s in key.split('-')]
        assert row['residual'] < 1e-8
        assert row['policy'] == pytest.approx(enumerate_policy(row['weights']))
        assert row['policy'] <= row['objective'] + 1e-8
        assert row['objective'] <= 49 + 1e-8
        assert row['variables'] == 18 + sum(len(MODEL.support(mask)) for mask in masks)
        for t, weights in enumerate(row['weights']):
            assert sum(weights) == pytest.approx(1)
            for a, weight in enumerate(weights):
                if weight > 1e-8:
                    assert a in MODEL.support(masks[t])
                    assert np.all(MODEL.RESOURCES @ MODEL.ACTIONS[a] <= MODEL.CAPACITIES)
                    assert abs(row['pricing'][t]['scores'][a]) < 1e-7


def test_every_addition_and_exact_pricing(states):
    for key, row in states.items():
        masks = [int(s) for s in key.split('-')]
        scores = []
        for t in range(2):
            for a in range(1, 5):
                if a in MODEL.support(masks[t]):
                    continue
                after = masks.copy()
                after[t] |= 1 << (a - 1)
                gain = states['-'.join(map(str, after))]['objective'] - row['objective']
                assert gain >= -1e-8
                score = row['pricing'][t]['scores'][a]
                scores.append(score)
                if score <= 1e-8:
                    assert gain == pytest.approx(0)
        if max(scores, default=0) <= 1e-8:
            assert row['objective'] == pytest.approx(states['15-15']['objective'])
