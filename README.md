# 🔐 ContractAI — Enterprise Contract Analyzer & Risk Agent

A production-ready Streamlit application that analyzes uploaded contract PDFs, extracts key legal terms, detects risks, highlights critical dates, supports natural-language Q&A, and generates downloadable JSON and PDF reports.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **PDF Upload & Preview** | Upload any PDF contract; page count and text preview shown |
| 🧠 **Smart Extraction** | Automatically extracts parties, dates, payment terms, governing law, and 12+ key terms |
| ⚠️ **Risk Scoring** | Weighted 0–100 risk score with Low / Medium / High / Critical levels |
| 🚩 **18 Risk Rules** | Pre-built heuristics covering unlimited liability, one-sided indemnity, auto-renewal, and more |
| 💬 **Contract Q&A** | Ask natural-language questions; grounded answers from the contract text |
| 🤖 **LLM Mode** | Optional OpenAI GPT integration for richer extraction and Q&A |
| 📊 **Visual Dashboard** | Risk cards, severity badges, styled tables, and metric panels |
| 📥 **JSON Report** | Full structured analysis exportable as JSON |
| 📋 **PDF Report** | Professional multi-page PDF report with risk tables and key terms |
| 🎨 **Premium UI** | Custom CSS, Inter font, indigo palette, responsive layout |

---

## 🏗️ Project Structure

```
contract_analyzer/
├── app.py                      # Main Streamlit application
├── analysis/
│   ├── extractor.py            # Key term & clause extraction
│   ├── risk_engine.py          # Risk scoring engine (18 rules)
│   ├── qna.py                  # Contract Q&A (heuristic + LLM)
│   └── report_builder.py       # JSON + PDF report generation
├── utils/
│   ├── ui.py                   # CSS, header, sidebar, empty state
│   └── helpers.py              # PDF text extraction utilities
├── .streamlit/
│   └── config.toml             # Streamlit theme + server settings
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourname/contract-analyzer.git
cd contract-analyzer
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables (optional)
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY if you want LLM mode
```

### 5. Run the app
```bash
streamlit run app.py
```

The app will open at **http://localhost:8501**

---

## ☁️ Deploy to Streamlit Cloud

1. Push your project to a **public or private GitHub repository**
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in
3. Click **New app** → Select your repository and branch
4. Set **Main file path**: `app.py`
5. Click **Deploy**

### Adding your OpenAI API key to Streamlit Cloud
1. In the Streamlit Cloud dashboard, open your app settings
2. Go to **Secrets**
3. Add:
```toml
OPENAI_API_KEY = "sk-your-api-key-here"
```
4. Redeploy

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Optional | Enables LLM-enhanced extraction & Q&A via GPT-3.5-Turbo |

Without `OPENAI_API_KEY`, the app runs entirely in **heuristic rule-based mode** — all features still work.

---

## 📊 Risk Scoring System

The risk engine evaluates 18 risk rules weighted by severity:

| Rule | Severity | Weight |
|------|----------|--------|
| Unlimited Liability | Critical | 20 |
| Immediate Termination Without Cause | High | 14 |
| One-Sided Indemnification | High | 12 |
| Auto-Renewal Without Notice | Medium | 10 |
| Sole Discretion Clauses | High | 10 |
| Missing Governing Law | Medium | 8 |
| Ambiguous Payment Penalties | Medium | 8 |
| Missing Critical Dates | Medium | 9 |
| Liquidated Damages | High | 9 |
| Binding Arbitration | Medium | 7 |
| Unilateral Assignment | Medium | 7 |
| IP Ownership Ambiguity | Medium | 7 |
| Consequential Damages Excluded | Medium | 6 |
| Non-Refundable Fees | Medium | 6 |
| Vague Termination Clause | Medium | 6 |
| Broad Confidentiality | Medium | 8 |
| Best Efforts Standard | Low | 5 |
| Broad Waiver Clause | Low | 5 |

**Score thresholds:**
- 0–29: 🟢 Low
- 30–59: 🟡 Medium
- 60–84: 🟠 High
- 85–100: 🔴 Critical

---

## 💬 Example Q&A Questions

- *What is the termination notice period?*
- *Does this contract have unlimited liability?*
- *When does the agreement expire?*
- *What are the payment terms?*
- *Is there an auto-renewal clause?*
- *Which clause carries the highest risk?*
- *What governing law applies to this contract?*
- *Are there any indemnification obligations?*

---

## 📸 Screenshots

> *(Add your screenshots here after running the app)*

- **Landing page** — upload prompt with feature cards
- **Analysis dashboard** — risk score, metrics, and PDF preview
- **Risk Analysis tab** — color-coded risk cards with explanations
- **Key Terms tab** — extracted term table with confidence indicators
- **Q&A tab** — conversation-style question answering

---

## ⚠️ Limitations

- Works best with text-based PDFs; scanned/image PDFs may have limited extraction
- Heuristic analysis may miss complex or unusual clause structures
- LLM analysis uses GPT-3.5-Turbo on the first 6,000 characters (to manage token cost)
- Not a substitute for professional legal review

---

## 🔮 Future Improvements

- [ ] Multi-document comparison (compare two contracts side-by-side)
- [ ] Clause library / benchmark comparison against standard templates
- [ ] Red-line / change tracking between contract versions
- [ ] Collaboration mode — share analysis with teammates
- [ ] Custom risk rule configuration per industry
- [ ] Named entity recognition for better party extraction
- [ ] Support for DOCX and TXT input formats
- [ ] Persistent history / analysis sessions

---

## ⚖️ Disclaimer

**ContractAI is for contract review assistance only and does not constitute legal advice.** Always consult a qualified legal professional before executing or relying on any contract. ContractAI may not detect all risks in complex or non-standard agreements.

---

## 🛠️ Tech Stack

- **Frontend / App**: [Streamlit](https://streamlit.io)
- **PDF Extraction**: pdfplumber · PyPDF2 · pymupdf
- **PDF Reports**: ReportLab · fpdf2
- **Data**: pandas
- **LLM (optional)**: OpenAI GPT-3.5-Turbo via `openai` SDK
- **Language**: Python 3.9+
