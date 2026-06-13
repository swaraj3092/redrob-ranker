#!/usr/bin/env python3
"""
rank.py — Redrob Hackathon: Intelligent Candidate Discovery & Ranking System
=============================================================================
Entry point. Processes candidates.jsonl and produces a ranked submission CSV.

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Constraints:
    - No API calls during ranking
    - No GPU usage
    - Must complete in < 5 minutes on 16 GB CPU machine
    - Outputs exactly 100 rows + header, ranks 1-100

Architecture: 5-layer scoring pipeline
    Layer 1: Honeypot/fraud detection
    Layer 2: Hard disqualifier penalties
    Layer 3: Technical match score (skills + text + assessments + GitHub)
    Layer 4: Career quality score (company type + experience + trajectory)
    Layer 5: Behavioral signal multiplier (availability + engagement)
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Iterator, Dict, Any

from ranker.pipeline import score_candidate


def iter_candidates(candidates_path: Path) -> Iterator[Dict[str, Any]]:
    """Stream candidates from .jsonl file, handling both plain and gzipped."""
    path_str = str(candidates_path)

    if path_str.endswith(".gz"):
        import gzip
        opener = lambda: gzip.open(candidates_path, "rt", encoding="utf-8")
    else:
        opener = lambda: open(candidates_path, "r", encoding="utf-8")

    with opener() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def rank_candidates(candidates_path: Path, top_n: int = 100) -> list:
    """
    Stream all candidates, score each, return top_n sorted by final_score DESC.
    Memory-efficient: only the scored results (not raw profiles) are kept.
    """
    results = []
    total = 0
    honeypots = 0
    disqualified = 0

    t0 = time.time()
    for candidate in iter_candidates(candidates_path):
        total += 1
        result = score_candidate(candidate)

        if result["is_honeypot"]:
            honeypots += 1
        elif result.get("disqualifier"):
            disqualified += 1

        # Store lightweight result (drop heavy breakdowns from memory after scoring)
        results.append({
            "candidate_id": result["candidate_id"],
            "final_score":  result["final_score"],
            "reasoning":    result["reasoning"],
            "is_honeypot":  result["is_honeypot"],
        })

        if total % 10000 == 0:
            elapsed = time.time() - t0
            print(f"  Processed {total:,} candidates in {elapsed:.1f}s "
                  f"({honeypots} honeypots, {disqualified} disqualified)",
                  file=sys.stderr)

    elapsed = time.time() - t0
    print(
        f"\nScored {total:,} candidates in {elapsed:.1f}s | "
        f"Honeypots: {honeypots} | Disqualified (soft): {disqualified}",
        file=sys.stderr
    )

    # Sort by score descending; break ties by candidate_id ascending (per spec)
    results.sort(key=lambda r: (-r["final_score"], r["candidate_id"]))

    return results[:top_n], {
        "total": total,
        "honeypots": honeypots,
        "disqualified": disqualified,
        "elapsed_seconds": round(elapsed, 2),
    }


def normalise_scores(ranked: list) -> list:
    """
    Ensure scores are strictly non-increasing as rank increases (per spec §3).
    If a score tie exists, keep scores equal (ties are allowed; ranks still unique).
    This function clamps any accidental reversals.
    """
    if not ranked:
        return ranked

    normalised = list(ranked)
    max_score = normalised[0]["final_score"]

    for i in range(1, len(normalised)):
        if normalised[i]["final_score"] > normalised[i - 1]["final_score"]:
            normalised[i]["final_score"] = normalised[i - 1]["final_score"]

    # Scale to [0.20, 0.99] range to avoid suspicious all-same scores
    # while preserving relative ordering
    min_s = normalised[-1]["final_score"]
    max_s = normalised[0]["final_score"]
    span = max_s - min_s

    if span > 0:
        for r in normalised:
            r["final_score"] = round(
                0.20 + 0.79 * (r["final_score"] - min_s) / span, 4
            )
    else:
        # All same — distribute uniformly
        for i, r in enumerate(normalised):
            r["final_score"] = round(0.99 - (i * 0.79 / max(1, len(normalised) - 1)), 4)

    return normalised


def write_submission(ranked: list, output_path: Path) -> None:
    """Write the submission CSV per spec §2-3."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for rank_idx, result in enumerate(ranked, start=1):
            writer.writerow([
                result["candidate_id"],
                rank_idx,
                f"{result['final_score']:.4f}",
                result["reasoning"],
            ])

    print(f"\nSubmission written → {output_path}", file=sys.stderr)
    print(f"  Rows: {len(ranked)}", file=sys.stderr)
    print(f"  Rank 1:  {ranked[0]['candidate_id']} (score={ranked[0]['final_score']:.4f})", file=sys.stderr)
    print(f"  Rank 10: {ranked[9]['candidate_id']} (score={ranked[9]['final_score']:.4f})", file=sys.stderr)
    print(f"  Rank 100:{ranked[-1]['candidate_id']} (score={ranked[-1]['final_score']:.4f})", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Redrob Intelligent Candidate Ranker — produces top-100 submission CSV"
    )
    parser.add_argument(
        "--candidates",
        required=True,
        type=Path,
        help="Path to candidates.jsonl (or candidates.jsonl.gz)"
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Output path for submission CSV (e.g. ./submission.csv)"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=100,
        help="Number of candidates to rank (default: 100, per spec)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validate_submission.py after generating the CSV"
    )
    args = parser.parse_args()

    if not args.candidates.exists():
        print(f"ERROR: candidates file not found: {args.candidates}", file=sys.stderr)
        sys.exit(1)

    print(f"Redrob Candidate Ranker", file=sys.stderr)
    print(f"  Input:  {args.candidates}", file=sys.stderr)
    print(f"  Output: {args.out}", file=sys.stderr)
    print(f"  Top-N:  {args.top_n}", file=sys.stderr)
    print("", file=sys.stderr)

    print("Scoring candidates...", file=sys.stderr)
    ranked, stats = rank_candidates(args.candidates, top_n=args.top_n)

    print("\nNormalising scores...", file=sys.stderr)
    ranked = normalise_scores(ranked)

    print("\nWriting submission...", file=sys.stderr)
    write_submission(ranked, args.out)

    print(f"\nDone in {stats['elapsed_seconds']}s", file=sys.stderr)
    print(f"Stats: {stats}", file=sys.stderr)

    if args.validate:
        import subprocess
        result = subprocess.run(
            [sys.executable, "validate_submission.py", str(args.out)],
            capture_output=True, text=True
        )
        print("\n=== Validation ===", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
