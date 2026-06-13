<div align="center">

<img src="https://img.shields.io/badge/Redrob-India%20Runs%20Hackathon-6c5ce7?style=for-the-badge&labelColor=0f0f13" />
<img src="https://img.shields.io/badge/Track%201-Data%20%26%20AI%20Challenge-a29bfe?style=for-the-badge&labelColor=0f0f13" />
<img src="https://img.shields.io/badge/Python-3.10%2B-3776ab?style=for-the-badge&logo=python&logoColor=white&labelColor=0f0f13" />
<img src="https://img.shields.io/badge/CPU%20Only-No%20GPU%20Required-00b894?style=for-the-badge&labelColor=0f0f13" />
<img src="https://img.shields.io/badge/Runtime-~100s%20for%20100K-fd79a8?style=for-the-badge&labelColor=0f0f13" />

# 🧠 Redrob Candidate Ranker

### *Intelligent Candidate Discovery & Ranking System*
#### India Runs Hackathon · Track 1: The Data & AI Challenge

> **Reproduce command:**
> ```bash
> python rank.py --candidates ./candidates.jsonl --out ./submission.csv
> ```

[📊 View Submission](#results) · [🏗️ Architecture](#architecture) · [⚡ Quick Start](#quick-start) · [🧪 Sandbox](#sandbox)

</div>

---

## 🎯 The Problem

Recruiters searching for a **Senior AI Engineer** face two failure modes:

| Failure | Why it happens |
|---|---|
| **Keyword inflation** | A Marketing Manager lists "Pinecone" and "RAG" in skills → floats to the top |
| **Ghost candidates** | A perfect-on-paper engineer hasn't logged in for 7 months and ignores recruiter messages → wastes everyone's time |

Most ranking systems fail at both. This one doesn't.

---

## 🏗️ Architecture

A **5-layer deterministic scoring pipeline** — no LLM API calls, no GPU, fully reproducible on CPU in under 2 minutes for 100,000 candidates.

```
candidates.jsonl  (100,000 profiles)
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  LAYER 1 · Honeypot Detection                         │
│  Cross-validates internal profile consistency          │
│  → 7,580 impossible profiles caught & eliminated      │
└──────────────────────────┬────────────────────────────┘
                           ▼
┌───────────────────────────────────────────────────────┐
│  LAYER 2 · Minimum Technical Relevance Gate           │
│  Zero-relevance candidates (Accountants, Civil        │
│  Engineers with no ML signals) → score ≈ 0            │
└──────────────────────────┬────────────────────────────┘
                           ▼
┌───────────────────────────────────────────────────────┐
│  LAYER 3 · Technical Match Score          (55% weight)│
│                                                       │
│  ├─ Skill Taxonomy (Tier 1/2/3/−1)       50%          │
│  │   Tier 1 (3×): FAISS, Pinecone, embeddings,        │
│  │               sentence-transformers, retrieval      │
│  │   Tier 2 (2×): RAG, LoRA, learning-to-rank, NDCG   │
│  │   Tier −1 (−0.5×): Photoshop, Marketing, SEO       │
│  │                                                     │
│  ├─ Semantic Cluster Text Matching        30%          │
│  │   7 clusters over career descriptions:              │
│  │   retrieval_search, production_ml, eval_frameworks, │
│  │   learning_to_rank, product_shipping, llm_embeddings│
│  │                                                     │
│  ├─ Platform Assessment Scores            12%          │
│  │   Verified Redrob skill test results               │
│  │                                                     │
│  └─ GitHub Activity Score                 8%           │
└──────────────────────────┬────────────────────────────┘
                           ▼
┌───────────────────────────────────────────────────────┐
│  LAYER 4 · Career Quality Score           (35% weight)│
│                                                       │
│  ├─ Company Type          30%   (product 1.0× vs      │
│  │                               consulting 0.25×)    │
│  ├─ Experience Bracket    25%   (sweet spot: 5–7 yrs) │
│  ├─ Trajectory Stability  15%   (avg tenure < 18mo    │
│  │                               penalized)           │
│  ├─ Location              15%   (Pune/Noida/Hyd = 1.0)│
│  ├─ Education Tier        10%   (Tier 1–4)            │
│  └─ Notice Period          5%   (sub-30d bonus)       │
└──────────────────────────┬────────────────────────────┘
                           ▼
┌───────────────────────────────────────────────────────┐
│  LAYER 5 · Behavioral Signal Multiplier  (0.05–1.50×) │
│                                                       │
│  open_to_work · last_active_date · response_rate      │
│  avg_response_time · notice_period · completeness     │
│  verified_email/phone · interview_completion_rate     │
│  recruiter_saves_30d                                  │
└──────────────────────────┬────────────────────────────┘
                           ▼
         final = (0.55×tech + 0.35×career + 0.10×avail)
                         × behavioral_multiplier
                           │
                           ▼
                    Top 100 · submission.csv
```

---

## 📊 Results

Scored **100,000 candidates** from the Redrob dataset.

| Metric | Value |
|---|---|
| Total candidates scored | 100,000 |
| Honeypots detected & excluded | 7,580 |
| Below tech threshold | 72,944 |
| Qualified pool | ~19,476 |
| Runtime (CPU, no GPU) | **97.7 seconds** |
| Validation | ✅ `Submission is valid` |

### Top 10 Ranked Candidates

| Rank | Title | Company | Key Signals |
|---|---|---|---|
| 🥇 1 | AI Engineer | Microsoft | Sentence Transformers (85.8/100 assessed), Python, Vector Search; RR 0.81 |
| 🥈 2 | Rec Systems Engineer | CRED | QLoRA, FAISS, HuggingFace; RR 0.90; 30d notice |
| 🥉 3 | Senior AI Engineer | Netflix | LoRA (86.7/100), Weaviate, PEFT (85.6/100); GitHub 82.8 |
| 4 | Senior NLP Engineer | Niramai | OpenSearch, FAISS, PEFT; RR 0.89; **15d notice** |
| 5 | Junior ML Engineer | Aganitha | Information Retrieval (83.5/100 assessed), Semantic Search, Qdrant |
| 6 | Senior Applied Scientist | Sarvam AI | Vector Search (92.7/100), Uber Search & Ranking background; **0d notice** |
| 7 | Senior ML Engineer | Genpact AI | Elasticsearch, LinkedIn career; RR 0.88 |
| 8 | Senior ML Engineer | Flipkart | Uber + Rephrase.ai career; RR 0.87; 30d notice |
| 9 | Machine Learning Engineer | Netflix | FAISS (70.8/100), LoRA, Milvus; RR 0.84; **15d notice** |
| 10 | Search Engineer | Sarvam AI | Milvus, Weaviate, Freshworks + Apple career; RR 0.94 |

---

## ⚡ Quick Start

### 1. Clone & install
```bash
git clone https://github.com/swaraj3092/redrob-ranker.git
cd redrob-ranker
pip install -r requirements.txt
```

> **Note:** The ranker itself has **zero external dependencies** — pure Python stdlib.  
> `requirements.txt` only contains `streamlit` and `pandas` for the sandbox UI.

### 2. Download the dataset
Get `candidates.jsonl` from the [hackathon bundle](https://hack2skill.com/redrob) and place it in the repo root.

### 3. Run the ranker
```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

### 4. Validate output
```bash
python validate_submission.py submission.csv
# → Submission is valid.
```

### 5. Run with built-in validation
```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv --validate
```

---

## 🧪 Sandbox

A Streamlit app for interactive exploration — upload up to 100 candidate profiles, rank them, and download the CSV.

```bash
streamlit run app.py
```

Live demo: [🤗 HuggingFace Spaces](https://huggingface.co/spaces/swaraj3092/redrob-ranker)

---

## 📁 Repository Structure

```
redrob-ranker/
│
├── rank.py                      # ← Entry point. Reproduce command lives here.
├── app.py                       # Streamlit sandbox UI
├── requirements.txt             # streamlit, pandas
├── submission.csv               # Final submission (top 100 ranked candidates)
├── submission_metadata.yaml     # Hackathon portal metadata
├── validate_submission.py       # Official validator (unmodified from bundle)
├── sample_candidates.jsonl      # 50-profile sample for sandbox testing
│
└── ranker/                      # Core ranking package
    ├── __init__.py
    ├── config.py                # All weights, taxonomies, firm lists (tunable)
    ├── honeypot_detector.py     # Layer 1: Internal consistency checks
    ├── tech_scorer.py           # Layer 3: Skills + semantic clusters + GitHub
    ├── career_scorer.py         # Layer 4: Company type, experience, location
    ├── behavioral_scorer.py     # Layer 5: Availability × engagement multiplier
    ├── reasoning_engine.py      # Auto-generate honest, specific reasoning
    └── pipeline.py              # Master orchestrator (all layers)
```

---

## 🕵️ Honeypot Detection

The dataset contains ~80 candidates with subtly impossible profiles. Our cross-validation catches them **naturally** — no special-casing.

| Check | Example |
|---|---|
| YoE vs career duration | Claims 10 yrs experience but only 7 yrs of career history |
| Expert skill, 0 months used | `proficiency: "expert"`, `duration_months: 0` |
| 9+ simultaneous expert skills | Implausibly broad skill mastery |
| Career dates vs stated YoE | Role started before career could have begun |
| Duration vs start/end dates | Stated 60 months, but dates imply 12 months |
| Metric contradiction | `offer_acceptance_rate > 0` with `interview_completion_rate = 0` |

Detected honeypots → `score = 0.0` → never enter top 100.

---

## 🚫 Hard Disqualifiers

The JD explicitly names these anti-patterns. We penalize them:

| Disqualifier | Penalty |
|---|---|
| Pure consulting career (TCS/Infosys/Wipro only, no product co.) | `score × 0.04` |
| Ghost candidate (inactive 300d + RR < 5% + not open to work) | `score × 0.04` |
| Zero technical relevance (tech_score < 0.08) | Clamped to near-zero |

---

## 🎯 Why This Ranking Works

The JD contains a hidden note to hackathon participants:

> *"The right answer involves reasoning about the gap between what the JD says and what the JD means. A candidate who has all the AI keywords listed as skills but whose title is 'Marketing Manager' is not a fit, no matter how perfect their skill list looks."*

Our system handles exactly this:

- **Skill tier weighting** with duration trust — a "beginner" at Pinecone for 1 month ≠ "expert" for 5 years
- **Career text semantic clustering** — detects that a candidate "built a recommendation system at a product company" even if they never wrote the word "RAG"
- **Company quality scoring** — distinguishes Swiggy (product) from TCS (consulting) via industry + company name matching
- **Behavioral multiplier** — a candidate with 0.90 response rate and 15d notice is worth 3× as much as an identical candidate who's been inactive for 4 months

---

## 👥 Team

| Name | Role |
|---|---|
| Swaraj Kumar Behera | ML Engineer / Team Lead |
| Prajakta Kuila | ML Engineer |

**Team:** Trade Mark · India Runs Hackathon 2026

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.
