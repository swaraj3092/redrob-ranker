"""
reasoning_engine.py — Auto-generate specific, honest, non-templated reasoning.
Each reasoning string is built from actual scored features — never hallucinated.
"""

from typing import Dict, Any, List


def _top_n(items: List, n: int) -> List:
    return items[:n] if items else []


def generate_reasoning(
    candidate: Dict[str, Any],
    tech_breakdown: Dict,
    career_breakdown: Dict,
    behavioral_breakdown: Dict,
    final_score: float,
) -> str:
    """
    Generate a ≤2-sentence, specific reasoning string for the CSV submission.
    Grounded entirely in actual scored signals — no hallucinations.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    yoe = float(profile.get("years_of_experience", 0))
    title = profile.get("current_title", "N/A")
    company = profile.get("current_company", "")
    location = profile.get("location", "")
    country = profile.get("country", "")

    # ── Positive signals ──────────────────────────────────────────────────
    positives = []
    caveats = []

    # Technical highlights
    matched_skills = tech_breakdown.get("matched_skills", [])
    if matched_skills:
        top_skills = _top_n(matched_skills, 3)
        positives.append(f"strong core skills: {', '.join(top_skills)}")

    matched_clusters = tech_breakdown.get("matched_clusters", [])
    cluster_labels = {
        "retrieval_search": "retrieval/search systems experience",
        "production_ml":    "production ML deployment",
        "eval_frameworks":  "ranking eval expertise (NDCG/MRR)",
        "learning_to_rank": "learning-to-rank experience",
        "product_company_shipping": "shipped at product scale",
        "llm_and_embeddings": "LLM/embedding work",
        "nlp_ml_general":   "applied ML background",
    }
    if matched_clusters:
        top_cluster = matched_clusters[0]
        positives.append(cluster_labels.get(top_cluster, top_cluster))

    assess_score = tech_breakdown.get("assess_score", 0)
    if assess_score > 0.5:
        assessed = signals.get("skill_assessment_scores", {})
        top_assessed = sorted(assessed.items(), key=lambda x: -x[1])
        if top_assessed:
            sk, sc = top_assessed[0]
            positives.append(f"Redrob-assessed {sk} ({sc:.0f}/100)")

    # Career highlights
    if career_breakdown.get("product_flag"):
        positives.append("product company background")
    if career_breakdown.get("trajectory", 0) >= 0.75:
        positives.append("stable tenure history")

    # Location
    loc_score = career_breakdown.get("location_score", 0.5)
    if loc_score >= 0.85:
        positives.append(f"India-based ({location})")
    elif loc_score >= 0.55 and signals.get("willing_to_relocate"):
        positives.append("willing to relocate to India")

    # Behavioral highlights
    rr = behavioral_breakdown.get("response_rate", 0)
    if rr >= 0.75:
        positives.append(f"high recruiter response rate ({rr:.0%})")

    notice = behavioral_breakdown.get("notice_days", 90)
    if notice <= 30:
        positives.append(f"sub-{notice}d notice period")

    saves = behavioral_breakdown.get("recruiter_saves_30d", 0)
    if saves >= 8:
        positives.append(f"saved by {saves} recruiters in last 30d")

    days_inactive = behavioral_breakdown.get("days_inactive", 0)
    if days_inactive <= 14:
        positives.append("recently active on platform")

    github = float(signals.get("github_activity_score", -1))
    if github >= 50:
        positives.append(f"strong GitHub activity ({github:.0f}/100)")

    # ── Caveats (honest) ─────────────────────────────────────────────────
    if career_breakdown.get("pure_consulting_flag"):
        caveats.append("majority consulting background")

    if notice > 90:
        caveats.append(f"long notice period ({notice}d)")

    if days_inactive > 90:
        caveats.append(f"inactive for {days_inactive}d")

    if rr < 0.20:
        caveats.append(f"low response rate ({rr:.0%})")

    jh = career_breakdown.get("title_job_hops", 0)
    if jh >= 3:
        caveats.append("some signs of title-chasing")

    if not signals.get("open_to_work_flag"):
        caveats.append("not currently marked open-to-work")

    # ── Compose sentences ─────────────────────────────────────────────────
    # Sentence 1: identity + top positives
    positive_str = "; ".join(positives[:4]) if positives else "general ML background"
    sentence1 = (
        f"{title} with {yoe:.1f}yr exp"
        + (f" at {company}" if company else "")
        + f": {positive_str}."
    )

    # Sentence 2: caveats or final endorsement
    if caveats:
        sentence2 = f"Note: {'; '.join(caveats[:2])}."
    elif final_score >= 0.80:
        sentence2 = "Strong overall fit across technical, career, and availability signals."
    elif final_score >= 0.60:
        sentence2 = "Good fit with no major disqualifying factors identified."
    else:
        sentence2 = "Adjacent profile — included at edge of shortlist based on engagement signals."

    # Trim to max ~500 chars
    full = f"{sentence1} {sentence2}"
    if len(full) > 480:
        full = full[:477] + "..."

    return full
