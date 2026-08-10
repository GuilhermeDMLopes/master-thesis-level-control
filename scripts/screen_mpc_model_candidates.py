from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path("results/mpc/pi-baseline-identification")


def static_gain(model: dict[str, Any]) -> float | None:
    a = [float(v) for v in model.get("a", [])]
    b = [float(v) for v in model.get("b", [])]

    denominator = 1.0 - sum(a)
    numerator = sum(b)

    if abs(denominator) < 1e-12:
        return None

    gain = numerator / denominator

    if not math.isfinite(gain):
        return None

    return gain


def homogeneous_response_is_stable(
    a: list[float],
    *,
    steps: int = 600,
    growth_limit: float = 1e6,
    tail_limit: float = 1e-3,
) -> bool:
    """
    Standard-library-only stability screen.

    The AR recurrence is:
        y[k] = a1*y[k-1] + a2*y[k-2] + ...

    Each independent initial-state basis is propagated. For a stable
    discrete-time recurrence, all such homogeneous responses must decay.
    """
    order = len(a)

    if order == 0:
        return False

    for basis in range(order):
        history = [0.0] * order
        history[basis] = 1.0

        max_abs = max(abs(value) for value in history)

        for _ in range(steps):
            next_value = sum(
                coefficient * history[-lag]
                for lag, coefficient in enumerate(a, start=1)
            )

            if not math.isfinite(next_value):
                return False

            max_abs = max(max_abs, abs(next_value))

            if max_abs > growth_limit:
                return False

            history.append(next_value)
            history = history[-order:]

        if max(abs(value) for value in history) > tail_limit:
            return False

    return True


def metrics(model: dict[str, Any]) -> dict[str, float]:
    values = model.get("metrics", {})
    return {
        "train_rmse": float(
            values.get("train_one_step_rmse_raw", float("inf"))
        ),
        "validation_one_step_rmse": float(
            values.get("validation_one_step_rmse_raw", float("inf"))
        ),
        "validation_free_run_rmse": float(
            values.get("validation_free_run_rmse_raw", float("inf"))
        ),
        "validation_fit_percent": float(
            values.get("validation_free_run_fit_percent", float("-inf"))
        ),
        "validation_bias": float(
            values.get("validation_free_run_bias_raw", float("inf"))
        ),
        "validation_max_abs_error": float(
            values.get("validation_max_abs_error_raw", float("inf"))
        ),
    }


def evaluate(model: dict[str, Any], rank: int) -> dict[str, Any]:
    a = [float(v) for v in model.get("a", [])]
    b = [float(v) for v in model.get("b", [])]
    gain = static_gain(model)
    stable = homogeneous_response_is_stable(a)
    model_metrics = metrics(model)

    finite_metrics = all(
        math.isfinite(value)
        for key, value in model_metrics.items()
        if key != "validation_fit_percent"
    ) and math.isfinite(model_metrics["validation_fit_percent"])

    positive_gain = gain is not None and gain > 0.0
    positive_fit = model_metrics["validation_fit_percent"] > 0.0

    physical_pass = (
        stable
        and positive_gain
        and finite_metrics
        and positive_fit
    )

    return {
        "source_rank": rank,
        "na": int(model["na"]),
        "nb": int(model["nb"]),
        "input_delay_samples": int(model["input_delay_samples"]),
        "input_delay_s": float(model["input_delay_s"]),
        "a": a,
        "b": b,
        "static_gain_raw_per_dac": gain,
        "stable": stable,
        "positive_static_gain": positive_gain,
        "positive_validation_fit": positive_fit,
        "physical_screen_pass": physical_pass,
        **model_metrics,
        "model": model,
    }


def print_candidate(prefix: str, item: dict[str, Any]) -> None:
    gain = item["static_gain_raw_per_dac"]
    gain_text = "undefined" if gain is None else f"{gain:.9f}"

    print(prefix)
    print(f"  source rank: {item['source_rank']}")
    print(f"  na / nb: {item['na']} / {item['nb']}")
    print(
        "  input delay: "
        f"{item['input_delay_samples']} samples "
        f"({item['input_delay_s']:.6f} s)"
    )
    print(f"  stable AR dynamics: {item['stable']}")
    print(f"  static gain raw/DAC: {gain_text}")
    print(
        "  validation free-run RMSE raw: "
        f"{item['validation_free_run_rmse']:.6f}"
    )
    print(
        "  validation free-run fit percent: "
        f"{item['validation_fit_percent']:.3f}"
    )
    print(
        "  validation max abs error raw: "
        f"{item['validation_max_abs_error']:.6f}"
    )
    print(
        "  physical screen pass: "
        f"{item['physical_screen_pass']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Offline physical-consistency screening of ARX candidates "
            "identified from the real PI baseline."
        )
    )
    parser.add_argument(
        "--candidate-models",
        type=Path,
        default=DEFAULT_ROOT / "candidate-models.json",
    )
    parser.add_argument(
        "--selected-model",
        type=Path,
        default=DEFAULT_ROOT / "selected-model.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_ROOT / "physical-screening.json",
    )
    args = parser.parse_args()

    print("MPC MODEL PHYSICAL-CONSISTENCY SCREEN")
    print("=====================================")
    print("NETWORK ACCESS: NO")
    print("ACTUATOR WRITES: NO")
    print()

    selected = json.loads(
        args.selected_model.read_text(encoding="utf-8")
    )
    candidates = json.loads(
        args.candidate_models.read_text(encoding="utf-8")
    )

    selected_eval = evaluate(selected, 0)

    print_candidate("CURRENT SELECTED MODEL", selected_eval)
    print()

    evaluated = [
        evaluate(model, rank)
        for rank, model in enumerate(candidates, start=1)
    ]

    physically_valid = [
        item
        for item in evaluated
        if item["physical_screen_pass"]
    ]

    physically_valid.sort(
        key=lambda item: (
            item["validation_free_run_rmse"],
            item["validation_one_step_rmse"],
            item["na"] + item["nb"],
            item["input_delay_samples"],
        )
    )

    print(f"Candidates evaluated: {len(evaluated)}")
    print(
        "Physically consistent candidates "
        f"(stable + positive DC gain + positive validation fit): "
        f"{len(physically_valid)}"
    )
    print()

    result: dict[str, Any] = {
        "current_selected_model": {
            key: value
            for key, value in selected_eval.items()
            if key != "model"
        },
        "criteria": {
            "stable_ar_dynamics": True,
            "positive_static_gain": True,
            "positive_validation_free_run_fit_percent": True,
            "finite_validation_metrics": True,
        },
        "physically_consistent_candidate_count": len(
            physically_valid
        ),
        "physically_consistent_candidates": [
            {
                key: value
                for key, value in item.items()
                if key != "model"
            }
            for item in physically_valid
        ],
    }

    if physically_valid:
        best = physically_valid[0]
        result["recommended_candidate"] = best["model"]

        print_candidate(
            "BEST PHYSICALLY CONSISTENT CANDIDATE",
            best,
        )
        print()
        print(
            "DECISION: CANDIDATE AVAILABLE FOR INDEPENDENT "
            "OFFLINE VALIDATION"
        )
        exit_code = 0
    else:
        result["recommended_candidate"] = None

        print(
            "DECISION: NO PHYSICALLY CONSISTENT ARX CANDIDATE "
            "FOUND IN THE CURRENT LEADERBOARD"
        )
        print(
            "NEXT: do not authorize MPC; change the identification "
            "method rather than forcing the closed-loop least-squares model."
        )
        exit_code = 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"Report JSON: {args.output}")
    print("REAL MPC AUTHORIZED: NO")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
