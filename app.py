"""
app.py — Redrob Candidate Ranker · Streamlit Sandbox
=====================================================
A clean, functional sandbox for hackathon evaluation.
Upload ≤100 candidate JSON(L) profiles, rank them, download the CSV.
"""

import csv
import io
import json
import sys
import time
from pathlib import Path

import streamlit as st
import pandas as pd

# Ensure ranker package is importable
sys.path.insert(0, str(Path(__file__).parent))
from ranker.pipeline import score_candidate
from rank import normalise_scores

# ─────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Redrob Candidate Ranker",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# Styling
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0f0f13; }
    .stApp { background-color: #0f0f13; }
    h1, h2, h3 { color: #e8e8f0; }
    .metric-box {
        background: #1a1a2e;
        border: 1px solid #2d2d4e;
        border-radius: 10px;
        padding: 16px 20px;
        margin: 6px 0;
    }
    .score-bar-bg {
        background: #2d2d4e;
        border-radius: 4px;
        height: 8px;
        width: 100%;
    }
    .score-bar-fill {
        background: linear-gradient(90deg, #6c5ce7, #a29bfe);
        border-radius: 4px;
        height: 8px;
    }
    .tag {
        display: inline-block;
        background: #2d2d4e;
        color: #a29bfe;
        border-radius: 6px;
        padding: 2px 10px;
        margin: 2px;
        font-size: 12px;
    }
    .rank-badge {
        font-size: 28px;
        font-weight: 800;
        color: #6c5ce7;
    }
    .cand-card {
        background: #16162a;
        border: 1px solid #2d2d4e;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# Sidebar: About
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 Redrob Ranker")
    st.markdown("**India Runs Hackathon · Track 1**")
    st.markdown("---")
    st.markdown("""
**Architecture:** 5-Layer Scoring Pipeline

1. 🕵️ **Honeypot Detection** — Profile consistency checks
2. 🚫 **Hard Disqualifiers** — Consulting-only, ghost candidates
3. 🔬 **Technical Match** — Skill taxonomy + career text + assessments
4. 📈 **Career Quality** — Company type, trajectory, experience bracket
5. ⚡ **Behavioral Multiplier** — Availability, response rate, engagement
    """)
    st.markdown("---")
    st.markdown("""
**Scoring Formula:**
```
raw = 0.55×tech + 0.35×career + 0.10×avail
final = raw × behavioral_multiplier
```
    """)
    st.markdown("---")
    st.caption("No API calls · CPU only · < 5 min for 100K candidates")


# ─────────────────────────────────────────────────────────────
# Main UI
# ─────────────────────────────────────────────────────────────
st.markdown("# 🧠 Intelligent Candidate Ranker")
st.markdown("*Upload up to 100 candidate profiles to rank them for the **Senior AI Engineer** role*")
st.markdown("---")

# JD Display (collapsible)
with st.expander("📋 View Job Description: Senior AI Engineer — Redrob AI", expanded=False):
    st.markdown("""
**Role:** Senior AI Engineer (Founding Team) · Redrob AI  
**Location:** Pune / Noida · Hybrid · Open to India relocation  
**Experience:** 5–9 years (sweet spot: 6–8 years)

**Must-have:**
- Production experience with embeddings-based retrieval (sentence-transformers, BGE, E5, OpenAI embeddings)
- Vector DB / hybrid search experience (Pinecone, Weaviate, Qdrant, FAISS, OpenSearch, Elasticsearch)
- Strong Python — code quality matters
- Designed evaluation frameworks for ranking systems (NDCG, MRR, MAP, A/B testing)

**JD explicitly disqualifies:**
- Pure consulting-only career (TCS, Infosys, Wipro, etc. with no product company experience)
- Pure research (no production deployments)
- Ghost candidates (inactive 6+ months, <10% response rate)
- Computer vision / speech specialists without NLP/IR background
    """)

# ─────────────────────────────────────────────────────────────
# File upload
# ─────────────────────────────────────────────────────────────
col_upload, col_or, col_sample = st.columns([3, 0.3, 2])

with col_upload:
    uploaded = st.file_uploader(
        "Upload candidates (.json array or .jsonl)",
        type=["json", "jsonl"],
        help="JSON array of candidate objects, or one JSON object per line (JSONL format)"
    )

with col_or:
    st.markdown("<br><br><center>or</center>", unsafe_allow_html=True)

with col_sample:
    st.markdown("<br>", unsafe_allow_html=True)
    use_sample = st.button("▶ Run on built-in sample (50 candidates)", use_container_width=True)


# ─────────────────────────────────────────────────────────────
# Load candidates
# ─────────────────────────────────────────────────────────────
candidates = []

if uploaded:
    try:
        raw = uploaded.read().decode("utf-8")
        # Try JSON array first, then JSONL
        try:
            candidates = json.loads(raw)
            if not isinstance(candidates, list):
                candidates = [candidates]
        except json.JSONDecodeError:
            candidates = [json.loads(line) for line in raw.splitlines() if line.strip()]
        st.success(f"✅ Loaded **{len(candidates)}** candidates from upload")
        if len(candidates) > 100:
            st.warning("⚠️ Sandbox limit is 100 candidates. Using first 100.")
            candidates = candidates[:100]
    except Exception as e:
        st.error(f"❌ Failed to parse file: {e}")
        candidates = []

elif use_sample:
    sample_path = Path("sample_candidates.jsonl")
    if sample_path.exists():
        with open(sample_path, "r", encoding="utf-8") as f:
            candidates = [json.loads(line) for line in f if line.strip()]
        st.success(f"✅ Loaded **{len(candidates)}** built-in sample candidates")
    else:
        st.error("Sample file not found. Please upload candidates manually.")


# ─────────────────────────────────────────────────────────────
# Rank button
# ─────────────────────────────────────────────────────────────
if candidates:
    st.markdown("---")
    if st.button("🚀 Rank Candidates", type="primary", use_container_width=True):
        with st.spinner(f"Running 5-layer pipeline on {len(candidates)} candidates..."):
            t0 = time.time()
            results = [score_candidate(c) for c in candidates]
            elapsed = time.time() - t0

        # Sort and normalise
        results.sort(key=lambda r: (-r["final_score"], r["candidate_id"]))
        results_norm = normalise_scores(results)

        # Stats
        honeypots = sum(1 for r in results if r["is_honeypot"])
        disq = sum(1 for r in results if not r["is_honeypot"] and r.get("disqualifier"))
        qualified = len(results) - honeypots - disq

        st.markdown(f"### ✅ Ranked {len(results)} candidates in **{elapsed:.2f}s**")

        # Summary metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Candidates", len(results))
        m2.metric("Honeypots Detected", honeypots, delta=f"-{honeypots}" if honeypots else None, delta_color="inverse")
        m3.metric("Disqualified", disq)
        m4.metric("Qualified Pool", qualified)

        st.markdown("---")

        # ── Top 10 cards ──────────────────────────────────────────────────
        st.markdown("## 🏆 Top 10 Candidates")
        top_10 = results_norm[:10]

        for rank_idx, res in enumerate(top_10, start=1):
            cid = res["candidate_id"]
            score = res["final_score"]

            # Match back to original candidate for display data
            orig = next((c for c in candidates if c.get("candidate_id") == cid), {})
            profile = orig.get("profile", {})
            signals = orig.get("redrob_signals", {})
            tb = res.get("tech_breakdown", {})
            cb = res.get("career_breakdown", {})
            bb = res.get("behavioral_breakdown", {})

            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank_idx, f"#{rank_idx}")

            with st.container():
                st.markdown(f"""<div class='cand-card'>""", unsafe_allow_html=True)

                c1, c2, c3 = st.columns([0.08, 0.6, 0.32])
                with c1:
                    st.markdown(f"<div class='rank-badge'>{medal}</div>", unsafe_allow_html=True)
                with c2:
                    title = profile.get("current_title", "N/A")
                    company = profile.get("current_company", "")
                    location = profile.get("location", "")
                    yoe = profile.get("years_of_experience", "?")
                    st.markdown(f"**{title}** at *{company}*")
                    st.markdown(f"📍 {location} · {yoe} yrs experience")
                    # Matched skills tags
                    matched = tb.get("matched_skills", [])
                    if matched:
                        tags_html = " ".join(f"<span class='tag'>{s}</span>" for s in matched[:6])
                        st.markdown(tags_html, unsafe_allow_html=True)
                    st.markdown(f"*{res['reasoning']}*")
                with c3:
                    # Score breakdown bars
                    score_pct = int(score * 100)
                    tech_pct = int(tb.get("tech_total", 0) * 100)
                    career_pct = int(cb.get("career_total", 0) * 100)
                    behav = bb.get("behavioral_multiplier", 1.0)

                    st.markdown(f"**Final Score: {score:.4f}**")
                    st.progress(score, text=f"Overall: {score_pct}%")
                    st.progress(min(1.0, tb.get("tech_total", 0)), text=f"Tech: {tech_pct}%")
                    st.progress(min(1.0, cb.get("career_total", 0)), text=f"Career: {career_pct}%")
                    st.markdown(f"Behav. ×{behav:.2f} | RR: {signals.get('recruiter_response_rate', 0):.0%}")

                st.markdown("</div>", unsafe_allow_html=True)

        # ── Full ranked table ─────────────────────────────────────────────
        st.markdown("---")
        st.markdown("## 📊 Full Ranked Table")

        table_data = []
        for rank_idx, res in enumerate(results_norm, start=1):
            cid = res["candidate_id"]
            orig = next((c for c in candidates if c.get("candidate_id") == cid), {})
            profile = orig.get("profile", {})
            tb = res.get("tech_breakdown", {})
            cb = res.get("career_breakdown", {})
            bb = res.get("behavioral_breakdown", {})

            table_data.append({
                "Rank": rank_idx,
                "Candidate ID": cid,
                "Score": res["final_score"],
                "Title": profile.get("current_title", "?"),
                "YoE": profile.get("years_of_experience", "?"),
                "Tech Score": round(tb.get("tech_total", 0), 3),
                "Career Score": round(cb.get("career_total", 0), 3),
                "Behav ×": round(bb.get("behavioral_multiplier", 0), 2),
                "Honeypot": "⚠️" if res.get("is_honeypot") else "",
                "Disqualified": res.get("disqualifier", "") or "",
            })

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ── Download CSV ──────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("## 📥 Download Submission CSV")

        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank_idx, res in enumerate(results_norm[:100], start=1):
            writer.writerow([
                res["candidate_id"],
                rank_idx,
                f"{res['final_score']:.4f}",
                res["reasoning"],
            ])

        st.download_button(
            label="⬇️ Download submission.csv",
            data=csv_buffer.getvalue().encode("utf-8"),
            file_name="submission.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("*This CSV meets the hackathon submission spec: 100 rows, UTF-8, scores non-increasing by rank.*")

else:
    # Landing state
    st.markdown("""
    <div style='text-align:center; padding: 60px 0; color: #666;'>
        <div style='font-size: 64px;'>🧠</div>
        <h3 style='color: #888;'>Upload candidate profiles to begin ranking</h3>
        <p>Supports JSON array or JSONL format · Max 100 candidates in sandbox</p>
    </div>
    """, unsafe_allow_html=True)
