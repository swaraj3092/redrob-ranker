"""
pipeline.py — Master orchestrator for the 5-layer ranking pipeline.
Processes one candidate through all layers and returns a scored result.
"""

from datetime import date
from typing import Dict, Any, Optional

from ranker.config import (
    WEIGHT_TECH, WEIGHT_CAREER, WEIGHT_AVAIL, REFERENCE_DATE,
    MIN_TECH_SCORE_THRESHOLD
)
from ranker.honeypot_detector import is_honeypot
from ranker.tech_scorer import compute_tech_score
from ranker.career_scorer import compute_career_score
from ranker.behavioral_scorer import compute_behavioral_multiplier, compute_base_availability
from ranker.reasoning_engine import generate_reasoning


# Disqualifier penalty: applied as a multiplier before behavioral
DISQUALIFIER_MULTIPLIER = 0.04


def _apply_disqualifiers(
    candidate: Dict[str, Any],
    career_breakdown: Dict,
    tech_breakdown: Dict,
) -> tuple[float, Optional[str]]:
    """
    Layer 2: Hard disqualifier filter.
    Returns (penalty_multiplier, reason_string_or_None).
    """
    signals = candidate.get("redrob_signals", {})
    profile = candidate.get("profile", {})

    # ── Pure consulting-only career ──────────────────────────────────────
    if career_breakdown.get("consulting_ratio", 0) > 0.92:
        return DISQUALIFIER_MULTIPLIER, "pure_consulting_career"

    # ── Complete ghost candidate ─────────────────────────────────────────
    rr = float(signals.get("recruiter_response_rate", 0.5))
    from ranker.behavioral_scorer import _days_since
    days = _days_since(signals.get("last_active_date", ""), REFERENCE_DATE)
    if days > 300 and rr < 0.05 and not signals.get("open_to_work_flag"):
        return DISQUALIFIER_MULTIPLIER, "complete_ghost"

    # ── Zero technical relevance (entirely wrong domain) ─────────────────
    if tech_breakdown.get("tech_total", 0) < 0.02:
        if career_breakdown.get("avg_co_score", 0.5) < 0.35:
            return 0.10, "zero_technical_relevance"

    return 1.0, None


def score_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full 5-layer pipeline for a single candidate.
    Returns a result dict with final_score, breakdown, and reasoning.
    """
    cid = candidate.get("candidate_id", "?")

    # ── Layer 1: Honeypot detection ──────────────────────────────────────
    hp, hp_reason = is_honeypot(candidate, REFERENCE_DATE)
    if hp:
        return {
            "candidate_id": cid,
            "final_score": 0.0,
            "is_honeypot": True,
            "honeypot_reason": hp_reason,
            "tech_breakdown": {},
            "career_breakdown": {},
            "behavioral_breakdown": {},
            "reasoning": f"HONEYPOT: {hp_reason}",
        }

    # ── Layer 3: Technical score ─────────────────────────────────────────
    tech_score, tech_breakdown = compute_tech_score(candidate)

    # ── GATE: Minimum technical relevance threshold ───────────────────────
    # Candidates with essentially zero AI/ML relevance cannot enter top 100
    # regardless of how good their behavioral signals are.
    if tech_score < MIN_TECH_SCORE_THRESHOLD:
        return {
            "candidate_id": cid,
            "final_score": tech_score * 0.05,  # near-zero, won't rank in top 100
            "raw_score": tech_score * 0.05,
            "disqualifier": "below_min_tech_threshold",
            "is_honeypot": False,
            "tech_score": tech_score,
            "career_score": 0.0,
            "base_avail": 0.0,
            "behav_multiplier": 0.0,
            "tech_breakdown": tech_breakdown,
            "career_breakdown": {},
            "behavioral_breakdown": {},
            "reasoning": f"Insufficient technical relevance for this AI/ML role (score={tech_score:.3f}).",
        }

    # ── Layer 4: Career quality score ────────────────────────────────────
    career_score, career_breakdown = compute_career_score(candidate)

    # ── Layer 5: Behavioral multiplier ──────────────────────────────────
    signals = candidate.get("redrob_signals", {})
    behav_multiplier, behav_breakdown = compute_behavioral_multiplier(signals)
    base_avail = compute_base_availability(signals)

    # ── Layer 2: Hard disqualifiers (applied after computing subscores) ──
    disq_mult, disq_reason = _apply_disqualifiers(
        candidate, career_breakdown, tech_breakdown
    )

    # ── Final score composition ──────────────────────────────────────────
    raw_score = (
        WEIGHT_TECH   * tech_score +
        WEIGHT_CAREER * career_score +
        WEIGHT_AVAIL  * base_avail
    )

    # Apply disqualifier, then behavioral multiplier
    final_score = raw_score * disq_mult * behav_multiplier

    # Clip to [0, 1]
    final_score = min(1.0, max(0.0, final_score))

    # ── Reasoning ───────────────────────────────────────────────────────
    reasoning = generate_reasoning(
        candidate, tech_breakdown, career_breakdown, behav_breakdown, final_score
    )

    return {
        "candidate_id": cid,
        "final_score": final_score,
        "raw_score": raw_score,
        "disqualifier": disq_reason,
        "is_honeypot": False,
        "tech_score": tech_score,
        "career_score": career_score,
        "base_avail": base_avail,
        "behav_multiplier": behav_multiplier,
        "tech_breakdown": tech_breakdown,
        "career_breakdown": career_breakdown,
        "behavioral_breakdown": behav_breakdown,
        "reasoning": reasoning,
    }
