"""
analysis/extractor.py
======================
Extracts structured information from raw contract text.
Uses rule-based heuristics first; optionally enhances with LLM if API key available.
"""

import re
from datetime import datetime
from typing import Optional
from utils.helpers import truncate_snippet, find_all_snippets


# ─── Common regex patterns ────────────────────────────────────────────────────
DATE_PATTERNS = [
    r"\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})\b",
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
    r"\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
    r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\b",
]

MONEY_PATTERNS = [
    r"\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|USD|CAD|GBP|EUR))?\b",
    r"USD\s*[\d,]+(?:\.\d{2})?",
    r"[\d,]+(?:\.\d{2})?\s*(?:dollars|USD|GBP|EUR|CAD)\b",
]

NOTICE_PATTERNS = [
    r"(\d+)\s*(calendar\s+days?|business\s+days?|working\s+days?|days?|weeks?|months?)\s*(?:written\s+)?notice",
    r"notice\s+(?:period\s+of\s+)?(\d+)\s*(days?|weeks?|months?)",
]

CONTRACT_TYPE_KEYWORDS = {
    "Service Agreement": ["services", "service agreement", "statement of work", "sow"],
    "Non-Disclosure Agreement": ["non-disclosure", "nda", "confidentiality agreement", "confidential information"],
    "Employment Agreement": ["employment", "employee", "employer", "salary", "compensation", "wages"],
    "Software License Agreement": ["software", "license", "saas", "subscription", "intellectual property"],
    "Lease Agreement": ["lease", "landlord", "tenant", "rent", "premises", "property"],
    "Sales Agreement": ["purchase", "sale", "buyer", "seller", "goods", "product"],
    "Partnership Agreement": ["partnership", "joint venture", "partners"],
    "Consulting Agreement": ["consultant", "consulting", "independent contractor"],
    "Master Services Agreement": ["master services", "msa", "master agreement"],
    "Loan Agreement": ["loan", "borrower", "lender", "principal", "interest rate", "repayment"],
}

GOVERNING_LAW_PATTERNS = [
    r"governed by (?:the laws? of )?([A-Z][a-zA-Z\s,]+?)(?:\.|,|\n)",
    r"laws? of (?:the (?:State|Province|Country) of )?([A-Z][a-zA-Z\s]+?)(?:\.|,|\s+shall govern)",
    r"governing law[:\s]+([A-Z][a-zA-Z\s,]+?)(?:\.|,|\n)",
]

PARTY_PATTERNS = [
    r"(?:between|by and between)\s+([\w\s,\.]+?)\s+(?:\((?:hereinafter|referred to as|the\s+\"?\w+\"?)\)|and\b)",
    r'"([\w\s]+(?:Inc\.|LLC|Ltd\.?|Corp\.?|LLP|PLC|GmbH|AG|SA))"',
    r"\b([\w\s]+(?:Inc\.|LLC|Ltd\.?|Corp\.?|LLP|PLC))\b",
]


class ContractExtractor:
    def __init__(self, text: str, api_key: Optional[str] = None):
        self.text = text
        self.text_lower = text.lower()
        self.api_key = api_key

    # ─── Main entry ──────────────────────────────────────────────────────────
    def extract_all(self) -> dict:
        result = {
            "contract_type": self._extract_contract_type(),
            "parties": self._extract_parties(),
            "critical_dates": self._extract_critical_dates(),
            "key_terms": self._extract_key_terms(),
            "obligations": self._extract_obligations(),
            "summary": self._generate_summary(),
        }

        # Optional LLM enhancement
        if self.api_key:
            try:
                result = self._enhance_with_llm(result)
            except Exception:
                pass  # Silently fall back

        return result

    # ─── Contract type ────────────────────────────────────────────────────────
    def _extract_contract_type(self) -> str:
        scores = {}
        for contract_type, keywords in CONTRACT_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in self.text_lower)
            if score > 0:
                scores[contract_type] = score
        if scores:
            return max(scores, key=scores.get)
        return "General Contract"

    # ─── Parties ──────────────────────────────────────────────────────────────
    def _extract_parties(self) -> list:
        parties = set()
        # Pattern: company names in quotes
        for m in re.finditer(r'"([\w\s,\.]+?(?:Inc\.|LLC|Ltd\.?|Corp\.?|LLP|PLC|GmbH|AG|SA))"', self.text):
            name = m.group(1).strip()
            if 2 < len(name) < 80:
                parties.add(name)
        # Pattern: "between X and Y"
        between_match = re.search(
            r"between\s+([\w\s,\.]+?)\s+(?:\(.*?\)\s+)?and\s+([\w\s,\.]+?)(?:\(|\.|,|\n)",
            self.text, re.IGNORECASE
        )
        if between_match:
            for grp in [between_match.group(1), between_match.group(2)]:
                clean = grp.strip().strip(",").strip()
                if 2 < len(clean) < 80:
                    parties.add(clean)
        return sorted(list(parties))[:5]

    # ─── Critical dates ───────────────────────────────────────────────────────
    def _extract_critical_dates(self) -> list:
        dates = []
        seen = set()

        date_contexts = [
            ("Effective Date", ["effective date", "effective as of", "commencing on", "starting from"]),
            ("Expiration / End Date", ["expires", "expiry", "termination date", "end date", "expires on"]),
            ("Renewal Date", ["renewal", "renew", "auto-renew"]),
            ("Execution Date", ["executed on", "signed on", "dated as of", "date of execution"]),
            ("Notice Date", ["notice", "notify"]),
        ]

        for label, context_kws in date_contexts:
            for kw in context_kws:
                idx = self.text_lower.find(kw)
                if idx == -1:
                    continue
                window = self.text[max(0, idx - 30): idx + 120]
                for pat in DATE_PATTERNS:
                    m = re.search(pat, window, re.IGNORECASE)
                    if m:
                        date_val = m.group(0).strip()
                        if date_val not in seen:
                            seen.add(date_val)
                            dates.append({"Type": label, "Date": date_val, "Context": kw.title()})
                        break

        return dates

    # ─── Key terms ────────────────────────────────────────────────────────────
    def _extract_key_terms(self) -> dict:
        terms = {}

        # Effective Date
        terms["Effective Date"] = self._find_near_date(
            ["effective date", "effective as of", "commencing on"])

        # Expiration Date
        terms["Expiration Date"] = self._find_near_date(
            ["expires", "expiry date", "termination date", "end date"])

        # Governing Law
        terms["Governing Law"] = self._find_governing_law()

        # Jurisdiction
        terms["Jurisdiction"] = self._find_jurisdiction()

        # Termination Notice
        terms["Termination Notice"] = self._find_notice_period(
            ["termination", "terminate"])

        # Payment Terms
        terms["Payment Terms"] = self._find_payment_terms()

        # Liability Cap
        terms["Liability Cap"] = self._find_liability_cap()

        # Confidentiality
        conf = self._keyword_exists(
            ["confidential", "non-disclosure", "proprietary information"])
        terms["Confidentiality"] = "Present" if conf else "Not found"

        # Indemnification
        ind = self._keyword_exists(["indemnif"])
        terms["Indemnification"] = "Present" if ind else "Not found"

        # Renewal Type
        terms["Renewal Type"] = self._find_renewal_type()

        # IP Ownership
        ip = self._keyword_exists(["intellectual property", "ip ownership", "work for hire", "ownership of"])
        terms["IP Ownership Clause"] = "Present" if ip else "Not found"

        # Force Majeure
        fm = self._keyword_exists(["force majeure", "act of god", "natural disaster"])
        terms["Force Majeure"] = "Present" if fm else "Not found"

        # Arbitration
        arb = self._keyword_exists(["arbitration", "arbitrate", "binding arbitration"])
        terms["Dispute Resolution"] = "Arbitration" if arb else (
            "Litigation" if self._keyword_exists(["courts of", "court of competent jurisdiction"]) else "Not found"
        )

        # Payment due period
        terms["Payment Due Period"] = self._find_payment_due_period()

        return terms

    # ─── Obligations ──────────────────────────────────────────────────────────
    def _extract_obligations(self) -> list:
        obligation_patterns = [
            r"(?:shall|must|agrees? to|is required to|will)\s+([\w\s,]+?)(?:\.|;|\n)",
            r"(?:the (?:client|company|vendor|contractor|service provider|party))\s+(?:shall|must|agrees? to)\s+([\w\s,]+?)(?:\.|;|\n)",
        ]
        obligations = []
        seen = set()
        for pat in obligation_patterns:
            for m in re.finditer(pat, self.text, re.IGNORECASE):
                ob = m.group(0).strip()
                if len(ob) > 20 and len(ob) < 250 and ob not in seen:
                    seen.add(ob)
                    obligations.append(ob)
                if len(obligations) >= 12:
                    break
            if len(obligations) >= 12:
                break
        return obligations[:10]

    # ─── Summary ──────────────────────────────────────────────────────────────
    def _generate_summary(self) -> str:
        contract_type = self._extract_contract_type()
        parties = self._extract_parties()
        gov_law = self._find_governing_law()
        eff_date = self._find_near_date(["effective date", "effective as of"])
        exp_date = self._find_near_date(["expires", "expiry date", "termination date"])
        conf = self._keyword_exists(["confidential"])
        ind = self._keyword_exists(["indemnif"])

        party_str = " and ".join(parties[:2]) if parties else "the identified parties"
        summary_parts = [
            f"This document appears to be a {contract_type} between {party_str}.",
        ]
        if eff_date and eff_date != "Not found":
            summary_parts.append(f"The agreement is effective from {eff_date}.")
        if exp_date and exp_date != "Not found":
            summary_parts.append(f"It is set to expire on {exp_date}.")
        if gov_law and gov_law != "Not found":
            summary_parts.append(f"The agreement is governed by the laws of {gov_law}.")
        if conf:
            summary_parts.append("A confidentiality clause is present.")
        if ind:
            summary_parts.append("Indemnification provisions have been identified.")
        summary_parts.append(
            "Review the Risk Analysis tab for flagged clauses and recommended actions."
        )
        return " ".join(summary_parts)

    # ─── LLM enhancement ─────────────────────────────────────────────────────
    def _enhance_with_llm(self, base_result: dict) -> dict:
        """Use OpenAI to improve extraction quality."""
        import openai
        client = openai.OpenAI(api_key=self.api_key)

        snippet = self.text[:6000]  # Use first 6k chars to stay within token limits
        prompt = f"""
You are a legal contract analyst. Analyze the following contract text and return ONLY a JSON object with these fields:
- contract_type (string)
- parties (list of strings, max 5)
- summary (string, 2-4 sentences, professional executive summary)
- governing_law (string)
- jurisdiction (string)
- effective_date (string)
- expiration_date (string)
- renewal_type (string: "Auto-Renewal", "Manual Renewal", "No Renewal", or "Not found")
- payment_terms (string)
- liability_cap (string)
- termination_notice (string)

If a field is not clearly found, use "Not clearly found in document".
Do not invent information. Return only valid JSON.

CONTRACT TEXT:
{snippet}
"""
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000,
            )
            import json
            raw = response.choices[0].message.content.strip()
            # Strip markdown fences if present
            raw = re.sub(r"```(?:json)?", "", raw).strip()
            llm_data = json.loads(raw)

            # Merge LLM results into base result, preferring LLM if it found real data
            def prefer(llm_val, base_val):
                if llm_val and "not clearly" not in str(llm_val).lower():
                    return llm_val
                return base_val

            base_result["contract_type"] = prefer(llm_data.get("contract_type"), base_result["contract_type"])
            if llm_data.get("parties"):
                base_result["parties"] = llm_data["parties"]
            base_result["summary"] = prefer(llm_data.get("summary"), base_result["summary"])

            kt = base_result.get("key_terms", {})
            kt["Governing Law"] = prefer(llm_data.get("governing_law"), kt.get("Governing Law", "Not found"))
            kt["Jurisdiction"] = prefer(llm_data.get("jurisdiction"), kt.get("Jurisdiction", "Not found"))
            kt["Effective Date"] = prefer(llm_data.get("effective_date"), kt.get("Effective Date", "Not found"))
            kt["Expiration Date"] = prefer(llm_data.get("expiration_date"), kt.get("Expiration Date", "Not found"))
            kt["Renewal Type"] = prefer(llm_data.get("renewal_type"), kt.get("Renewal Type", "Not found"))
            kt["Payment Terms"] = prefer(llm_data.get("payment_terms"), kt.get("Payment Terms", "Not found"))
            kt["Liability Cap"] = prefer(llm_data.get("liability_cap"), kt.get("Liability Cap", "Not found"))
            kt["Termination Notice"] = prefer(llm_data.get("termination_notice"), kt.get("Termination Notice", "Not found"))
            base_result["key_terms"] = kt

        except Exception:
            pass  # Silent fallback

        return base_result

    # ─── Helper methods ───────────────────────────────────────────────────────
    def _find_near_date(self, context_keywords: list) -> str:
        for kw in context_keywords:
            idx = self.text_lower.find(kw)
            if idx == -1:
                continue
            window = self.text[max(0, idx - 20): idx + 120]
            for pat in DATE_PATTERNS:
                m = re.search(pat, window, re.IGNORECASE)
                if m:
                    return m.group(0).strip()
        return "Not found"

    def _find_governing_law(self) -> str:
        for pat in GOVERNING_LAW_PATTERNS:
            m = re.search(pat, self.text, re.IGNORECASE)
            if m:
                return m.group(1).strip().rstrip(".,;")
        return "Not found"

    def _find_jurisdiction(self) -> str:
        patterns = [
            r"(?:exclusive\s+)?jurisdiction\s+(?:of\s+)?(?:the\s+courts?\s+of\s+)?([A-Z][a-zA-Z\s,]+?)(?:\.|,|\n)",
            r"courts?\s+of\s+([A-Z][a-zA-Z\s,]+?)(?:\s+shall have|\.|,|\n)",
        ]
        for pat in patterns:
            m = re.search(pat, self.text, re.IGNORECASE)
            if m:
                return m.group(1).strip().rstrip(".,;")
        return "Not found"

    def _find_notice_period(self, context_keywords: list) -> str:
        for kw in context_keywords:
            idx = self.text_lower.find(kw)
            if idx == -1:
                continue
            window = self.text[max(0, idx - 30): idx + 200]
            for pat in NOTICE_PATTERNS:
                m = re.search(pat, window, re.IGNORECASE)
                if m:
                    return m.group(0).strip()
        return "Not found"

    def _find_payment_terms(self) -> str:
        patterns = [
            r"(?:net\s+\d+|due\s+within\s+\d+\s+days?|payable\s+within\s+\d+\s+days?|payment\s+due\s+\d+\s+days?)",
            r"(?:monthly|quarterly|annually|bi-annually|weekly)\s+(?:payments?|invoices?|fees?)",
        ]
        for pat in patterns:
            m = re.search(pat, self.text, re.IGNORECASE)
            if m:
                return m.group(0).strip()
        return "Not found"

    def _find_payment_due_period(self) -> str:
        m = re.search(r"(?:net\s+(\d+)|due\s+(?:within\s+)?(\d+)\s+days?|payable\s+(?:within\s+)?(\d+)\s+days?)",
                      self.text, re.IGNORECASE)
        if m:
            days = next((g for g in m.groups() if g), None)
            return f"{days} days" if days else m.group(0)
        return "Not found"

    def _find_liability_cap(self) -> str:
        patterns = [
            r"(?:liability|damages?)\s+(?:shall be\s+)?(?:limited|capped)\s+to\s+([\$\d\w\s,\.]+?)(?:\.|;|\n)",
            r"aggregate\s+liability\s+(?:shall\s+not\s+exceed|limited to)\s+([\$\d\w\s,\.]+?)(?:\.|;|\n)",
            r"in\s+no\s+event\s+(?:shall|will)\s+[\w\s]+?liability\s+exceed\s+([\$\d\w\s,\.]+?)(?:\.|;|\n)",
        ]
        for pat in patterns:
            m = re.search(pat, self.text, re.IGNORECASE)
            if m:
                return m.group(1).strip().rstrip(".,;")

        # Check for "unlimited" liability
        if re.search(r"unlimited\s+liability", self.text, re.IGNORECASE):
            return "Unlimited (HIGH RISK)"
        return "Not found"

    def _find_renewal_type(self) -> str:
        if re.search(r"auto(?:matically)?[\s-]renew|automatic\s+renewal|shall\s+(?:automatically\s+)?renew",
                     self.text, re.IGNORECASE):
            return "Auto-Renewal"
        if re.search(r"(?:may\s+be\s+renewed|option\s+to\s+renew|renewal\s+at\s+the\s+(?:option|discretion))",
                     self.text, re.IGNORECASE):
            return "Optional Renewal"
        if re.search(r"no\s+(?:automatic\s+)?renewal|does\s+not\s+renew|shall\s+not\s+(?:automatically\s+)?renew",
                     self.text, re.IGNORECASE):
            return "No Auto-Renewal"
        return "Not found"

    def _keyword_exists(self, keywords: list) -> bool:
        return any(kw in self.text_lower for kw in keywords)
