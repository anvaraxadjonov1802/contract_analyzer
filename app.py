"""
Enterprise Contract Analyzer & Risk Agent
==========================================
Main Streamlit application entry point.
"""

import streamlit as st
import json
import time
import os
from datetime import datetime
from io import BytesIO

# ─── Page Config (must be first) ─────────────────────────────────────────────
st.set_page_config(
    page_title="ContractAI — Enterprise Contract Analyzer",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Enterprise Contract Analyzer & Risk Agent — Built for legal teams.",
    },
)

# ─── Internal imports ─────────────────────────────────────────────────────────
from utils.ui import inject_css, render_header, render_sidebar, render_empty_state
from utils.helpers import extract_pdf_text, get_page_count, pdf_to_base64_preview
from analysis.extractor import ContractExtractor
from analysis.risk_engine import RiskEngine
from analysis.qna import ContractQnA
from analysis.report_builder import build_json_report, build_pdf_report

# ─── Inject global CSS ────────────────────────────────────────────────────────
inject_css()

# ─── Session State Defaults ───────────────────────────────────────────────────
defaults = {
    "analysis_done": False,
    "extracted_text": "",
    "analysis": {},
    "risks": [],
    "key_terms": {},
    "risk_score": 0,
    "risk_level": "Low",
    "summary": "",
    "qa_history": [],
    "pdf_bytes": None,
    "filename": "",
    "page_count": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── Sidebar ──────────────────────────────────────────────────────────────────
api_key = render_sidebar()

# ─── Header ───────────────────────────────────────────────────────────────────
render_header()

# ─── File Upload ──────────────────────────────────────────────────────────────
st.markdown('<div class="upload-section">', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    "Upload your contract PDF",
    type=["pdf"],
    help="Upload a PDF contract to begin analysis. Maximum file size: 50MB.",
    label_visibility="collapsed",
)
st.markdown("</div>", unsafe_allow_html=True)

if uploaded_file is None:
    render_empty_state()
    st.stop()

# ─── Process uploaded file ────────────────────────────────────────────────────
if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    new_file = uploaded_file.name != st.session_state.get("filename", "")

    if new_file or not st.session_state.analysis_done:
        st.session_state.pdf_bytes = file_bytes
        st.session_state.filename = uploaded_file.name
        st.session_state.analysis_done = False
        st.session_state.qa_history = []

        # ── Analysis pipeline ────────────────────────────────────────────────
        with st.status("🔍 Analyzing contract…", expanded=True) as status:
            st.write("📄 Extracting text from PDF…")
            time.sleep(0.3)
            text = extract_pdf_text(file_bytes)
            pages = get_page_count(file_bytes)
            st.session_state.extracted_text = text
            st.session_state.page_count = pages

            if not text.strip():
                st.error("❌ Could not extract text from this PDF. It may be scanned/image-based.")
                st.stop()

            st.write("🧠 Running contract extraction…")
            time.sleep(0.3)
            extractor = ContractExtractor(text, api_key=api_key)
            extraction = extractor.extract_all()
            st.session_state.analysis = extraction

            st.write("⚠️ Scoring risks…")
            time.sleep(0.3)
            engine = RiskEngine(text, extraction)
            risks, score, level = engine.evaluate()
            st.session_state.risks = risks
            st.session_state.risk_score = score
            st.session_state.risk_level = level

            st.write("📊 Preparing insights…")
            time.sleep(0.2)
            st.session_state.key_terms = extraction.get("key_terms", {})
            st.session_state.summary = extraction.get("summary", "")
            st.session_state.analysis_done = True
            status.update(label="✅ Analysis complete!", state="complete", expanded=False)

# ─── Main layout ──────────────────────────────────────────────────────────────
if st.session_state.analysis_done:
    analysis = st.session_state.analysis
    risks = st.session_state.risks
    score = st.session_state.risk_score
    level = st.session_state.risk_level
    key_terms = st.session_state.key_terms
    text = st.session_state.extracted_text
    pages = st.session_state.page_count

    # ── Success banner ───────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="success-banner">
        <span class="success-icon">✅</span>
        <span>Analysis completed for <strong>{st.session_state.filename}</strong> — 
        {pages} page{"s" if pages != 1 else ""} · 
        {len(text.split())} words · 
        Generated {datetime.now().strftime("%b %d, %Y %H:%M")}</span>
    </div>
    """, unsafe_allow_html=True)

    left_col, right_col = st.columns([1, 2], gap="large")

    # ── LEFT: PDF Preview ────────────────────────────────────────────────────
    with left_col:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown("### 📄 Document Preview")

        # Metric summary strip
        red_flag_count = len([r for r in risks if r["severity"] in ("High", "Critical")])
        dates_count = len([v for v in key_terms.values()
                           if any(kw in str(k).lower() for k, v in key_terms.items()
                                  for kw in ["date", "expir", "terminat"]) if v and v != "Not found"])
        critical_dates = analysis.get("critical_dates", [])

        c1, c2, c3 = st.columns(3)
        c1.metric("📑 Pages", pages)
        c2.metric("🚩 Red Flags", red_flag_count)
        c3.metric("📅 Dates", len(critical_dates))

        # Risk score card
        # app.py ichida risk score qismi (taxminan 160-qatorlar)

        score_color = "#22c55e" if level == "Low" else "#f59e0b" if level == "Medium" else "#ef4444"

        st.markdown(f"""
        <div class="panel-card" style="text-align: center;">
            <p class="risk-label">Risk Assessment</p>
            <div class="risk-circle" style="border-color: {score_color}44; color: {score_color};">
                <div class="risk-value">{score}</div>
                <div style="font-size: 0.9rem; font-weight: 600;">{level.upper()}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(score / 100)

        pdf_preview = pdf_to_base64_preview(st.session_state.pdf_bytes)
        if pdf_preview:
            st.markdown(
                f'''
                <iframe 
                    src="{pdf_preview}" 
                    width="100%" 
                    height="720" 
                    style="border:1px solid #e2e8f0; border-radius:12px; background:white;">
                </iframe>
                ''',
                unsafe_allow_html=True,
            )
        else:
            st.info("PDF preview is unavailable for this file.")

        # PDF download
        st.download_button(
            label="⬇️ Download Original PDF",
            data=st.session_state.pdf_bytes,
            file_name=st.session_state.filename,
            mime="application/pdf",
            use_container_width=True,
        )

        # Text snippet preview
        with st.expander("📝 Extracted Text Preview", expanded=False):
            snippet = text[:2000] + ("…" if len(text) > 2000 else "")
            st.text_area("First 2000 characters", snippet, height=250, disabled=True)

        # Top 3 Recommendations
        top_risks = sorted(
            [r for r in risks if r.get("recommendation")],
            key=lambda x: {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}.get(x["severity"], 4)
        )[:3]
        if top_risks:
            st.markdown("#### 💡 Top Recommendations")
            for i, r in enumerate(top_risks, 1):
                sev_icon = "🔴" if r["severity"] in ("Critical", "High") else "🟡"
                st.markdown(f"""
                <div class="recommendation-chip">
                    <span class="rec-number">{i}</span>
                    {sev_icon} <strong>{r['title']}</strong><br>
                    <small>{r['recommendation']}</small>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── RIGHT: Analysis Tabs ─────────────────────────────────────────────────
    with right_col:
        tab_overview, tab_risks, tab_terms, tab_qa = st.tabs([
            "📋 Overview", "⚠️ Risk Analysis", "🔑 Key Terms", "💬 Q&A"
        ])

        # ── TAB 1: Overview ───────────────────────────────────────────────
        with tab_overview:
            st.markdown("### Executive Summary")
            summary_text = st.session_state.summary or "Summary not available."
            st.markdown(f'<div class="summary-box">{summary_text}</div>', unsafe_allow_html=True)

            st.markdown("### Contract Details")
            parties = analysis.get("parties", [])
            contract_type = analysis.get("contract_type", "Not identified")
            gov_law = key_terms.get("Governing Law", "Not found")
            jurisdiction = key_terms.get("Jurisdiction", "Not found")

            d1, d2 = st.columns(2)
            with d1:
                st.markdown(f"""
                <div class="detail-card">
                    <div class="detail-label">📄 Contract Type</div>
                    <div class="detail-value">{contract_type}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="detail-card">
                    <div class="detail-label">⚖️ Governing Law</div>
                    <div class="detail-value">{gov_law}</div>
                </div>
                """, unsafe_allow_html=True)
            with d2:
                st.markdown(f"""
                <div class="detail-card">
                    <div class="detail-label">🏛️ Jurisdiction</div>
                    <div class="detail-value">{jurisdiction}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="detail-card">
                    <div class="detail-label">🚩 Total Red Flags</div>
                    <div class="detail-value" style="color:#ef4444">{len(risks)}</div>
                </div>
                """, unsafe_allow_html=True)

            if parties:
                st.markdown("#### 👥 Parties Identified")
                for p in parties:
                    st.markdown(f'<div class="party-chip">🏢 {p}</div>', unsafe_allow_html=True)

            if critical_dates:
                st.markdown("#### 📅 Critical Dates")
                import pandas as pd
                dates_df = pd.DataFrame(critical_dates)
                st.dataframe(dates_df, use_container_width=True, hide_index=True)

            obligations = analysis.get("obligations", [])
            if obligations:
                st.markdown("#### 📌 Key Obligations")
                for ob in obligations[:6]:
                    st.markdown(f'<div class="obligation-item">→ {ob}</div>', unsafe_allow_html=True)

        # ── TAB 2: Risk Analysis ──────────────────────────────────────────
        with tab_risks:
            st.markdown("### Risk Breakdown")

            if not risks:
                st.info("✅ No significant risks detected in this contract.")
            else:
                import pandas as pd
                severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
                sorted_risks = sorted(risks, key=lambda x: severity_order.get(x.get("severity", "Low"), 4))

                for risk in sorted_risks:
                    sev = risk.get("severity", "Low")
                    if sev in ("Critical", "High"):
                        box_fn = st.error
                        icon = "🔴"
                    elif sev == "Medium":
                        box_fn = st.warning
                        icon = "🟡"
                    else:
                        box_fn = st.info
                        icon = "🔵"

                    with st.expander(f"{icon} [{sev}] {risk.get('title', 'Unknown Risk')}", expanded=(sev in ("Critical", "High"))):
                        c1, c2 = st.columns([2, 1])
                        with c1:
                            st.markdown(f"**Category:** {risk.get('category', 'General')}")
                            st.markdown(f"**Explanation:** {risk.get('explanation', '')}")
                            if risk.get("clause_snippet"):
                                st.markdown("**Clause Snippet:**")
                                st.code(risk["clause_snippet"], language=None)
                        with c2:
                            st.markdown(f"**Recommendation:**")
                            st.markdown(f"_{risk.get('recommendation', 'Consult legal counsel.')}_")

                st.markdown("---")
                st.markdown("#### 📊 Risk Summary Table")
                df_data = []
                for i, r in enumerate(sorted_risks, 1):
                    df_data.append({
                        "ID": f"R{i:02d}",
                        "Severity": r.get("severity", ""),
                        "Category": r.get("category", ""),
                        "Title": r.get("title", ""),
                        "Recommendation": r.get("recommendation", "")[:80] + "…" if len(r.get("recommendation", "")) > 80 else r.get("recommendation", ""),
                    })
                df = pd.DataFrame(df_data)

                def color_severity(val):
                    if val == "Critical": return "background-color: #fee2e2; color: #991b1b; font-weight:600"
                    if val == "High": return "background-color: #ffe4e6; color: #be123c; font-weight:600"
                    if val == "Medium": return "background-color: #fef3c7; color: #92400e; font-weight:600"
                    return "background-color: #dcfce7; color: #166534"

                styled = df.style.map(color_severity, subset=["Severity"])
                st.dataframe(styled, use_container_width=True, hide_index=True)

        # ── TAB 3: Key Terms ──────────────────────────────────────────────
        with tab_terms:
            st.markdown("### Extracted Contract Terms")
            import pandas as pd

            if not key_terms:
                st.info("No key terms could be extracted from this document.")
            else:
                terms_data = []
                for term, value in key_terms.items():
                    confidence = "High" if value and value != "Not found" and value != "Not clearly found" else "Low"
                    conf_icon = "✅" if confidence == "High" else "❓"
                    terms_data.append({
                        "Term": term,
                        "Extracted Value": str(value) if value else "Not found",
                        "Confidence": f"{conf_icon} {confidence}",
                    })

                terms_df = pd.DataFrame(terms_data)
                st.dataframe(terms_df, use_container_width=True, hide_index=True, height=420)

                st.markdown("---")
                st.markdown("#### 📋 Term Details")
                for term, value in key_terms.items():
                    if value and value not in ("Not found", "Not clearly found"):
                        st.markdown(f"""
                        <div class="term-detail-row">
                            <span class="term-name">🔹 {term}</span>
                            <span class="term-value">{value}</span>
                        </div>
                        """, unsafe_allow_html=True)

        # ── TAB 4: Q&A ────────────────────────────────────────────────────
        with tab_qa:
            st.markdown("### 💬 Ask About This Contract")
            st.markdown(
                '<div class="qa-hint">Ask any question about the contract. '
                'The assistant will answer strictly based on the document content.</div>',
                unsafe_allow_html=True
            )

            example_questions = [
                "What is the termination notice period?",
                "Does the contract have unlimited liability?",
                "When does the agreement expire?",
                "What are the payment obligations?",
                "Is there an auto-renewal clause?",
                "Which clause carries the highest risk?",
            ]

            st.markdown("**💡 Example questions:**")
            cols = st.columns(3)
            for i, q in enumerate(example_questions):
                if cols[i % 3].button(q, key=f"eq_{i}", use_container_width=True):
                    st.session_state["qa_input_prefill"] = q

            prefill = st.session_state.pop("qa_input_prefill", "")
            user_question = st.text_input(
                "Your question",
                value=prefill,
                placeholder="e.g. What are the payment terms?",
                key="qa_input",
                label_visibility="collapsed",
            )

            ask_col, clear_col = st.columns([3, 1])
            ask_btn = ask_col.button("🔍 Ask", type="primary", use_container_width=True)
            clear_btn = clear_col.button("🗑️ Clear", use_container_width=True)

            if clear_btn:
                st.session_state.qa_history = []
                st.rerun()

            if ask_btn and user_question.strip():
                with st.spinner("Searching contract…"):
                    qna_engine = ContractQnA(text, analysis, api_key=api_key)
                    answer = qna_engine.answer(user_question.strip())
                    st.session_state.qa_history.insert(0, {
                        "question": user_question.strip(),
                        "answer": answer,
                        "time": datetime.now().strftime("%H:%M"),
                    })

            if st.session_state.qa_history:
                st.markdown("---")
                st.markdown("#### Conversation History")
                for item in st.session_state.qa_history:
                    st.markdown(f"""
                    <div class="qa-bubble-user">
                        <span class="qa-role">You · {item['time']}</span><br>
                        {item['question']}
                    </div>
                    <div class="qa-bubble-ai">
                        <span class="qa-role">ContractAI</span><br>
                        {item['answer']}
                    </div>
                    """, unsafe_allow_html=True)

    # ── DOWNLOADS ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📥 Download Reports")
    dl1, dl2, dl3 = st.columns(3)

    with dl1:
        json_report = build_json_report(
            filename=st.session_state.filename,
            analysis=analysis,
            risks=risks,
            key_terms=key_terms,
            score=score,
            level=level,
            pages=pages,
        )
        st.download_button(
            label="📄 Download JSON Report",
            data=json.dumps(json_report, indent=2, default=str),
            file_name=f"contract_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )

    with dl2:
        try:
            pdf_report_bytes = build_pdf_report(
                filename=st.session_state.filename,
                analysis=analysis,
                risks=risks,
                key_terms=key_terms,
                score=score,
                level=level,
                summary=st.session_state.summary,
            )
            st.download_button(
                label="📋 Download PDF Report",
                data=pdf_report_bytes,
                file_name=f"contract_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"PDF report generation failed: {e}")

    with dl3:
        st.download_button(
            label="📝 Download Raw Text",
            data=st.session_state.extracted_text,
            file_name=f"contract_text_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # ── Legal Disclaimer ─────────────────────────────────────────────────────
    st.markdown("""
    <div class="disclaimer">
        ⚖️ <strong>Legal Disclaimer:</strong> This tool is for contract review assistance only and does 
        not constitute legal advice. Always consult a qualified legal professional before acting on 
        any contract analysis. ContractAI may not detect all risks in complex or non-standard agreements.
    </div>
    """, unsafe_allow_html=True)
