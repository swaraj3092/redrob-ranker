"""
career_scorer.py — Layer 4: Career Quality Score.
Evaluates company type, experience bracket, trajectory, location, education.
"""

import math
from datetime import date, datetime
from typing import Dict, Any, List

from ranker.config import (
    PURE_CONSULTING_FIRMS, PRODUCT_COMPANIES, RESEARCH_INSTITUTIONS,
    EDU_TIER_SCORE, experience_score, location_score, notice_score,
)


def _company_type_score(company_name: str, industry: str, company_size: str) -> float:
    """
    Score a single company appearance.
    1.0 = clear product company, 0.3 = pure consulting, 0.5 = ambiguous.
    """
    name_lower = (company_name or "").lower().strip()
    industry_lower = (industry or "").lower().strip()

    # Check known consulting firms
    for firm in PURE_CONSULTING_FIRMS:
        if firm in name_lower:
            return 0.25

    # Check known product companies
    for prod in PRODUCT_COMPANIES:
        if prod in name_lower:
            return 1.00

    # Industry-based inference
    product_industries = {
        "software", "saas", "fintech", "edtech", "food delivery",
        "e-commerce", "ecommerce", "ai", "ai/ml", "machine learning",
        "internet", "technology", "product", "startup",
        "transportation", "logistics", "healthtech", "health tech",
    }
    consulting_industries = {
        "it services", "consulting", "it consulting", "bpo",
        "outsourcing", "staffing",
    }

    for pi in product_industries:
        if pi in industry_lower:
            return 0.85

    for ci in consulting_industries:
        if ci in industry_lower:
            return 0.30

    # Size-based heuristic: very small companies tend to be product
    if company_size in ("1-10", "11-50", "51-200"):
        return 0.75

    return 0.55  # ambiguous


def score_company_history(career_history: List[Dict]) -> tuple[float, Dict]:
    """
    Weighted average company quality across career, weighted by duration.
    Recent roles get recency bonus.
    """
    if not career_history:
        return 0.3, {"consulting_flag": False, "product_flag": False}

    total_weight = 0.0
    weighted_score = 0.0
    pure_consulting_months = 0
    product_months = 0
    total_months = 0
    title_job_hop_count = 0
    prev_title = None

    for i, role in enumerate(career_history):
        company = role.get("company", "")
        industry = role.get("industry", "")
        size = role.get("company_size", "")
        duration = max(1, int(role.get("duration_months", 1)))
        title = (role.get("title", "") or "").lower()

        co_score = _company_type_score(company, industry, size)

        # Recency weight: most recent role counts more
        recency_weight = max(0.5, 1.5 - (i * 0.25))
        weight = duration * recency_weight

        weighted_score += co_score * weight
        total_weight += weight
        total_months += duration

        if co_score <= 0.30:
            pure_consulting_months += duration
        elif co_score >= 0.85:
            product_months += duration

        # Title job-hop detection (same title at many companies quickly)
        if prev_title and prev_title == title and duration < 18:
            title_job_hop_count += 1
        prev_title = title

    avg_co_score = weighted_score / total_weight if total_weight > 0 else 0.4

    # Penalize if >70% of career is in pure consulting
    consulting_ratio = pure_consulting_months / max(1, total_months)
    if consulting_ratio > 0.80:
        avg_co_score *= 0.4  # heavy penalty

    # Bonus if majority is product company
    product_ratio = product_months / max(1, total_months)
    if product_ratio > 0.60:
        avg_co_score = min(1.0, avg_co_score * 1.15)

    breakdown = {
        "avg_co_score": round(avg_co_score, 4),
        "consulting_ratio": round(consulting_ratio, 4),
        "product_ratio": round(product_ratio, 4),
        "pure_consulting_flag": consulting_ratio > 0.80,
        "product_flag": product_ratio > 0.40,
        "title_job_hops": title_job_hop_count,
    }
    return min(1.0, avg_co_score), breakdown


def score_career_trajectory(career_history: List[Dict]) -> float:
    """
    Reward upward trajectory, penalize excessive title-chasing / instability.
    """
    if len(career_history) < 2:
        return 0.60

    # Average tenure in months
    durations = [max(1, int(h.get("duration_months", 1))) for h in career_history]
    avg_tenure = sum(durations) / len(durations)

    # JD explicitly penalizes < 18 month average tenure
    if avg_tenure < 12:
        return 0.30
    if avg_tenure < 18:
        return 0.55
    if avg_tenure < 30:
        return 0.75
    return 1.00


def score_education(education: List[Dict]) -> float:
    """Score highest-tier education entry."""
    if not education:
        return 0.50

    best = 0.0
    for edu in education:
        tier = edu.get("tier", "unknown")
        score = EDU_TIER_SCORE.get(tier, 0.50)
        best = max(best, score)
    return best


def compute_career_score(candidate: Dict[str, Any]) -> tuple[float, Dict]:
    """
    Master function for Layer 4.
    Returns (career_score 0-1, breakdown dict).
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    education = candidate.get("education", [])
    signals = candidate.get("redrob_signals", {})

    yoe = float(profile.get("years_of_experience", 0))
    location = profile.get("location", "")
    country = profile.get("country", "")
    willing_relocate = bool(signals.get("willing_to_relocate", False))
    notice = int(signals.get("notice_period_days", 90))

    exp_sc = experience_score(yoe)
    co_sc, co_breakdown = score_company_history(career)
    traj_sc = score_career_trajectory(career)
    loc_sc = location_score(location, country, willing_relocate)
    edu_sc = score_education(education)
    notice_sc = notice_score(notice)

    # Weighted composite for career quality
    career_score = (
        0.30 * co_sc +
        0.25 * exp_sc +
        0.15 * traj_sc +
        0.15 * loc_sc +
        0.10 * edu_sc +
        0.05 * notice_sc
    )

    breakdown = {
        "exp_score":      round(exp_sc, 4),
        "company_score":  round(co_sc, 4),
        "trajectory":     round(traj_sc, 4),
        "location_score": round(loc_sc, 4),
        "edu_score":      round(edu_sc, 4),
        "notice_score":   round(notice_sc, 4),
        "career_total":   round(career_score, 4),
        **co_breakdown,
    }

    return min(1.0, career_score), breakdown
