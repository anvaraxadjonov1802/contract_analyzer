"""
analysis/qna.py
================
Contract Q&A engine.
- With API key: uses OpenAI GPT for accurate, grounded answers.
- Without API key: uses heuristic keyword retrieval with snippet extraction.
"""

import re
from typing import Optional
from utils.helpers import truncate_snippet, find_all_snippets


# ─── Heuristic Q&A mapping ────────────────────────────────────────────────────
# Maps question intent to relevant keywords for snippet retrieval
QUESTION_INTENT_MAP = [
    (
        ["termination notice", "notice period", "notice to terminate", "how much notice"],
        ["termination", "terminate", "notice period", "written notice"],
        "termination_notice",
    ),
    (
        ["unlimited liability", "liability cap", "liability limit"],
        ["liability", "unlimited liability", "cap on liability", "aggregate liability"],
        "liability",
    ),
    (
        ["when does", "expire", "expiration", "end date", "expiry"],
        ["expires", "expiry", "expiration", "termination date", "end date"],
        "expiry",
    ),
    (
        ["payment", "pay", "invoice", "fee", "cost", "price"],
        ["payment", "pay", "invoice", "fee", "due", "net 30", "net 60"],
        "payment",
    ),
    (
        ["auto-renew", "automatic renewal", "auto renewal", "renew"],
        ["auto-renew", "automatic renewal", "automatically renew", "renewal"],
        "renewal",
    ),
    (
        ["governing law", "which law", "what jurisdiction", "which jurisdiction"],
        ["governed by", "governing law", "jurisdiction", "laws of"],
        "governing_law",
    ),
    (
        ["confidential", "confidentiality", "nda", "non-disclosure"],
        ["confidential", "confidentiality", "non-disclosure", "proprietary"],
        "confidentiality",
    ),
    (
        ["indemnif", "hold harmless", "indemnification"],
        ["indemnif", "hold harmless", "indemnification"],
        "indemnification",
    ),
    (
        ["arbitration", "dispute", "resolve dispute", "resolve conflict"],
        ["arbitration", "dispute resolution", "mediation", "litigation"],
        "dispute",
    ),
    (
        ["risky", "most risky", "highest risk", "biggest risk", "dangerous clause"],
        [],  # Handled specially
        "risk_summary",
    ),
    (
        ["penalty", "penalties", "late fee", "late payment"],
        ["penalty", "penalties", "late payment", "interest", "liquidated damages"],
        "penalty",
    ),
    (
        ["effective date", "start date", "when does it start", "when does this start"],
        ["effective date", "effective as of", "commencing on", "starting from"],
        "effective_date",
    ),
    (
        ["parties", "who are the parties", "who signed", "who is involved"],
        ["between", "party", "parties", "hereinafter"],
        "parties",
    ),
    (
        ["obligation", "obligations", "responsibilities", "duties"],
        ["shall", "must", "agrees to", "is required to", "obligated"],
        "obligations",
    ),
    (
        ["ip", "intellectual property", "ownership", "work for hire"],
        ["intellectual property", "work for hire", "ownership", "ip"],
        "ip",
    ),
    (
        ["force majeure", "act of god", "natural disaster"],
        ["force majeure", "act of god", "natural disaster", "circumstances beyond"],
        "force_majeure",
    ),
    (
        ["warranty", "warranties", "guarantees"],
        ["warrant", "warranty", "warranties", "guarantee"],
        "warranty",
    ),
]


def _build_pre_answer(intent: str, analysis: dict) -> Optional[str]:
    """Build a structured pre-answer from extracted analysis data."""
    key_terms = analysis.get("key_terms", {})
    extraction = analysis

    answers = {
        "termination_notice": f"The termination notice period is: **{key_terms.get('Termination Notice', 'Not clearly found in the document.')}**",
        "liability": f"The liability cap is: **{key_terms.get('Liability Cap', 'Not clearly found in the document.')}**",
        "expiry": f"The expiration / end date is: **{key_terms.get('Expiration Date', 'Not clearly found in the document.')}**",
        "payment": f"Payment terms identified: **{key_terms.get('Payment Terms', key_terms.get('Payment Due Period', 'Not clearly found in the document.'))}**",
        "renewal": f"Renewal type: **{key_terms.get('Renewal Type', 'Not clearly found in the document.')}**",
        "governing_law": f"Governing law: **{key_terms.get('Governing Law', 'Not clearly found.')}** | Jurisdiction: **{key_terms.get('Jurisdiction', 'Not clearly found.')}**",
        "confidentiality": f"Confidentiality clause: **{key_terms.get('Confidentiality', 'Not clearly found.')}**",
        "indemnification": f"Indemnification clause: **{key_terms.get('Indemnification', 'Not clearly found.')}**",
        "dispute": f"Dispute resolution method: **{key_terms.get('Dispute Resolution', 'Not clearly found.')}**",
        "penalty": "Penalty / late payment provisions were flagged in the risk analysis. Review the Risk Analysis tab.",
        "effective_date": f"Effective date: **{key_terms.get('Effective Date', 'Not clearly found in the document.')}**",
        "ip": f"IP Ownership clause: **{key_terms.get('IP Ownership Clause', 'Not clearly found.')}**",
        "force_majeure": f"Force Majeure clause: **{key_terms.get('Force Majeure', 'Not clearly found.')}**",
        "warranty": "No specific warranty term was extracted. Please review the contract text directly.",
    }

    return answers.get(intent)


class ContractQnA:
    def __init__(self, text: str, analysis: dict, api_key: Optional[str] = None):
        self.text = text
        self.text_lower = text.lower()
        self.analysis = analysis
        self.api_key = api_key

    def answer(self, question: str) -> str:
        """Return an answer to the question about the contract."""
        if self.api_key:
            try:
                return self._llm_answer(question)
            except Exception as e:
                return self._heuristic_answer(question) + f"\n\n*[LLM unavailable: {str(e)[:60]}…]*"
        return self._heuristic_answer(question)

    # ─── LLM-based answer ─────────────────────────────────────────────────────
    def _llm_answer(self, question: str) -> str:
        import openai
        client = openai.OpenAI(api_key=self.api_key)

        # Use a targeted portion of the contract text
        context = self.text[:8000]

        prompt = f"""You are a senior legal analyst reviewing a contract. Answer the following question STRICTLY based on the contract text provided below.

Rules:
- Only use information from the contract text.
- If the answer is not clearly present, say "This is not clearly specified in the contract."
- Be concise (2-4 sentences max).
- Do not make assumptions or hallucinate.
- Highlight key clause language in quotes where relevant.

CONTRACT TEXT:
{context}

QUESTION: {question}

ANSWER:"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()

    # ─── Heuristic answer ─────────────────────────────────────────────────────
    def _heuristic_answer(self, question: str) -> str:
        q_lower = question.lower()

        # ── Special: "most risky" ────────────────────────────────────────────
        if any(kw in q_lower for kw in ["risky", "most risky", "highest risk", "dangerous"]):
            return self._answer_most_risky()

        # ── Special: "parties" ───────────────────────────────────────────────
        if any(kw in q_lower for kw in ["who are the parties", "parties to", "who signed"]):
            parties = self.analysis.get("parties", [])
            if parties:
                return f"The following parties were identified in the contract: **{', '.join(parties)}**."
            return "The parties to this contract could not be clearly identified. Please review the opening clauses of the document."

        # ── Intent-based matching ────────────────────────────────────────────
        for question_triggers, search_keywords, intent in QUESTION_INTENT_MAP:
            if any(t in q_lower for t in question_triggers):
                # First try structured answer
                pre = _build_pre_answer(intent, self.analysis)
                if pre and "not clearly" not in pre.lower():
                    # Also find supporting snippet
                    snippets = find_all_snippets(self.text, search_keywords, window=150) if search_keywords else []
                    if snippets:
                        return f"{pre}\n\n**Supporting clause:**\n> {snippets[0]}"
                    return pre

                # Fallback: snippet search
                if search_keywords:
                    snippets = find_all_snippets(self.text, search_keywords, window=200)
                    if snippets:
                        return (
                            f"Based on the contract text, here is the most relevant excerpt:\n\n"
                            f"> {snippets[0]}\n\n"
                            f"*This clause may require legal review for full interpretation.*"
                        )

                # Last resort
                return (
                    f"This information was not clearly identified in the contract. "
                    f"Please review the relevant clauses manually or enable LLM mode for deeper analysis."
                )

        # ── Generic keyword search ────────────────────────────────────────────
        return self._generic_search(question)

    def _generic_search(self, question: str) -> str:
        """Search for question keywords in contract text."""
        # Extract significant words from question
        stopwords = {"what", "is", "the", "are", "does", "do", "has", "have", "can",
                     "which", "where", "when", "how", "a", "an", "this", "that", "it",
                     "and", "or", "in", "of", "for", "to", "on", "with", "any", "there"}
        words = [w.lower().strip("?.,!") for w in question.split() if w.lower() not in stopwords and len(w) > 3]

        snippets = find_all_snippets(self.text, words, window=200) if words else []

        if snippets:
            return (
                f"Here is the most relevant section I found in the contract:\n\n"
                f"> {snippets[0]}\n\n"
                f"*For precise legal interpretation, consult a qualified attorney.*"
            )

        return (
            "I could not find a clear answer to that question in the contract text. "
            "This may be because the topic is not covered, uses different terminology, "
            "or is in an image-based section that could not be extracted. "
            "Consider enabling LLM mode or reviewing the document manually."
        )

    def _answer_most_risky(self) -> str:
        """Identify and describe the highest-risk element."""
        # Import here to avoid circular
        from analysis.risk_engine import RiskEngine
        risks, score, level = RiskEngine(self.text, self.analysis).evaluate()
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        if not risks:
            return "No significant risks were identified in this contract."
        top = sorted(risks, key=lambda r: severity_order.get(r["severity"], 4))[0]
        return (
            f"The **highest-risk clause** identified is: **{top['title']}** ({top['severity']} severity).\n\n"
            f"{top['explanation']}\n\n"
            f"**Recommendation:** {top['recommendation']}"
        )
