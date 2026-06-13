"""
honeypot_detector.py — Layer 1: Cross-validate profile internal consistency.
Profiles with impossible or contradictory data are honeypots → score clamped to 0.
"""

import math
from datetime import date, datetime
from typing import Dict, Any, List


def _parse_date(d: str) -> date | None:
    if not d:
        return None
    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        return None


def is_honeypot(candidate: Dict[str, Any], reference_date: date) -> tuple[bool, str]:
    """
    Returns (is_honeypot: bool, reason: str).
    A honeypot is a candidate with an internally contradictory / impossible profile.
    """
    pid = candidate.get("candidate_id", "?")
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})

    yoe = float(profile.get("years_of_experience", 0))

    # ── CHECK 1: YoE vs. sum of career duration ─────────────────────────────
    total_career_months = sum(
        int(h.get("duration_months", 0)) for h in career
    )
    total_career_years = total_career_months / 12.0
    # Allow 2-year slack for gaps/overlaps; flag if YoE is massively overstated
    if yoe > 0 and total_career_years > 0:
        if yoe > (total_career_years + 3.0) and yoe > 5:
            return True, (
                f"YoE={yoe:.1f} but total career history={total_career_years:.1f}yr "
                f"(gap > 3yr)"
            )

    # ── CHECK 2: Expert skill with 0 months used ────────────────────────────
    zero_month_experts = [
        s["name"] for s in skills
        if s.get("proficiency") == "expert" and int(s.get("duration_months", 1)) == 0
    ]
    if zero_month_experts:
        return True, (
            f"Expert proficiency with 0 months used: {zero_month_experts[:3]}"
        )

    # ── CHECK 3: Too many expert skills simultaneously ────────────────────────
    expert_skills = [s for s in skills if s.get("proficiency") == "expert"]
    if len(expert_skills) >= 9:
        return True, (
            f"{len(expert_skills)} skills listed as expert — implausibly broad"
        )

    # ── CHECK 4: Career role start_date before realistic career start ────────
    # If someone has 3 yrs YoE but a role that started 15 years ago, contradiction
    if yoe > 0 and career:
        earliest_possible_start = reference_date.year - yoe - 2  # 2yr buffer
        for h in career:
            sd = _parse_date(h.get("start_date", ""))
            if sd and sd.year < (earliest_possible_start - 2):
                return True, (
                    f"Career role at {h.get('company','?')} starts {sd.year} "
                    f"but YoE={yoe:.1f} implies career started ~{int(reference_date.year - yoe)}"
                )

    # ── CHECK 5: Duration_months wildly inconsistent with start/end dates ────
    for h in career:
        sd = _parse_date(h.get("start_date", ""))
        ed = h.get("end_date")
        stated_months = int(h.get("duration_months", 0))
        if sd and ed and stated_months > 0:
            end_date = _parse_date(ed)
            if end_date:
                actual_months = (
                    (end_date.year - sd.year) * 12 + (end_date.month - sd.month)
                )
                # Flag if stated duration is wildly off (> 24 months discrepancy)
                if abs(actual_months - stated_months) > 24:
                    return True, (
                        f"Role at {h.get('company','?')}: stated {stated_months} months "
                        f"but dates imply {actual_months} months"
                    )

    # ── CHECK 6: Signup date in the future ───────────────────────────────────
    signup = _parse_date(signals.get("signup_date", ""))
    if signup and signup > reference_date:
        return True, f"signup_date {signup} is in the future"

    # ── CHECK 7: last_active_date before signup_date ──────────────────────────
    last_active = _parse_date(signals.get("last_active_date", ""))
    if signup and last_active and last_active < signup:
        return True, f"last_active_date {last_active} < signup_date {signup}"

    # ── CHECK 8: Impossible metric combinations ───────────────────────────────
    rr = float(signals.get("recruiter_response_rate", 0))
    apps = int(signals.get("applications_submitted_30d", 0))
    offer_rate = float(signals.get("offer_acceptance_rate", -1))

    # offer_acceptance_rate > 0 but interview_completion_rate = 0 → impossible
    icr = float(signals.get("interview_completion_rate", 0))
    if offer_rate > 0 and icr == 0:
        return True, "offer_acceptance_rate > 0 but interview_completion_rate = 0"

    return False, ""
