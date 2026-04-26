"""
utils/ui.py
============
All CSS injection, header, sidebar, and empty-state rendering.
"""

import streamlit as st
import os


# ─── CSS ──────────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
<style>
/* ── Google Font ──────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Root variables ───────────────────────────────────────────────────────── */
:root {
    --primary:      #4f46e5;
    --primary-light:#6366f1;
    --primary-dark: #3730a3;
    --success:      #22c55e;
    --warning:      #f59e0b;
    --danger:       #ef4444;
    --bg:           #f8fafc;
    --surface:      #ffffff;
    --border:       #e2e8f0;
    --text:         #0f172a;
    --text-muted:   #64748b;
    --radius:       12px;
    --shadow:       0 1px 3px rgba(0,0,0,.08), 0 4px 16px rgba(0,0,0,.06);
    --shadow-lg:    0 4px 24px rgba(0,0,0,.10), 0 8px 40px rgba(0,0,0,.06);
}

/* ── Global reset ─────────────────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* ── Streamlit chrome cleanup ─────────────────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
.block-container {
    padding: 0 2rem 2rem 2rem !important;
    max-width: 1400px !important;
}

/* ── App header ───────────────────────────────────────────────────────────── */
.app-header {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
    border-radius: 0 0 var(--radius) var(--radius);
    padding: 2rem 2.5rem;
    margin: 0 -2rem 2rem -2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: var(--shadow-lg);
}
.app-header-left { display: flex; align-items: center; gap: 1.2rem; }
.app-logo {
    width: 52px; height: 52px;
    background: rgba(255,255,255,.15);
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.8rem; backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,.2);
}
.app-title { color: #ffffff; font-size: 1.6rem; font-weight: 800; letter-spacing: -0.02em; margin: 0; }
.app-subtitle { color: rgba(255,255,255,.65); font-size: 0.85rem; font-weight: 400; margin: 2px 0 0 0; }
.header-badge {
    background: rgba(255,255,255,.15);
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.35rem 0.85rem;
    border-radius: 50px;
    border: 1px solid rgba(255,255,255,.25);
    letter-spacing: 0.04em;
}

/* ── Upload section ───────────────────────────────────────────────────────── */
.upload-section {
    margin-bottom: 1.5rem;
}
[data-testid="stFileUploader"] {
    border: 2px dashed var(--primary-light) !important;
    border-radius: var(--radius) !important;
    background: rgba(79,70,229,.04) !important;
    padding: 1.5rem !important;
    transition: all 0.2s ease;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--primary) !important;
    background: rgba(79,70,229,.08) !important;
}

/* ── Panel card ───────────────────────────────────────────────────────────── */
.panel-card {
    background: var(--surface);
    border-radius: var(--radius);
    padding: 1.5rem;
    box-shadow: var(--shadow);
    border: 1px solid var(--border);
    margin-bottom: 1rem;
}

/* ── Risk score card ──────────────────────────────────────────────────────── */
.risk-score-card {
    border-radius: var(--radius);
    padding: 1.25rem 1.5rem;
    margin: 1rem 0 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
}
.risk-score-label { font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); }
.risk-score-value { font-size: 3rem; font-weight: 800; line-height: 1; letter-spacing: -0.04em; }
.risk-score-max { font-size: 1.1rem; font-weight: 500; color: var(--text-muted); }
.risk-level-badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.2rem 0.75rem;
    border-radius: 50px;
    letter-spacing: 0.08em;
    width: fit-content;
}

/* ── Success banner ───────────────────────────────────────────────────────── */
.success-banner {
    background: linear-gradient(90deg, #dcfce7, #f0fdf4);
    border: 1px solid #86efac;
    border-radius: var(--radius);
    padding: 0.9rem 1.25rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    color: #166534;
    font-weight: 500;
    font-size: 0.9rem;
}
.success-icon { font-size: 1.1rem; }

/* ── Detail cards ─────────────────────────────────────────────────────────── */
.detail-card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.75rem;
}
.detail-label { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); margin-bottom: 0.3rem; }
.detail-value { font-size: 0.95rem; font-weight: 600; color: var(--text); }

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--bg);
    padding: 4px;
    border-radius: 10px;
    border: 1px solid var(--border);
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    padding: 0.5rem 1.1rem !important;
    color: var(--text-muted) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: var(--primary) !important;
    color: white !important;
}

/* ── Summary box ──────────────────────────────────────────────────────────── */
.summary-box {
    background: linear-gradient(135deg, #f8fafc, #f1f5f9);
    border-left: 4px solid var(--primary);
    border-radius: 0 var(--radius) var(--radius) 0;
    padding: 1.25rem 1.5rem;
    font-size: 0.95rem;
    line-height: 1.7;
    color: var(--text);
    margin-bottom: 1.5rem;
}

/* ── Obligation items ─────────────────────────────────────────────────────── */
.obligation-item {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    margin-bottom: 0.4rem;
    font-size: 0.88rem;
    color: var(--text);
}

/* ── Party chips ──────────────────────────────────────────────────────────── */
.party-chip {
    display: inline-block;
    background: #ede9fe;
    color: #5b21b6;
    border: 1px solid #c4b5fd;
    border-radius: 50px;
    padding: 0.3rem 0.9rem;
    font-size: 0.85rem;
    font-weight: 600;
    margin: 0.25rem 0.25rem 0.25rem 0;
}

/* ── Recommendation chips ─────────────────────────────────────────────────── */
.recommendation-chip {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
    font-size: 0.85rem;
    line-height: 1.5;
}
.rec-number {
    display: inline-block;
    background: var(--primary);
    color: white;
    width: 20px; height: 20px;
    border-radius: 50%;
    text-align: center;
    line-height: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    margin-right: 0.5rem;
}

/* ── Term detail rows ─────────────────────────────────────────────────────── */
.term-detail-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 0.65rem 0;
    border-bottom: 1px solid var(--border);
    gap: 1rem;
}
.term-name { font-weight: 600; font-size: 0.88rem; color: var(--text); min-width: 180px; }
.term-value { font-size: 0.88rem; color: var(--text-muted); text-align: right; }

/* ── Q&A bubbles ──────────────────────────────────────────────────────────── */
.qa-hint {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: 0.65rem 1rem;
    font-size: 0.85rem;
    color: #1e40af;
    margin-bottom: 1rem;
}
.qa-bubble-user {
    background: #ede9fe;
    border-radius: 12px 12px 4px 12px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    color: #4c1d95;
    border: 1px solid #c4b5fd;
}
.qa-bubble-ai {
    background: var(--surface);
    border-radius: 4px 12px 12px 12px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
    color: var(--text);
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
}
.qa-role { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); }

/* ── Disclaimer ───────────────────────────────────────────────────────────── */
.disclaimer {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: var(--radius);
    padding: 0.9rem 1.25rem;
    font-size: 0.82rem;
    color: #78350f;
    margin-top: 1.5rem;
    line-height: 1.6;
}

/* ── Empty state ──────────────────────────────────────────────────────────── */
.empty-state {
    background: var(--surface);
    border: 2px dashed var(--border);
    border-radius: 16px;
    padding: 4rem 2rem;
    text-align: center;
    margin: 2rem 0;
}
.empty-state-icon { font-size: 4rem; margin-bottom: 1rem; }
.empty-state-title { font-size: 1.5rem; font-weight: 700; color: var(--text); margin-bottom: 0.5rem; }
.empty-state-subtitle { font-size: 0.95rem; color: var(--text-muted); max-width: 500px; margin: 0 auto 2rem; line-height: 1.6; }

/* ── Feature grid ─────────────────────────────────────────────────────────── */
.feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 2rem; text-align: left; }
.feature-card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.1rem 1.25rem;
}
.feature-icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
.feature-title { font-size: 0.88rem; font-weight: 700; color: var(--text); margin-bottom: 0.25rem; }
.feature-desc { font-size: 0.78rem; color: var(--text-muted); line-height: 1.5; }

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #1e1b4b !important;
}
[data-testid="stSidebar"] * { color: rgba(255,255,255,.85) !important; }
[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,.1) !important;
    border: 1px solid rgba(255,255,255,.2) !important;
    color: white !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {
    color: white !important;
}
[data-testid="stSidebar"] .stMarkdown p { color: rgba(255,255,255,.7) !important; font-size: 0.85rem; }

/* ── Metric cards ─────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.75rem 1rem !important;
}
[data-testid="stMetricLabel"] { font-size: 0.78rem !important; font-weight: 600 !important; color: var(--text-muted) !important; }
[data-testid="stMetricValue"] { font-size: 1.4rem !important; font-weight: 800 !important; }

/* ── Progress bar ─────────────────────────────────────────────────────────── */
[data-testid="stProgressBar"] > div {
    border-radius: 50px !important;
    height: 10px !important;
}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"] {
    background: var(--primary) !important;
    border-color: var(--primary) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--primary-dark) !important;
    border-color: var(--primary-dark) !important;
}
.stDownloadButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    width: 100% !important;
}

/* ── Dataframe ────────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    overflow: hidden;
}

/* ── Expander ─────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    margin-bottom: 0.5rem;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    font-size: 0.92rem !important;
}

/* ── Scrollbar ────────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 50px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
</style>
"""


def inject_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_header():
    st.markdown("""
    <div class="app-header">
        <div class="app-header-left">
            <div class="app-logo">🔐</div>
            <div>
                <p class="app-title">ContractAI</p>
                <p class="app-subtitle">Enterprise Contract Analyzer &amp; Risk Intelligence Platform</p>
            </div>
        </div>
        <div class="header-badge">BETA</div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar() -> str:
    """Render the sidebar and return the API key (if provided)."""
    with st.sidebar:
        st.markdown("## 🔐 ContractAI")
        st.markdown("*Enterprise Contract Intelligence*")
        st.markdown("---")

        st.markdown("### 🔑 OpenAI API Key")
        st.markdown("Optional — enables LLM-enhanced analysis & Q&A.")
        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder="sk-…",
            label_visibility="collapsed",
            key="openai_key",
        )

        env_key = os.environ.get("OPENAI_API_KEY", "")
        final_key = api_key.strip() or env_key.strip()

        if final_key:
            st.success("✅ LLM mode active")
        else:
            st.info("ℹ️ Heuristic mode (no API key)")

        st.markdown("---")
        st.markdown("### ⚙️ Analysis Mode")
        mode_label = "🤖 LLM-Enhanced" if final_key else "📐 Rule-Based"
        st.markdown(f"**Current mode:** {mode_label}")

        st.markdown("---")
        st.markdown("### 📊 Risk Score Guide")
        st.markdown("""
        | Score | Level |
        |-------|-------|
        | 0–29  | 🟢 Low |
        | 30–59 | 🟡 Medium |
        | 60–84 | 🟠 High |
        | 85+   | 🔴 Critical |
        """)

        st.markdown("---")
        st.markdown("### 💬 Example Questions")
        questions = [
            "What is the notice period?",
            "Is there unlimited liability?",
            "When does this contract expire?",
            "Are there auto-renewal clauses?",
            "What are the payment terms?",
            "Which clause is most risky?",
        ]
        for q in questions:
            st.markdown(f"- *{q}*")

        st.markdown("---")
        st.markdown("### 📋 Supported Clause Types")
        clauses = [
            "Termination", "Payment Terms", "Liability Cap",
            "Indemnification", "Confidentiality", "Governing Law",
            "Dispute Resolution", "Auto-Renewal", "Penalties",
            "Warranties", "IP Ownership", "Force Majeure",
        ]
        for c in clauses:
            st.markdown(f"- {c}")

        st.markdown("---")
        st.markdown(
            "<small style='color:rgba(255,255,255,.4)'>ContractAI v1.0 · Not legal advice</small>",
            unsafe_allow_html=True
        )

    return final_key


def render_empty_state():
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">📂</div>
        <div class="empty-state-title">Upload a Contract to Begin</div>
        <div class="empty-state-subtitle">
            Drop a PDF contract above to instantly receive a comprehensive risk analysis, 
            key term extraction, critical date identification, and an interactive Q&A assistant.
        </div>
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">⚠️</div>
                <div class="feature-title">Risk Scoring</div>
                <div class="feature-desc">0–100 risk score with severity breakdown and clause-level explanations.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔑</div>
                <div class="feature-title">Key Term Extraction</div>
                <div class="feature-desc">Dates, parties, payment terms, governing law, and more — automatically extracted.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💬</div>
                <div class="feature-title">Contract Q&amp;A</div>
                <div class="feature-desc">Ask any question about your contract and get instant answers grounded in the text.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📥</div>
                <div class="feature-title">Exportable Reports</div>
                <div class="feature-desc">Download structured JSON and PDF reports for sharing with your legal team.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📅</div>
                <div class="feature-title">Critical Dates</div>
                <div class="feature-desc">Effective dates, expiry, renewal windows — never miss a deadline again.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🏛️</div>
                <div class="feature-title">Jurisdiction Analysis</div>
                <div class="feature-desc">Governing law, jurisdiction, and dispute resolution clauses identified.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
