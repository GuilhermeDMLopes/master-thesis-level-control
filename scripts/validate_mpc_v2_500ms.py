from __future__ import annotations

import importlib.util
import json
import math
import sys
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "scripts" / "mpc_reference_controller.py"
MODEL_PATH = ROOT / "models" / "mpc" / "deadzone-hammerstein-v1.json"


def load_reference():
    spec = importlib.util.spec_from_file_location(
        "mpc_reference_controller_v2_analysis",
        REFERENCE,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load MPC reference controller")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ref = load_reference()


def v1_config():
    return ref.MPCConfig()


def v2_config():
    # 500 ms compute period.
    # 750 DAC / 500 ms preserves the original 1500 DAC/s move envelope.
    #
    # Stage weights are rescaled to preserve approximately the same
    # physical-horizon weighting with five times fewer prediction samples.
    return ref.MPCConfig(
        sample_time_s=0.5,
        setpoint_raw=450.0,
        minimum_dac=0.0,
        maximum_dac=12000.0,
        maximum_delta_dac=750.0,
        prediction_horizon_s=20.0,
        target_grid_step_dac=50.0,
        predicted_soft_level_raw=650.0,
        predicted_hard_level_raw=750.0,
        measured_hard_level_raw=800.0,
        tracking_weight=5.0,
        move_weight=0.00004,
        soft_level_weight=100.0,
        terminal_weight=10.0,
        # Bias adaptation remains deliberately conservative for commissioning.
        bias_adaptation_gain=0.01,
        maximum_bias_update_dac=5.0,
        maximum_abs_input_bias_dac=250.0,
    )


def gateway_limit(current: float, requested: float) -> float:
    delta = max(-150.0, min(150.0, requested - current))
    return max(0.0, min(12000.0, current + delta))


def simulate(
    *,
    controller_model,
    physical_model,
    config,
    duration_s: float = 60.0,
    plant_dt_s: float = 0.1,
):
    controller = ref.SafeMoveBlockedNMPC(
        controller_model,
        config,
    )

    y = controller_model.baseline_raw
    applied = 0.0
    requested = 0.0

    time_s = 0.0
    next_controller_s = 0.0

    max_level = y
    max_applied = applied
    first_deadzone_s = None
    tripped = False

    while time_s < duration_s - 1e-12:
        if time_s + 1e-12 >= next_controller_s:
            output = controller.step(
                measured_raw=y,
                applied_dac=applied,
                enable_request=True,
                external_healthy=True,
                reset_request=False,
                setpoint_raw=450.0,
            )

            if output.tripped:
                tripped = True
                break

            requested = output.command_dac
            next_controller_s += config.sample_time_s

        # Real project defense-in-depth boundary:
        # gateway applies at most 150 DAC per approximately 100 ms write.
        applied = gateway_limit(applied, requested)

        y = ref.plant_step(
            y,
            applied,
            physical_model,
            plant_dt_s,
        )

        max_level = max(max_level, y)
        max_applied = max(max_applied, applied)

        if first_deadzone_s is None and applied >= controller_model.deadzone_dac:
            first_deadzone_s = time_s

        time_s += plant_dt_s

    return {
        "tripped": tripped,
        "final_raw": y,
        "max_raw": max_level,
        "max_applied_dac": max_applied,
        "first_deadzone_s": first_deadzone_s,
        "input_bias_dac": controller.input_bias_estimate_dac,
    }


def main() -> int:
    model = ref.load_model(MODEL_PATH)

    v1 = v1_config()
    v2 = v2_config()

    v1_steps = round(v1.prediction_horizon_s / v1.sample_time_s)
    v2_steps = round(v2.prediction_horizon_s / v2.sample_time_s)

    probe_v1 = ref.SafeMoveBlockedNMPC(model, v1)
    probe_v2 = ref.SafeMoveBlockedNMPC(model, v2)

    v1_candidates = len(probe_v1._target_candidates)
    v2_candidates = len(probe_v2._target_candidates)

    a_v1 = math.exp(-v1.sample_time_s / model.tau_s)
    b_v1 = model.equilibrium_gain * (1.0 - a_v1)

    a_v2 = math.exp(-v2.sample_time_s / model.tau_s)
    b_v2 = model.equilibrium_gain * (1.0 - a_v2)

    print("MPC V2 500 ms OFFLINE TIMING CONTRACT")
    print("=====================================")
    print()
    print(f"Model tau: {model.tau_s:.6f} s")
    print(f"Model dead-zone: {model.deadzone_dac:.3f} DAC")
    print()
    print("V1")
    print(f"  sample time: {v1.sample_time_s:.3f} s")
    print(f"  max move: {v1.maximum_delta_dac:.1f} DAC/update")
    print(f"  move envelope: {v1.maximum_delta_dac / v1.sample_time_s:.1f} DAC/s")
    print(f"  prediction steps: {v1_steps}")
    print(f"  candidates: {v1_candidates}")
    print(f"  candidate prediction iterations: {v1_steps * v1_candidates}")
    print(f"  a: {a_v1:.15f}")
    print(f"  b: {b_v1:.15f}")
    print()
    print("V2 PROPOSAL")
    print(f"  sample time: {v2.sample_time_s:.3f} s")
    print(f"  max move: {v2.maximum_delta_dac:.1f} DAC/update")
    print(f"  move envelope: {v2.maximum_delta_dac / v2.sample_time_s:.1f} DAC/s")
    print(f"  prediction horizon: {v2.prediction_horizon_s:.1f} s")
    print(f"  prediction steps: {v2_steps}")
    print(f"  candidates: {v2_candidates}")
    print(f"  candidate prediction iterations: {v2_steps * v2_candidates}")
    print(f"  a: {a_v2:.15f}")
    print(f"  b: {b_v2:.15f}")
    print(
        "  prediction-iteration reduction: "
        f"{100.0 * (1.0 - (v2_steps * v2_candidates) / (v1_steps * v1_candidates)):.1f}%"
    )
    print()

    scenarios = {
        "nominal": model,
        "tau_fast_25pct": replace(model, tau_s=model.tau_s * 0.75),
        "tau_slow_35pct": replace(model, tau_s=model.tau_s * 1.35),
        "gain_high_20pct": replace(
            model,
            equilibrium_gain=model.equilibrium_gain * 1.20,
        ),
        "gain_low_20pct": replace(
            model,
            equilibrium_gain=model.equilibrium_gain * 0.80,
        ),
        "deadzone_minus_75": replace(
            model,
            deadzone_dac=model.deadzone_dac - 75.0,
        ),
        "deadzone_plus_75": replace(
            model,
            deadzone_dac=model.deadzone_dac + 75.0,
        ),
    }

    failures = []

    print("OFFLINE CLOSED-LOOP SCREEN")
    print("--------------------------")

    for name, physical_model in scenarios.items():
        result = simulate(
            controller_model=model,
            physical_model=physical_model,
            config=v2,
        )

        deadzone_text = (
            "none"
            if result["first_deadzone_s"] is None
            else f"{result['first_deadzone_s']:.1f}s"
        )

        passed = (
            not result["tripped"]
            and result["max_applied_dac"] <= 12000.0 + 1e-9
            and result["max_raw"] < 650.0
            and 380.0 <= result["final_raw"] <= 520.0
            and result["first_deadzone_s"] is not None
            and result["first_deadzone_s"] <= 12.0
        )

        print(
            f"{name:22s} "
            f"pass={passed} | "
            f"final={result['final_raw']:.2f} | "
            f"max={result['max_raw']:.2f} | "
            f"maxDAC={result['max_applied_dac']:.1f} | "
            f"deadzone={deadzone_text} | "
            f"bias={result['input_bias_dac']:.2f}"
        )

        if not passed:
            failures.append((name, result))

    print()

    if failures:
        print("MPC V2 500 ms OFFLINE CONTRACT: FAILED")
        for name, result in failures:
            print(f"  FAIL: {name}: {result}")
        return 1

    print("MPC V2 500 ms OFFLINE CONTRACT: PASSED")
    print("REAL MPC FULL OPERATION AUTHORIZED: NO")
    print("NEXT: additive 4diac/FORTE MPC V2 implementation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
