"""
behavioral_scorer.py — Layer 5: Behavioral Signal Multiplier.
Uses redrob_signals to compute a multiplicative availability/engagement modifier.
A perfect-on-paper candidate who is unreachable is worthless to a recruiter.
"""

import math
from datetime import date, datetime
from typing import Dict, Any

from ranker.config import REFERENCE_DATE


def _days_since(date_str: str, reference: date) -> int:
    """Return days between date_str and reference. Returns 999 if missing."""
    if not date_str:
        return 999
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return max(0, (reference - d).days)
    except Exception:
        return 999


def compute_behavioral_multiplier(signals: Dict[str, Any]) -> tuple[float, Dict]:
    """
    Compute behavioral multiplier (0.05 – 1.50).
    Multiplicative: applied on top of the raw tech+career score.
    Returns (multiplier, breakdown dict).
    """
    m = 1.0
    notes = []

    # ── 1. Open-to-work flag ─────────────────────────────────────────────────
    open_to_work = bool(signals.get("open_to_work_flag", False))
    if open_to_work:
        m *= 1.05
        notes.append("open_to_work(+)")
    else:
        m *= 0.65
        notes.append("not_open_to_work(-)")

    # ── 2. Recency of last activity ──────────────────────────────────────────
    days_inactive = _days_since(signals.get("last_active_date", ""), REFERENCE_DATE)
    if days_inactive <= 7:
        m *= 1.20
        notes.append(f"very_recent_active({days_inactive}d)(+)")
    elif days_inactive <= 14:
        m *= 1.10
        notes.append(f"recent_active({days_inactive}d)(+)")
    elif days_inactive <= 30:
        m *= 1.00
    elif days_inactive <= 60:
        m *= 0.88
        notes.append(f"inactive_{days_inactive}d(-)")
    elif days_inactive <= 120:
        m *= 0.70
        notes.append(f"inactive_{days_inactive}d(--)")
    elif days_inactive <= 180:
        m *= 0.50
        notes.append(f"inactive_{days_inactive}d(---)")
    else:
        m *= 0.25
        notes.append(f"ghost_{days_inactive}d(----)")

    # ── 3. Recruiter response rate ───────────────────────────────────────────
    rr = float(signals.get("recruiter_response_rate", 0.5))
    if rr >= 0.80:
        m *= 1.12
        notes.append(f"high_response_rate({rr:.0%})(+)")
    elif rr >= 0.60:
        m *= 1.05
    elif rr >= 0.40:
        m *= 1.00
    elif rr >= 0.20:
        m *= 0.85
        notes.append(f"low_response_rate({rr:.0%})(-)")
    elif rr >= 0.10:
        m *= 0.65
        notes.append(f"very_low_rr({rr:.0%})(--)")
    else:
        m *= 0.40
        notes.append(f"ghost_rr({rr:.0%})(---)")

    # ── 4. Response time (avg hours) ─────────────────────────────────────────
    avg_rt = float(signals.get("avg_response_time_hours", 48))
    if avg_rt <= 4:
        m *= 1.05
    elif avg_rt <= 24:
        m *= 1.02
    elif avg_rt <= 72:
        m *= 1.00
    elif avg_rt <= 168:  # 1 week
        m *= 0.95
    else:
        m *= 0.90

    # ── 5. Notice period ─────────────────────────────────────────────────────
    notice = int(signals.get("notice_period_days", 90))
    if notice <= 15:
        m *= 1.10
        notes.append("sub_15d_notice(+)")
    elif notice <= 30:
        m *= 1.05
        notes.append("sub_30d_notice(+)")
    elif notice <= 60:
        m *= 0.98
    elif notice <= 90:
        m *= 0.88
    elif notice <= 120:
        m *= 0.78
        notes.append(f"long_notice_{notice}d(-)")
    else:
        m *= 0.65
        notes.append(f"very_long_notice_{notice}d(--)")

    # ── 6. Profile completeness ──────────────────────────────────────────────
    completeness = float(signals.get("profile_completeness_score", 50))
    completeness_factor = 0.60 + 0.40 * (completeness / 100.0)
    m *= completeness_factor

    # ── 7. Verification trust ────────────────────────────────────────────────
    verified_email = bool(signals.get("verified_email", False))
    verified_phone = bool(signals.get("verified_phone", False))
    if verified_email and verified_phone:
        m *= 1.05
        notes.append("fully_verified(+)")
    elif verified_email or verified_phone:
        m *= 1.00
    else:
        m *= 0.90
        notes.append("not_verified(-)")

    # ── 8. Interview completion rate ─────────────────────────────────────────
    icr = float(signals.get("interview_completion_rate", 0.5))
    m *= (0.65 + 0.35 * icr)  # scales from 0.65 to 1.0

    # ── 9. Recruiter saves (social proof) ───────────────────────────────────
    saved_30d = int(signals.get("saved_by_recruiters_30d", 0))
    if saved_30d >= 10:
        m *= 1.08
        notes.append(f"in_demand({saved_30d}_saves)(+)")
    elif saved_30d >= 5:
        m *= 1.04
    elif saved_30d >= 1:
        m *= 1.01

    # Cap multiplier range: absolute floor 0.05, ceiling 1.50
    m = max(0.05, min(1.50, m))

    breakdown = {
        "behavioral_multiplier": round(m, 4),
        "open_to_work": open_to_work,
        "days_inactive": days_inactive,
        "response_rate": rr,
        "notice_days": notice,
        "profile_completeness": completeness,
        "interview_completion": icr,
        "recruiter_saves_30d": saved_30d,
        "behavioral_notes": notes,
    }

    return m, breakdown


def compute_base_availability(signals: Dict[str, Any]) -> float:
    """
    A simple 0-1 score representing 'how available is this person right now'.
    Used as the third component in the raw score before multiplier is applied.
    """
    score = 0.5
    if signals.get("open_to_work_flag"):
        score += 0.20
    rr = float(signals.get("recruiter_response_rate", 0.3))
    score += 0.20 * rr
    days = _days_since(signals.get("last_active_date", ""), REFERENCE_DATE)
    recency = max(0.0, 1.0 - (days / 180.0))
    score += 0.10 * recency
    return min(1.0, score)
