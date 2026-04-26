"""
analysis/risk_engine.py
========================
Evaluates contract text for legal risks and produces a 0-100 risk score.
Uses a weighted heuristic model with explainable rationale.
"""

import re
from typing import Tuple
from utils.helpers import truncate_snippet


# ─── Risk definitions ─────────────────────────────────────────────────────────
# Each risk rule: (id, category, title, keywords[], weight, severity, explanation, recommendation)
RISK_RULES = [
    (
        "R001", "Liability", "Unlimited Liability",
        ["unlimited liability", "no cap on liability", "without limit"],
        20, "Critical",
        "The contract contains language suggesting unlimited liability, exposing a party to uncapped financial loss.",
        "Negotiate a liability cap (e.g., capped at contract value or a fixed amount).",
    ),
    (
        "R002", "Indemnification", "One-Sided Indemnification",
        ["indemnify", "indemnification", "hold harmless"],
        12, "High",
        "Indemnification clauses require one party to cover costs and losses of the other. One-sided indemnity is high risk.",
        "Ensure indemnification is mutual or clearly bounded to specific breaches.",
    ),
    (
        "R003", "Termination", "Immediate Termination Without Cause",
        ["immediately terminate", "terminate immediately", "termination without cause", "terminate without cause", "without notice"],
        14, "High",
        "Either or one party may terminate the agreement immediately or without cause, creating significant operational risk.",
        "Negotiate a reasonable notice period (e.g., 30–90 days) before termination is effective.",
    ),
    (
        "R004", "Renewal", "Auto-Renewal Without Adequate Notice",
        ["automatically renew", "auto-renew", "automatic renewal"],
        10, "Medium",
        "The contract includes an auto-renewal clause. If notice requirements are unclear, parties may be unknowingly locked in.",
        "Ensure auto-renewal notice periods are clearly defined and calendar reminders are set.",
    ),
    (
        "R005", "Governing Law", "Missing or Ambiguous Governing Law",
        [],  # checked separately
        8, "Medium",
        "No governing law or jurisdiction clause was clearly identified. This creates uncertainty about which legal framework applies.",
        "Add an explicit governing law clause specifying the applicable jurisdiction.",
    ),
    (
        "R006", "Payment", "Unclear or Aggressive Payment Penalties",
        ["penalty", "penalties", "late payment", "interest on overdue", "non-refundable"],
        8, "Medium",
        "The contract contains penalty clauses or non-refundable fee provisions that may be financially burdensome.",
        "Review penalty rates and ensure they comply with applicable law. Negotiate caps where possible.",
    ),
    (
        "R007", "Confidentiality", "Broad or Perpetual Confidentiality Obligations",
        ["perpetual confidentiality", "indefinite confidentiality", "confidential in perpetuity"],
        8, "Medium",
        "The confidentiality clause may impose obligations indefinitely or with very broad scope.",
        "Limit confidentiality obligations to a defined term (e.g., 2–5 years) with specific carve-outs.",
    ),
    (
        "R008", "Discretion", "Sole Discretion Clauses",
        ["sole discretion", "absolute discretion", "in its sole and absolute discretion"],
        10, "High",
        "Provisions granting sole discretion to one party create imbalanced power and potential for arbitrary decisions.",
        "Replace 'sole discretion' with 'reasonable discretion' and define clear objective criteria.",
    ),
    (
        "R009", "Dispute", "Binding Arbitration Clause",
        ["binding arbitration", "mandatory arbitration", "compulsory arbitration"],
        7, "Medium",
        "The contract requires disputes to be resolved via binding arbitration, which may limit access to courts.",
        "Review arbitration terms carefully — ensure location, rules, and cost allocation are favorable.",
    ),
    (
        "R010", "Termination", "Vague Termination Clause",
        ["material breach", "at its discretion", "may terminate"],
        6, "Medium",
        "Termination triggers are vaguely defined, potentially allowing termination based on subjective interpretation.",
        "Define termination triggers with specific, objective criteria and cure periods.",
    ),
    (
        "R011", "Obligations", "Best Efforts / Commercially Reasonable Efforts",
        ["best efforts", "commercially reasonable efforts", "reasonable endeavours"],
        5, "Low",
        "These vague obligation standards ('best efforts') are difficult to enforce and may be interpreted differently in various jurisdictions.",
        "Where possible, replace with specific, measurable deliverable obligations.",
    ),
    (
        "R012", "Dates", "Missing Effective or Expiry Date",
        [],  # checked separately
        9, "Medium",
        "The contract does not clearly specify an effective date or expiry date, creating uncertainty about the agreement's term.",
        "Add explicit effective and expiry dates to the contract.",
    ),
    (
        "R013", "IP", "IP Ownership Ambiguity",
        ["intellectual property", "work for hire", "ownership of"],
        7, "Medium",
        "Intellectual property ownership clauses are present but may be ambiguous or overly broad.",
        "Clearly define ownership of all work products, pre-existing IP, and newly created IP.",
    ),
    (
        "R014", "Payment", "Non-Refundable Fees",
        ["non-refundable", "not refundable", "no refund"],
        6, "Medium",
        "Non-refundable fee provisions lock payment regardless of contract performance or early termination.",
        "Negotiate pro-rated refunds or performance-based payment structures.",
    ),
    (
        "R015", "Waiver", "Broad Waiver Clause",
        ["waiver", "waives", "deemed to have waived"],
        5, "Low",
        "Broad waiver language may inadvertently cause a party to lose important contractual rights.",
        "Ensure waivers are specific, in writing, and do not create precedent for future waivers.",
    ),
    (
        "R016", "Liability", "Consequential Damages Excluded",
        ["consequential damages", "incidental damages", "indirect damages", "special damages"],
        6, "Medium",
        "Exclusions of consequential damages may prevent recovery for significant losses resulting from a breach.",
        "Negotiate carve-outs for intentional misconduct, gross negligence, and data breaches.",
    ),
    (
        "R017", "Assignment", "Unilateral Assignment Rights",
        ["may assign", "right to assign", "assigns this agreement"],
        7, "Medium",
        "One party may be able to assign the agreement to a third party without consent, changing the nature of the relationship.",
        "Add a clause requiring written consent before assignment and right of termination if consent is denied.",
    ),
    (
        "R018", "Penalty", "Liquidated Damages / High Penalties",
        ["liquidated damages", "agreed damages", "pre-agreed penalty"],
        9, "High",
        "Liquidated damages clauses set pre-agreed penalties that may be disproportionate to actual losses.",
        "Ensure liquidated damages represent a genuine pre-estimate of loss and are not punitive.",
    ),
]


class RiskEngine:
    def __init__(self, text: str, extraction: dict):
        self.text = text
        self.text_lower = text.lower()
        self.extraction = extraction

    def evaluate(self) -> Tuple[list, int, str]:
        """
        Returns:
            risks (list of risk dicts)
            score (int 0-100)
            level (str Low/Medium/High/Critical)
        """
        detected_risks = []
        total_weight = 0

        key_terms = self.extraction.get("key_terms", {})
        governing_law = key_terms.get("Governing Law", "Not found")
        eff_date = key_terms.get("Effective Date", "Not found")
        exp_date = key_terms.get("Expiration Date", "Not found")

        for rule in RISK_RULES:
            rid, category, title, keywords, weight, severity, explanation, recommendation = rule

            triggered = False
            clause_snippet = ""

            # ── Special cases with no keywords ─────────────────────────────
            if rid == "R005":  # Governing law missing
                triggered = governing_law in ("Not found", "", None)
                if triggered:
                    clause_snippet = "No governing law clause identified."

            elif rid == "R012":  # Missing dates
                missing_eff = eff_date in ("Not found", "", None)
                missing_exp = exp_date in ("Not found", "", None)
                triggered = missing_eff or missing_exp
                if triggered:
                    clause_snippet = f"Effective date: {eff_date}. Expiry date: {exp_date}."

            else:
                # Keyword-based detection
                for kw in keywords:
                    if kw in self.text_lower:
                        triggered = True
                        clause_snippet = truncate_snippet(self.text, kw, 220)
                        break

            if triggered:
                # Adjust severity based on context
                actual_severity = severity
                if rid == "R002":
                    actual_severity = self._check_indemnity_one_sided()
                if rid == "R004":
                    actual_severity = self._check_autorenewal_notice()

                detected_risks.append({
                    "risk_id": rid,
                    "category": category,
                    "severity": actual_severity,
                    "title": title,
                    "explanation": explanation,
                    "clause_snippet": clause_snippet,
                    "recommendation": recommendation,
                    "weight": weight,
                })
                total_weight += weight

        # ── Score calculation ────────────────────────────────────────────────
        max_possible = sum(r[4] for r in RISK_RULES)
        raw_score = min(100, int((total_weight / max(max_possible, 1)) * 100))

        # Boost score for critical risks
        critical_count = sum(1 for r in detected_risks if r["severity"] == "Critical")
        high_count = sum(1 for r in detected_risks if r["severity"] == "High")
        raw_score = min(100, raw_score + critical_count * 8 + high_count * 3)

        # ── Level classification ─────────────────────────────────────────────
        if raw_score < 30:
            level = "Low"
        elif raw_score < 60:
            level = "Medium"
        elif raw_score < 85:
            level = "High"
        else:
            level = "Critical"

        return detected_risks, raw_score, level

    def _check_indemnity_one_sided(self) -> str:
        """Check if indemnification appears one-sided."""
        # Mutual indemnification typically has "each party shall indemnify"
        if re.search(r"each\s+party\s+(?:shall|will|agrees? to)\s+indemnif",
                     self.text, re.IGNORECASE):
            return "Medium"
        # If only one party is named near indemnify, it's one-sided
        return "High"

    def _check_autorenewal_notice(self) -> str:
        """Check if auto-renewal has a clear notice period."""
        if re.search(
            r"(?:auto(?:matic(?:ally)?)?[\s-]renew).{0,200}(?:days?|weeks?|months?)\s+(?:written\s+)?notice",
            self.text, re.IGNORECASE
        ):
            return "Low"
        return "Medium"
