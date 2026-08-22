from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "mpc_v3f_action_candidates.py"

spec = importlib.util.spec_from_file_location("mpc_v3f_action_candidates", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def test_contract_constants():
    assert mod.DAC_MIN == 0.0
    assert mod.DAC_MAX == 12000.0
    assert mod.MAX_MOVE == 750.0
    assert mod.CANDIDATE_COUNT == 13
    assert len(mod.RELATIVE_MOVES) == 13
    assert mod.RELATIVE_MOVES[0] == -750.0
    assert mod.RELATIVE_MOVES[6] == 0.0
    assert mod.RELATIVE_MOVES[-1] == 750.0


def test_interior_has_exactly_13_unique_candidates():
    c = mod.connected_candidates(6000.0)
    assert len(c) == 13
    assert len(set(c)) == 13


def test_every_candidate_move_respects_limit():
    for applied in (0.0, 125.0, 750.0, 6000.0, 11500.0, 11850.0, 12000.0):
        assert mod.all_moves_within_limit(applied)


def test_high_dac_region_has_downward_actions():
    for applied in (11500.0, 11845.626677302696, 11850.0, 12000.0):
        assert mod.has_downward_action(applied)
        assert min(mod.connected_candidates(applied)) <= max(0.0, applied - 750.0)


def test_high_dac_region_can_reach_zero():
    path = mod.descent_path_to_zero(11850.0)
    assert path[0] == 11850.0
    assert path[-1] == 0.0
    assert all(b < a for a, b in zip(path, path[1:]))
    assert all(abs(b - a) <= 750.0 + 1e-12 for a, b in zip(path, path[1:]))


def test_equilibrium_candidate_can_reach_zero():
    path = mod.descent_path_to_zero(11845.626677302696)
    assert path[-1] == 0.0


def test_zero_can_ramp_up():
    assert mod.has_upward_action(0.0)
    assert max(mod.connected_candidates(0.0)) == 750.0


def test_bounds_are_never_violated():
    for applied in (-100.0, 0.0, 11900.0, 12000.0, 13000.0):
        c = mod.connected_candidates(applied)
        assert min(c) >= 0.0
        assert max(c) <= 12000.0


def test_candidate_set_contains_hold_action():
    for applied in (0.0, 227.0, 6000.0, 11850.0, 12000.0):
        current = mod.clamp_dac(applied)
        assert any(abs(c - current) < 1e-12 for c in mod.connected_candidates(applied))
