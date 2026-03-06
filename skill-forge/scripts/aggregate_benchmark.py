#!/usr/bin/env python3
"""
Purpose: Aggregate eval results into a benchmark report with pass rate, time, and tokens.
Input: Path to an iteration workspace directory containing eval-*/with_skill/ and eval-*/baseline/
Output: benchmark.json and benchmark.md with aggregated metrics
Usage: python scripts/aggregate_benchmark.py /path/to/iteration-N --skill-name my-skill

Reads grading.json and timing.json from each eval run directory and produces:
- Per-eval pass rate, avg tokens, avg duration
- Overall summary with improvement ratios
- Variance analysis across trials
- Comparison with previous iteration (if --previous provided)
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any] | None:
    """Safely load a JSON file, returning None on failure."""
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def discover_eval_dirs(iteration_path: Path) -> list[Path]:
    """Find all eval-* directories in an iteration workspace."""
    eval_dirs: list[Path] = []
    for entry in sorted(iteration_path.iterdir()):
        if entry.is_dir() and re.match(r'^eval-\d+$', entry.name):
            eval_dirs.append(entry)
    return eval_dirs


def collect_run_data(run_path: Path) -> dict[str, Any] | None:
    """Collect grading and timing data from a run directory."""
    if not run_path.is_dir():
        return None

    grading = load_json(run_path / "grading.json")
    timing = load_json(run_path / "timing.json")

    if not grading:
        return None

    result: dict[str, Any] = {
        "pass_rate": grading.get("pass_rate", 0.0),
        "assertions": grading.get("assertions", []),
    }

    if timing:
        result["total_tokens"] = timing.get("total_tokens", 0)
        result["duration_seconds"] = timing.get("total_duration_seconds", 0.0)
    else:
        result["total_tokens"] = 0
        result["duration_seconds"] = 0.0

    return result


def collect_trial_data(eval_dir: Path, run_type: str) -> list[dict[str, Any]]:
    """Collect data across multiple trials for a run type."""
    trials: list[dict[str, Any]] = []

    # Check for single run (with_skill/ or baseline/)
    single_run = eval_dir / run_type
    if single_run.is_dir():
        data = collect_run_data(single_run)
        if data:
            trials.append(data)

    # Check for numbered trials (with_skill_0/, with_skill_1/, etc.)
    for i in range(20):
        trial_dir = eval_dir / f"{run_type}_{i}"
        if trial_dir.is_dir():
            data = collect_run_data(trial_dir)
            if data:
                trials.append(data)

    return trials


def calculate_stats(values: list[float]) -> dict[str, float]:
    """Calculate mean and standard deviation for a list of values."""
    if not values:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}

    n = len(values)
    mean = sum(values) / n
    if n > 1:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        std = variance ** 0.5
    else:
        std = 0.0

    return {
        "mean": round(mean, 4),
        "std": round(std, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


def aggregate_benchmark(
    iteration_path: str,
    skill_name: str,
    previous_path: str | None = None,
) -> dict[str, Any]:
    """Aggregate all eval results into a benchmark report."""
    path = Path(iteration_path).resolve()
    if not path.is_dir():
        return {"error": f"Not a directory: {iteration_path}"}

    eval_dirs = discover_eval_dirs(path)
    if not eval_dirs:
        return {"error": f"No eval-* directories found in {path}"}

    # Extract iteration number from path
    iteration_match = re.search(r'iteration-(\d+)', path.name)
    iteration = int(iteration_match.group(1)) if iteration_match else 1

    per_eval: list[dict[str, Any]] = []
    all_with_pass_rates: list[float] = []
    all_baseline_pass_rates: list[float] = []
    all_with_tokens: list[float] = []
    all_baseline_tokens: list[float] = []
    all_with_durations: list[float] = []
    all_baseline_durations: list[float] = []

    for eval_dir in eval_dirs:
        eval_id_match = re.match(r'^eval-(\d+)$', eval_dir.name)
        eval_id = int(eval_id_match.group(1)) if eval_id_match else 0

        # Load eval metadata
        metadata = load_json(eval_dir / "eval_metadata.json")
        eval_name = metadata.get("eval_name", eval_dir.name) if metadata else eval_dir.name

        with_trials = collect_trial_data(eval_dir, "with_skill")
        baseline_trials = collect_trial_data(eval_dir, "baseline")

        with_pass_rates = [t["pass_rate"] for t in with_trials]
        baseline_pass_rates = [t["pass_rate"] for t in baseline_trials]
        with_tokens = [t["total_tokens"] for t in with_trials if t["total_tokens"] > 0]
        baseline_tokens = [t["total_tokens"] for t in baseline_trials if t["total_tokens"] > 0]
        with_durations = [t["duration_seconds"] for t in with_trials if t["duration_seconds"] > 0]
        baseline_durations = [t["duration_seconds"] for t in baseline_trials if t["duration_seconds"] > 0]

        eval_result: dict[str, Any] = {
            "eval_id": eval_id,
            "eval_name": eval_name,
            "trials": max(len(with_trials), len(baseline_trials)),
        }

        if with_pass_rates:
            eval_result["with_skill"] = {
                "pass_rate": calculate_stats(with_pass_rates)["mean"],
                "pass_rate_std": calculate_stats(with_pass_rates)["std"],
                "avg_tokens": calculate_stats(with_tokens)["mean"] if with_tokens else 0,
                "avg_duration_seconds": calculate_stats(with_durations)["mean"] if with_durations else 0,
            }
            all_with_pass_rates.extend(with_pass_rates)
            all_with_tokens.extend(with_tokens)
            all_with_durations.extend(with_durations)

        if baseline_pass_rates:
            eval_result["baseline"] = {
                "pass_rate": calculate_stats(baseline_pass_rates)["mean"],
                "pass_rate_std": calculate_stats(baseline_pass_rates)["std"],
                "avg_tokens": calculate_stats(baseline_tokens)["mean"] if baseline_tokens else 0,
                "avg_duration_seconds": calculate_stats(baseline_durations)["mean"] if baseline_durations else 0,
            }
            all_baseline_pass_rates.extend(baseline_pass_rates)
            all_baseline_tokens.extend(baseline_tokens)
            all_baseline_durations.extend(baseline_durations)

        per_eval.append(eval_result)

    # Calculate overall summary
    with_stats = calculate_stats(all_with_pass_rates)
    baseline_stats = calculate_stats(all_baseline_pass_rates)

    with_token_mean = calculate_stats(all_with_tokens)["mean"] if all_with_tokens else 0
    baseline_token_mean = calculate_stats(all_baseline_tokens)["mean"] if all_baseline_tokens else 0
    with_duration_mean = calculate_stats(all_with_durations)["mean"] if all_with_durations else 0
    baseline_duration_mean = calculate_stats(all_baseline_durations)["mean"] if all_baseline_durations else 0

    # Ratios: >1 means with_skill is better for pass rate, <1 means with_skill uses fewer tokens/time
    # Handle edge cases: no baseline data or zero baseline values
    if baseline_stats["mean"] > 0:
        improvement_ratio = round(with_stats["mean"] / baseline_stats["mean"], 2)
    elif with_stats["mean"] > 0:
        improvement_ratio = 999.99  # Skill passes but baseline doesn't (capped for JSON)
    else:
        improvement_ratio = 1.0  # Both zero — no improvement

    token_savings = round(with_token_mean / baseline_token_mean, 2) if baseline_token_mean > 0 else 1.0
    time_savings = round(with_duration_mean / baseline_duration_mean, 2) if baseline_duration_mean > 0 else 1.0

    benchmark: dict[str, Any] = {
        "skill_name": skill_name,
        "iteration": iteration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_evals": len(per_eval),
            "with_skill": {
                "pass_rate": with_stats["mean"],
                "pass_rate_std": with_stats["std"],
                "avg_tokens": with_token_mean,
                "avg_duration_seconds": with_duration_mean,
            },
            "baseline": {
                "pass_rate": baseline_stats["mean"],
                "pass_rate_std": baseline_stats["std"],
                "avg_tokens": baseline_token_mean,
                "avg_duration_seconds": baseline_duration_mean,
            },
            "improvement_ratio": improvement_ratio,
            "token_savings_ratio": token_savings,
            "time_savings_ratio": time_savings,
        },
        "per_eval": per_eval,
    }

    # Compare with previous iteration
    if previous_path:
        prev_benchmark = load_json(Path(previous_path) / "benchmark.json")
        if prev_benchmark:
            prev_summary = prev_benchmark.get("summary", {})
            prev_with = prev_summary.get("with_skill", {})
            benchmark["comparison"] = {
                "previous_iteration": prev_benchmark.get("iteration", 0),
                "pass_rate_delta": round(
                    with_stats["mean"] - prev_with.get("pass_rate", 0), 4
                ),
                "token_delta": round(
                    with_token_mean - prev_with.get("avg_tokens", 0), 2
                ),
                "duration_delta": round(
                    with_duration_mean - prev_with.get("avg_duration_seconds", 0), 2
                ),
            }

    # Write outputs
    benchmark_json_path = path / "benchmark.json"
    benchmark_json_path.write_text(json.dumps(benchmark, indent=2))

    # Generate markdown report
    md_lines = [
        f"# Benchmark Report: {skill_name}",
        f"",
        f"**Iteration**: {iteration}  ",
        f"**Timestamp**: {benchmark['timestamp']}  ",
        f"**Total Evals**: {len(per_eval)}",
        f"",
        f"## Summary",
        f"",
        f"| Metric | With Skill | Baseline | Ratio |",
        f"|--------|-----------|----------|-------|",
        f"| Pass Rate | {with_stats['mean']:.0%} (std {with_stats['std']:.2f}) | {baseline_stats['mean']:.0%} (std {baseline_stats['std']:.2f}) | {improvement_ratio}x |",
        f"| Avg Tokens | {with_token_mean:,.0f} | {baseline_token_mean:,.0f} | {token_savings}x |",
        f"| Avg Time | {with_duration_mean:.1f}s | {baseline_duration_mean:.1f}s | {time_savings}x |",
        f"",
        f"## Per-Eval Results",
        f"",
        f"| Eval | With Skill | Baseline | Trials |",
        f"|------|-----------|----------|--------|",
    ]

    for e in per_eval:
        w_rate = e.get("with_skill", {}).get("pass_rate", 0)
        b_rate = e.get("baseline", {}).get("pass_rate", 0)
        trials = e.get("trials", 0)
        md_lines.append(f"| {e['eval_name']} | {w_rate:.0%} | {b_rate:.0%} | {trials} |")

    md_lines.append("")

    benchmark_md_path = path / "benchmark.md"
    benchmark_md_path.write_text("\n".join(md_lines))

    return {
        "status": "success",
        "benchmark_json": str(benchmark_json_path),
        "benchmark_md": str(benchmark_md_path),
        "summary": benchmark["summary"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Aggregate eval results into a benchmark report"
    )
    parser.add_argument("path", help="Path to iteration-N workspace directory")
    parser.add_argument(
        "--skill-name", required=True,
        help="Name of the skill being benchmarked"
    )
    parser.add_argument(
        "--previous", "-p",
        help="Path to previous iteration directory for comparison"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print(json.dumps({"error": f"Not a directory: {args.path}"}), file=sys.stderr)
        sys.exit(1)

    result = aggregate_benchmark(args.path, args.skill_name, args.previous)
    print(json.dumps(result, indent=2))

    if "error" in result:
        sys.exit(1)
