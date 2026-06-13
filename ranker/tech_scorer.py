"""
tech_scorer.py — Layer 3: Technical Match Score.
Combines skill taxonomy scoring, career text semantic cluster matching,
platform assessment scores, and GitHub activity.
"""

import math
import re
from typing import Dict, Any, List

from ranker.config import (
    SKILL_TIERS, PROFICIENCY_WEIGHT, SEMANTIC_CLUSTERS,
    TECH_WEIGHT_SKILLS, TECH_WEIGHT_CAREER_TEXT,
    TECH_WEIGHT_ASSESSMENT, TECH_WEIGHT_GITHUB,
)


def _normalize(val: float, max_val: float) -> float:
    if max_val <= 0:
        return 0.0
    return min(1.0, val / max_val)


def score_skills(skills: List[Dict]) -> tuple[float, List[str]]:
    """
    Score candidate skills against the JD skill taxonomy.
    Returns (normalized_score 0-1, list of matched tier-1/2 skills).
    """
    raw = 0.0
    matched_key_skills = []

    for skill in skills:
        name_lower = skill.get("name", "").lower().strip()
        proficiency = skill.get("proficiency", "beginner")
        endorsements = int(skill.get("endorsements", 0))
        duration_months = int(skill.get("duration_months", 0))

        # Find best matching tier key (exact or substring)
        tier_weight = 0.0
        matched_key = None
        for key, weight in SKILL_TIERS.items():
            if key in name_lower or name_lower in key:
                if abs(weight) > abs(tier_weight):
                    tier_weight = weight
                    matched_key = key

        if tier_weight == 0.0:
            continue

        prof_w = PROFICIENCY_WEIGHT.get(proficiency, 0.25)

        # Duration trust: ramp from 0 to 1.0 over 24 months
        duration_trust = min(1.0, duration_months / 24.0) if duration_months > 0 else 0.10

        # Endorsement log-boost (diminishing returns)
        endorsement_boost = 1.0 + math.log1p(endorsements) / 10.0

        contribution = tier_weight * prof_w * duration_trust * endorsement_boost
        raw += contribution

        if tier_weight >= 2.0 and contribution > 0:
            matched_key_skills.append(skill.get("name", matched_key))

    # Cap: a perfect candidate with all Tier-1 skills at expert gets ~1.0
    # Empirically derived max (sum of all T1 skills at expert with 24+ months)
    MAX_RAW = 35.0
    return _normalize(raw, MAX_RAW), matched_key_skills[:8]


def score_career_text(career_history: List[Dict], summary: str) -> tuple[float, List[str]]:
    """
    Match career description text against semantic clusters.
    Returns (normalized_score 0-1, list of matched cluster names).
    """
    # Build full searchable text, weighted by recency
    # Most recent role gets 1.5× weight, older roles decay
    texts_by_weight = []
    for i, role in enumerate(career_history):
        desc = role.get("description", "").lower()
        # Recency weight: index 0 = current/most recent
        recency_w = max(0.4, 1.5 - (i * 0.25))
        texts_by_weight.append((desc, recency_w))

    # Also include profile summary at moderate weight
    texts_by_weight.append((summary.lower(), 1.0))

    raw = 0.0
    matched_clusters = []

    for cluster in SEMANTIC_CLUSTERS:
        cluster_hits = 0
        cluster_score = 0.0
        for text, weight in texts_by_weight:
            for kw in cluster["keywords"]:
                if kw in text:
                    cluster_hits += 1
                    cluster_score += weight

        if cluster_hits > 0:
            # Diminishing returns on repeated keyword hits within a cluster
            cluster_contribution = cluster["weight"] * math.log1p(cluster_score)
            raw += cluster_contribution
            if cluster["weight"] >= 2.0:
                matched_clusters.append(cluster["name"])

    MAX_RAW = 30.0
    return _normalize(raw, MAX_RAW), matched_clusters


def score_assessments(
    skill_assessment_scores: Dict[str, float],
    relevant_skills: set
) -> float:
    """
    Score platform-verified skill assessments.
    Only assessments on JD-relevant skills count.
    Returns float 0-1.
    """
    if not skill_assessment_scores:
        return 0.0

    relevant_scores = []
    for skill_name, score in skill_assessment_scores.items():
        skill_lower = skill_name.lower()
        # Check if this assessment is for a JD-relevant skill
        is_relevant = any(
            kw in skill_lower or skill_lower in kw
            for kw in relevant_skills
        )
        if is_relevant:
            relevant_scores.append(float(score) / 100.0)

    if not relevant_scores:
        return 0.0

    return sum(relevant_scores) / len(relevant_scores)


def score_github(github_activity_score: float) -> float:
    """Score GitHub activity. -1 means no GitHub linked."""
    if github_activity_score < 0:
        return 0.20  # neutral, not penalized — many great engineers are private
    return github_activity_score / 100.0


def compute_tech_score(candidate: Dict[str, Any]) -> tuple[float, Dict]:
    """
    Master function for Layer 3.
    Returns (tech_score 0-1, breakdown dict for reasoning).
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    career = candidate.get("career_history", [])
    signals = candidate.get("redrob_signals", {})
    summary = profile.get("summary", "")

    # Define relevant skill names for assessment cross-check
    relevant_skill_keys = {
        k for k, v in SKILL_TIERS.items() if v >= 1.0
    }

    skill_score, matched_skills = score_skills(skills)
    text_score, matched_clusters = score_career_text(career, summary)
    assess_score = score_assessments(
        signals.get("skill_assessment_scores", {}),
        relevant_skill_keys
    )
    github_score = score_github(float(signals.get("github_activity_score", -1)))

    # Weighted composite
    tech_score = (
        TECH_WEIGHT_SKILLS      * skill_score +
        TECH_WEIGHT_CAREER_TEXT * text_score +
        TECH_WEIGHT_ASSESSMENT  * assess_score +
        TECH_WEIGHT_GITHUB      * github_score
    )

    breakdown = {
        "skill_score":     round(skill_score, 4),
        "text_score":      round(text_score, 4),
        "assess_score":    round(assess_score, 4),
        "github_score":    round(github_score, 4),
        "tech_total":      round(tech_score, 4),
        "matched_skills":  matched_skills,
        "matched_clusters": matched_clusters,
    }

    return min(1.0, tech_score), breakdown
