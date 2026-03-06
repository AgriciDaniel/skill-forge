#!/usr/bin/env python3
"""
Purpose: Optimize a skill's description for triggering accuracy using eval-driven iteration.
Input: Path to skill directory, path to trigger eval set JSON
Output: JSON report with best description, per-iteration scores, and train/test breakdown
Usage: python scripts/optimize_description.py /path/to/skill --eval-set trigger_evals.json

The optimization loop:
1. Splits eval set into 60% train / 40% held-out test
2. Evaluates current description against train set
3. Proposes improved description based on failures
4. Re-evaluates on both train and test
5. Iterates up to --max-iterations times
6. Selects best by test score (avoids overfitting)
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

# Use shared parser when available; inline fallback for standalone execution
try:
    from skill_utils import parse_frontmatter_simple as parse_frontmatter
except ImportError:
    def parse_frontmatter(content: str) -> tuple[dict[str, Any] | None, str]:  # type: ignore[misc]
        """Parse YAML frontmatter from SKILL.md content (inline fallback)."""
        if not content.startswith('---'):
            return None, content
        parts = content.split('---', 2)
        if len(parts) < 3:
            return None, content
        yaml_text, body = parts[1].strip(), parts[2].strip()
        frontmatter: dict[str, Any] = {}
        current_key, current_value, in_multiline = "", "", False
        for line in yaml_text.split('\n'):
            stripped = line.strip()
            if in_multiline:
                if stripped and not re.match(r'^[a-z_-]+:', stripped):
                    current_value += " " + stripped
                    continue
                frontmatter[current_key] = current_value.strip()
                in_multiline = False
            match = re.match(r'^([a-z_-]+):\s*(.*)', stripped)
            if match:
                current_key, value = match.group(1), match.group(2).strip()
                if value in ('>', '|'):
                    in_multiline, current_value = True, ""
                elif value:
                    frontmatter[current_key] = value.strip('"').strip("'")
        if in_multiline:
            frontmatter[current_key] = current_value.strip()
        return frontmatter, body


def split_eval_set(
    evals: list[dict[str, Any]],
    train_ratio: float = 0.6,
    seed: int = 42,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split evals into train and test sets, stratified by should_trigger."""
    rng = random.Random(seed)

    should_trigger = [e for e in evals if e.get("should_trigger", True)]
    should_not_trigger = [e for e in evals if not e.get("should_trigger", True)]

    rng.shuffle(should_trigger)
    rng.shuffle(should_not_trigger)

    def split_list(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        split_idx = max(1, int(len(items) * train_ratio))
        return items[:split_idx], items[split_idx:]

    train_pos, test_pos = split_list(should_trigger)
    train_neg, test_neg = split_list(should_not_trigger)

    return train_pos + train_neg, test_pos + test_neg


def score_description(
    description: str,
    eval_set: list[dict[str, Any]],
) -> dict[str, Any]:
    """Score a description against an eval set using keyword matching heuristics.

    This is a deterministic approximation. For full accuracy, the calling
    orchestrator (Claude) should run actual trigger tests and feed results back.
    This script provides a baseline heuristic score.
    """
    desc_lower = description.lower()
    desc_words = set(re.findall(r'[a-z]+(?:-[a-z]+)*', desc_lower))

    correct = 0
    total = len(eval_set)
    details: list[dict[str, Any]] = []

    for eval_item in eval_set:
        prompt = eval_item.get("prompt", "").lower()
        prompt_words = set(re.findall(r'[a-z]+(?:-[a-z]+)*', prompt))
        should_trigger = eval_item.get("should_trigger", True)

        # Heuristic: keyword overlap ratio
        overlap = desc_words & prompt_words
        overlap_ratio = len(overlap) / max(len(prompt_words), 1)

        # Threshold-based trigger prediction
        predicted_trigger = overlap_ratio > 0.15

        is_correct = predicted_trigger == should_trigger

        if is_correct:
            correct += 1

        details.append({
            "eval_id": eval_item.get("eval_id", 0),
            "prompt": eval_item.get("prompt", ""),
            "should_trigger": should_trigger,
            "predicted_trigger": predicted_trigger,
            "correct": is_correct,
            "overlap_ratio": round(overlap_ratio, 3),
            "matching_keywords": sorted(overlap)[:10],
        })

    return {
        "score": round(correct / total, 4) if total > 0 else 0.0,
        "correct": correct,
        "total": total,
        "details": details,
    }


def suggest_improvements(
    description: str,
    failures: list[dict[str, Any]],
) -> list[str]:
    """Suggest description improvements based on failure analysis."""
    suggestions: list[str] = []

    false_negatives = [f for f in failures if f["should_trigger"] and not f["predicted_trigger"]]
    false_positives = [f for f in failures if not f["should_trigger"] and f["predicted_trigger"]]

    if false_negatives:
        missing_keywords: set[str] = set()
        for fn in false_negatives:
            prompt_words = set(re.findall(r'[a-z]+(?:-[a-z]+)*', fn["prompt"].lower()))
            missing_keywords.update(prompt_words - set(re.findall(r'[a-z]+(?:-[a-z]+)*', description.lower())))

        # Filter out stop words
        stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'can', 'you', 'help', 'need', 'want'}
        missing_keywords -= stop_words

        if missing_keywords:
            top_missing = sorted(missing_keywords)[:10]
            suggestions.append(
                f"Add trigger keywords for under-triggering: {', '.join(top_missing)}"
            )
        suggestions.append(
            f"{len(false_negatives)} queries that should trigger are being missed"
        )

    if false_positives:
        suggestions.append(
            f"{len(false_positives)} unrelated queries are matching — narrow the description scope"
        )
        suggestions.append(
            "Consider adding negative triggers (\"Do NOT use for...\")"
        )

    return suggestions


def run_optimization(
    skill_path: str,
    eval_set_path: str,
    max_iterations: int = 5,
    seed: int = 42,
) -> dict[str, Any]:
    """Run the description optimization loop."""
    path = Path(skill_path).resolve()
    skill_md = path / "SKILL.md"

    if not skill_md.exists():
        return {"error": f"SKILL.md not found at {path}"}

    content = skill_md.read_text()
    frontmatter, body = parse_frontmatter(content)

    if not frontmatter:
        return {"error": "Could not parse SKILL.md frontmatter"}

    eval_data = json.loads(Path(eval_set_path).read_text())
    all_evals = eval_data.get("evals", [])

    if not all_evals:
        return {"error": "Eval set is empty"}

    # Split into train/test
    train_set, test_set = split_eval_set(all_evals, seed=seed)

    current_description = frontmatter.get("description", "")
    iterations: list[dict[str, Any]] = []
    best_test_score = 0.0
    best_description = current_description

    for i in range(max_iterations):
        # Score on train
        train_result = score_description(current_description, train_set)
        # Score on test
        test_result = score_description(current_description, test_set)

        # Identify failures
        train_failures = [d for d in train_result["details"] if not d["correct"]]
        suggestions = suggest_improvements(current_description, train_failures)

        iteration_data = {
            "iteration": i + 1,
            "description": current_description,
            "train_score": train_result["score"],
            "test_score": test_result["score"],
            "train_correct": train_result["correct"],
            "train_total": train_result["total"],
            "test_correct": test_result["correct"],
            "test_total": test_result["total"],
            "failure_count": len(train_failures),
            "suggestions": suggestions,
        }
        iterations.append(iteration_data)

        # Track best by TEST score (avoid overfitting to train)
        if test_result["score"] > best_test_score:
            best_test_score = test_result["score"]
            best_description = current_description

        # If perfect on train, stop early
        if train_result["score"] >= 1.0:
            break

        # The actual description improvement should be done by Claude using
        # extended thinking. This script provides the data and suggestions;
        # the orchestrator applies the improvements.
        # For the automated heuristic pass, we stop here and return suggestions.
        break  # In practice, Claude iterates calling this script per round

    return {
        "status": "success",
        "skill_name": frontmatter.get("name", "unknown"),
        "original_description": frontmatter.get("description", ""),
        "best_description": best_description,
        "best_test_score": best_test_score,
        "train_set_size": len(train_set),
        "test_set_size": len(test_set),
        "iterations": iterations,
        "recommendation": (
            "Use the suggestions above to improve the description, "
            "then re-run this script to measure improvement. "
            "Select the description with the highest TEST score to avoid overfitting."
        ),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Optimize a skill's description for triggering accuracy"
    )
    parser.add_argument("path", help="Path to skill directory containing SKILL.md")
    parser.add_argument(
        "--eval-set", required=True,
        help="Path to trigger eval set JSON file"
    )
    parser.add_argument(
        "--max-iterations", type=int, default=5,
        help="Maximum optimization iterations (default: 5)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for train/test split (default: 42)"
    )
    args = parser.parse_args()

    if not Path(args.path).is_dir():
        print(json.dumps({"error": f"Not a directory: {args.path}"}), file=sys.stderr)
        sys.exit(1)

    if not Path(args.eval_set).is_file():
        print(json.dumps({"error": f"Eval set not found: {args.eval_set}"}), file=sys.stderr)
        sys.exit(1)

    result = run_optimization(
        args.path, args.eval_set, args.max_iterations, args.seed
    )
    print(json.dumps(result, indent=2))

    if "error" in result:
        sys.exit(1)
