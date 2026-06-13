"""
config.py — Central configuration for the Redrob Candidate Ranker.
All weights, taxonomies, firm lists, and thresholds live here.
Tune these without touching pipeline logic.
"""

from datetime import date

# ─────────────────────────────────────────────
# Reference date for recency calculations
# ─────────────────────────────────────────────
REFERENCE_DATE = date(2026, 6, 14)

# ─────────────────────────────────────────────
# SCORING WEIGHTS  (must sum to 1.0)
# ─────────────────────────────────────────────
WEIGHT_TECH   = 0.55   # Layer 3: Technical match (dominant signal)
WEIGHT_CAREER = 0.35   # Layer 4: Career quality
WEIGHT_AVAIL  = 0.10   # Base availability component (before multiplier)

# Minimum tech score to even appear in top 100
# Candidates below this threshold are clamped to near-zero
MIN_TECH_SCORE_THRESHOLD = 0.08

# ─────────────────────────────────────────────
# LAYER 3 — TECHNICAL MATCH WEIGHTS
# ─────────────────────────────────────────────
TECH_WEIGHT_SKILLS      = 0.50  # Skill taxonomy scoring
TECH_WEIGHT_CAREER_TEXT = 0.30  # Career description semantic clusters
TECH_WEIGHT_ASSESSMENT  = 0.12  # Platform-verified assessment scores
TECH_WEIGHT_GITHUB      = 0.08  # GitHub activity

# Skill proficiency multipliers
PROFICIENCY_WEIGHT = {
    "beginner":     0.20,
    "intermediate": 0.50,
    "advanced":     0.80,
    "expert":       1.00,
}

# ─────────────────────────────────────────────
# JD SKILL TAXONOMY
# Tier 1 = Must-have  (3.0×)
# Tier 2 = Strong     (2.0×)
# Tier 3 = Nice       (1.0×)
# Tier -1 = Red-flag  (-0.5×) — wrong-domain skills that inflate keyword matches
# ─────────────────────────────────────────────
SKILL_TIERS = {
    # ---- TIER 1: Absolute must-haves ----
    "embeddings":               3.0,
    "embedding":                3.0,
    "sentence transformers":    3.0,
    "sentence-transformers":    3.0,
    "information retrieval":    3.0,
    "vector search":            3.0,
    "vector database":          3.0,
    "vector db":                3.0,
    "faiss":                    3.0,
    "pinecone":                 3.0,
    "weaviate":                 3.0,
    "qdrant":                   3.0,
    "milvus":                   3.0,
    "opensearch":               3.0,
    "elasticsearch":            3.0,
    "ranking":                  3.0,
    "ranking systems":          3.0,
    "retrieval":                3.0,
    "semantic search":          3.0,
    "python":                   3.0,
    "hybrid search":            3.0,

    # ---- TIER 2: Strong signals ----
    "rag":                      2.0,
    "retrieval augmented":      2.0,
    "llm fine-tuning":          2.0,
    "fine-tuning llms":         2.0,
    "fine tuning":              2.0,
    "lora":                     2.0,
    "qlora":                    2.0,
    "peft":                     2.0,
    "learning to rank":         2.0,
    "learning-to-rank":         2.0,
    "xgboost":                  2.0,
    "lightgbm":                 2.0,
    "ndcg":                     2.0,
    "mrr":                      2.0,
    "hugging face":             2.0,
    "hugging face transformers": 2.0,
    "huggingface":              2.0,
    "huggingface transformers": 2.0,
    "transformer":              2.0,
    "transformers":             2.0,
    "re-ranking":               2.0,
    "reranking":                2.0,
    "a/b testing":              2.0,
    "ab testing":               2.0,
    "bm25":                     2.0,
    "dense retrieval":          2.0,
    "sparse retrieval":         2.0,

    # ---- TIER 3: Nice to have ----
    "nlp":                      1.0,
    "natural language processing": 1.0,
    "machine learning":         1.0,
    "ml":                       1.0,
    "mlops":                    1.0,
    "recommendation systems":   1.0,
    "recommendation":           1.0,
    "mlflow":                   1.0,
    "pytorch":                  1.0,
    "tensorflow":               1.0,
    "scikit-learn":             1.0,
    "sklearn":                  1.0,
    "feature engineering":      1.0,
    "distributed systems":      1.0,
    "kafka":                    1.0,
    "spark":                    1.0,
    "airflow":                  1.0,
    "docker":                   1.0,
    "kubernetes":               1.0,
    "aws":                      1.0,
    "gcp":                      1.0,
    "azure":                    1.0,
    "bentoml":                  1.0,
    "weights & biases":         1.0,
    "wandb":                    1.0,
    "statistical modeling":     1.0,
    "data pipelines":           1.0,
    "databricks":               1.0,

    # ---- TIER -1: Red-flag skills (wrong domain inflation) ----
    "photoshop":               -0.5,
    "marketing":               -0.5,
    "seo":                     -0.5,
    "excel":                   -0.5,
    "accounting":              -0.5,
    "six sigma":               -0.5,
    "content writing":         -0.5,
    "sales":                   -0.5,
    "powerpoint":              -0.5,
    "tailwind":                -0.3,
}

# ─────────────────────────────────────────────
# SEMANTIC CLUSTER KEYWORDS (career text matching)
# Each cluster has a name, keywords, and weight
# ─────────────────────────────────────────────
SEMANTIC_CLUSTERS = [
    {
        "name": "retrieval_search",
        "weight": 3.0,
        "keywords": [
            "retrieval", "vector search", "hybrid search", "dense retrieval",
            "bm25", "elasticsearch", "opensearch", "semantic search",
            "information retrieval", "embedding-based", "embedding based",
            "recall", "search infrastructure", "re-ranking", "reranking",
            "ranking system", "candidate ranking", "search engine",
            "faiss", "pinecone", "qdrant", "weaviate", "milvus",
        ]
    },
    {
        "name": "production_ml",
        "weight": 2.5,
        "keywords": [
            "deployed to production", "production ml", "production model",
            "shipped ml", "ml system", "ai system in production",
            "model serving", "ml pipeline", "a/b test", "a/b testing",
            "online metrics", "ml inference", "model inference",
            "real users at scale", "production ranking", "production search",
            "embedding pipeline", "vector index", "vector store",
        ]
    },
    {
        "name": "eval_frameworks",
        "weight": 2.5,
        "keywords": [
            "ndcg", "mrr", "map", "mean average precision",
            "offline evaluation", "online evaluation", "benchmark",
            "relevance labeling", "click-through", "offline-online correlation",
            "eval framework", "evaluation framework", "relevance judgment",
            "recall@", "precision@", "hit rate",
        ]
    },
    {
        "name": "learning_to_rank",
        "weight": 2.0,
        "keywords": [
            "learning to rank", "learning-to-rank", "ltr",
            "xgboost", "lightgbm", "pointwise", "pairwise", "listwise",
            "ranking model", "ranking signal", "feature ranking",
            "gradient boosted", "gradient boosting", "ranker",
        ]
    },
    {
        "name": "product_company_shipping",
        "weight": 2.0,
        "keywords": [
            "product company", "shipped", "launched", "revenue",
            "conversion", "improved by", "grew by", "reduced by",
            "end-to-end", "real users", "user engagement", "dau", "mau",
            "increased", "decreased latency", "improved precision",
        ]
    },
    {
        "name": "llm_and_embeddings",
        "weight": 1.5,
        "keywords": [
            "llm", "large language model", "gpt", "embedding",
            "sentence transformer", "hugging face", "transformers",
            "fine-tun", "lora", "qlora", "rag", "retrieval augmented",
            "foundation model", "language model",
        ]
    },
    {
        "name": "nlp_ml_general",
        "weight": 1.0,
        "keywords": [
            "nlp", "natural language", "machine learning", "deep learning",
            "neural network", "recommendation", "classification",
            "regression", "feature engineering", "model training",
        ]
    },
]

# ─────────────────────────────────────────────
# CONSULTING FIRMS (pure-consulting disqualifier)
# ─────────────────────────────────────────────
PURE_CONSULTING_FIRMS = {
    "tcs", "tata consultancy", "infosys", "wipro", "accenture",
    "cognizant", "capgemini", "hcl", "hcl technologies", "tech mahindra",
    "mphasis", "hexaware", "l&t infotech", "ltimindtree", "lti",
    "mindtree",  # medium-tier IT services
    "niit technologies", "mastech", "kpit", "cyient", "zensar",
    "firstsource", "minda", "birlasoft", "coforge",
}

# ─────────────────────────────────────────────
# KNOWN PRODUCT COMPANIES (career quality boost)
# ─────────────────────────────────────────────
PRODUCT_COMPANIES = {
    # Indian unicorns & product cos
    "swiggy", "zomato", "flipkart", "ola", "paytm", "cred", "razorpay",
    "phonepe", "meesho", "dream11", "freshworks", "zoho", "zerodha",
    "groww", "upstox", "slice", "jupiter", "fi", "niyo", "mobikwik",
    "policybazaar", "naukri", "info edge", "infoedge", "sharechat",
    "moj", "dailyhunt", "verse innovation", "byju", "unacademy",
    "vedantu", "leadschool", "classplus", "doubtnut", "physicswallah",
    "licious", "bigbasket", "blinkit", "dunzo", "rapido", "porter",
    "loadshare", "shiprocket", "delhivery", "blackbuck",
    "chargebee", "leadsquared", "clevertap", "moengage", "webengage",
    "browserstack", "postman", "hasura", "appsmith", "directi",
    "mad street den", "mad street", "sarvam", "sarvam ai",
    "uber", "google", "microsoft", "amazon", "meta", "apple",
    "netflix", "airbnb", "stripe", "shopify", "atlassian",
    "salesforce", "servicenow", "workday", "databricks", "snowflake",
    "confluent", "dbt labs", "hugging face", "openai", "anthropic",
    "cohere", "mistral", "stability ai",
}

# ─────────────────────────────────────────────
# PURE RESEARCH / ACADEMIC INSTITUTIONS
# ─────────────────────────────────────────────
RESEARCH_INSTITUTIONS = {
    "iit", "iisc", "iim", "nit", "drdo", "barc", "isro",
    "tifr", "iiit", "bits pilani", "bits", "stanford", "mit",
    "university", "college", "institute of technology", "research lab",
    "academia", "postdoc", "phd research",
}

# ─────────────────────────────────────────────
# EXPERIENCE BRACKET SCORING
# ─────────────────────────────────────────────
def experience_score(yoe: float) -> float:
    """JD sweet spot: 5-9 years, ideal 6-8."""
    if yoe < 2:    return 0.05
    if yoe < 3:    return 0.20
    if yoe < 4:    return 0.40
    if yoe < 5:    return 0.60
    if yoe <= 7:   return 1.00   # sweet spot
    if yoe <= 9:   return 0.90
    if yoe <= 12:  return 0.70
    if yoe <= 15:  return 0.55
    return 0.40

# ─────────────────────────────────────────────
# LOCATION SCORING
# ─────────────────────────────────────────────
PREFERRED_LOCATIONS = {
    "pune", "noida", "delhi", "gurugram", "gurgaon", "hyderabad",
    "mumbai", "bangalore", "bengaluru", "delhi ncr", "ncr",
    "new delhi", "greater noida",
}

def location_score(location: str, country: str, willing_to_relocate: bool) -> float:
    loc_lower = (location or "").lower()
    country_lower = (country or "").lower()

    if country_lower not in ("india", "in"):
        return 0.55 if willing_to_relocate else 0.15

    for pref in PREFERRED_LOCATIONS:
        if pref in loc_lower:
            return 1.00

    # Other Indian city
    return 0.85 if willing_to_relocate else 0.65

# ─────────────────────────────────────────────
# NOTICE PERIOD SCORING
# ─────────────────────────────────────────────
def notice_score(days: int) -> float:
    if days <= 15:   return 1.00
    if days <= 30:   return 0.95
    if days <= 45:   return 0.85
    if days <= 60:   return 0.75
    if days <= 90:   return 0.60
    if days <= 120:  return 0.45
    return 0.30

# ─────────────────────────────────────────────
# EDUCATION TIER SCORING  (small weight)
# ─────────────────────────────────────────────
EDU_TIER_SCORE = {
    "tier_1": 1.0,
    "tier_2": 0.80,
    "tier_3": 0.60,
    "tier_4": 0.40,
    "unknown": 0.50,
}
