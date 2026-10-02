"""FinSight AI Training & Adaptation Layer.

Trains the Copilot on domain-specific invoice patterns, company policies,
and historical decision data to improve accuracy and relevance.
"""

from __future__ import annotations
import json
import os
from datetime import datetime, timedelta
from typing import Any
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

TRAINING_CONFIG = {
    "domain": "accounts_payable_invoice_analysis",
    "model": "gemini-2.5-flash",
    "max_context_examples": 50,
    "similarity_threshold": 0.7,
    "retrain_interval_days": 7,
}


class InvoicePatternAnalyzer:
    """Learn common invoice patterns and anomalies."""

    def __init__(self):
        self.vendor_patterns = defaultdict(lambda: {"total": 0, "avg_amount": 0, "categories": {}})
        self.category_statistics = defaultdict(lambda: {"count": 0, "avg": 0, "max": 0, "min": float("inf")})
        self.common_violations = defaultdict(int)
        self.approval_rate_by_vendor = {}

    def analyze_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract patterns from analysis results."""
        for result in results:
            evidence = result.get("evidence", {})
            vendor = evidence.get("vendor", "unknown")
            amount = evidence.get("amount", 0)
            category = evidence.get("category", "unknown")

            # Vendor patterns
            self.vendor_patterns[vendor]["total"] += 1
            self.vendor_patterns[vendor]["avg_amount"] = (
                (self.vendor_patterns[vendor]["avg_amount"] * (self.vendor_patterns[vendor]["total"] - 1) + amount)
                / self.vendor_patterns[vendor]["total"]
            )
            self.vendor_patterns[vendor]["categories"][category] = (
                self.vendor_patterns[vendor]["categories"].get(category, 0) + 1
            )

            # Category statistics
            stats = self.category_statistics[category]
            stats["count"] += 1
            old_avg = stats["avg"]
            stats["avg"] = (old_avg * (stats["count"] - 1) + amount) / stats["count"]
            stats["max"] = max(stats["max"], amount)
            stats["min"] = min(stats["min"], amount)

            # Violation patterns
            for rule_id in result.get("rule_ids", []):
                self.common_violations[rule_id] += 1

        # Calculate approval rates
        for vendor in self.vendor_patterns:
            total = self.vendor_patterns[vendor]["total"]
            self.approval_rate_by_vendor[vendor] = 1.0 - (
                sum(1 for r in results if r.get("evidence", {}).get("vendor") == vendor and r.get("status") == "EXCEPTION")
                / total
                if total > 0
                else 0
            )

        return {
            "vendor_patterns": dict(self.vendor_patterns),
            "category_statistics": dict(self.category_statistics),
            "common_violations": dict(self.common_violations),
            "approval_rate_by_vendor": self.approval_rate_by_vendor,
            "timestamp": datetime.now().isoformat(),
        }

    def get_vendor_profile(self, vendor: str) -> dict[str, Any]:
        """Get learned profile for a vendor."""
        profile = self.vendor_patterns.get(vendor, {})
        return {
            "vendor": vendor,
            "transaction_count": profile.get("total", 0),
            "average_amount": profile.get("avg_amount", 0),
            "common_categories": sorted(
                profile.get("categories", {}).items(), key=lambda x: x[1], reverse=True
            )[:3],
            "approval_rate": self.approval_rate_by_vendor.get(vendor, 0.5),
        }


class FineStuningDataGenerator:
    """Generate fine-tuning examples for domain-specific model adaptation."""

    def __init__(self):
        self.examples = []
        self.last_training = None

    def add_example(self, question: str, answer: str, result_context: dict[str, Any], approval: bool = True):
        """Record a Q&A pair for fine-tuning."""
        example = {
            "question": question,
            "answer": answer,
            "context": result_context,
            "approved": approval,
            "timestamp": datetime.now().isoformat(),
        }
        self.examples.append(example)

    def generate_training_set(self, min_examples: int = 10) -> list[dict[str, Any]]:
        """Export approved examples as fine-tuning data."""
        approved = [e for e in self.examples if e["approved"]]
        if len(approved) < min_examples:
            return []

        training_data = []
        for example in approved[-TRAINING_CONFIG["max_context_examples"] :]:
            training_data.append(
                {
                    "messages": [
                        {"role": "user", "content": example["question"]},
                        {"role": "assistant", "content": example["answer"]},
                    ],
                    "metadata": {"timestamp": example["timestamp"], "domain": "ap_invoice_analysis"},
                }
            )
        return training_data

    def export_jsonl(self, filepath: str):
        """Export training examples as JSONL for Gemini fine-tuning."""
        training_data = self.generate_training_set()
        if not training_data:
            return False, "Not enough approved examples for fine-tuning."

        with open(filepath, "w") as f:
            for example in training_data:
                f.write(json.dumps(example) + "\n")

        self.last_training = datetime.now()
        return True, f"Exported {len(training_data)} training examples to {filepath}"


class ContextualInvoiceExplainer:
    """Generate better explanations using learned patterns."""

    def __init__(self, analyzer: InvoicePatternAnalyzer):
        self.analyzer = analyzer

    def contextualize_explanation(self, result: dict[str, Any], results: list[dict[str, Any]]) -> str:
        """Generate a contextualized explanation using learned patterns."""
        invoice_id = result.get("invoice_id")
        evidence = result.get("evidence", {})
        vendor = evidence.get("vendor")
        amount = evidence.get("amount", 0)
        category = evidence.get("category")

        vendor_profile = self.analyzer.get_vendor_profile(vendor)
        stats = self.analyzer.category_statistics.get(category, {})

        lines = [f"Invoice {invoice_id} analysis:"]

        # Vendor context
        if vendor_profile["transaction_count"] > 0:
            lines.append(
                f"Vendor '{vendor}' has {vendor_profile['transaction_count']} transactions "
                f"with {vendor_profile['approval_rate']:.0%} approval rate."
            )

        # Amount context
        if stats.get("count", 0) > 0:
            if amount > stats.get("max", 0):
                lines.append(
                    f"Amount ₹{amount:,.0f} exceeds the highest seen in {category} category (₹{stats.get('max', 0):,.0f})."
                )
            elif amount < stats.get("min", float("inf")):
                lines.append(f"Amount ₹{amount:,.0f} is below typical {category} category minimums.")

        # Decision rationale
        if result.get("status") == "CLEAN":
            lines.append(
                f"✓ PASSED: This invoice matches {vendor}'s typical profile "
                f"and is within expected {category} category ranges."
            )
        else:
            for reason in result.get("reasons", []):
                rule = reason.get("rule")
                msg = reason.get("message")
                lines.append(f"⚠ {rule}: {msg}")
                if rule == "DUPLICATE_INVOICE":
                    lines.append(f"  Matches invoice {reason.get('matched_invoice_id')}")

        return "\n".join(lines)


class AdaptivePromptBuilder:
    """Build better prompts using historical data and learned patterns."""

    def __init__(self, analyzer: InvoicePatternAnalyzer, finetuner: FineStuningDataGenerator):
        self.analyzer = analyzer
        self.finetuner = finetuner

    def build_adaptive_prompt(
        self, question: str, results: list[dict[str, Any]], conversation: list[Any] | None = None
    ) -> str:
        """Build a prompt that includes learned patterns and historical examples."""
        base_prompt = f"""You are FinSight Copilot, an AI trained on accounts-payable invoice analysis.

DOMAIN KNOWLEDGE:
- You've analyzed {sum(r.get('evidence', {}).get('total', 1) for r in results)} invoices across multiple vendors and categories.
- Common violation patterns: {dict(list(self.analyzer.common_violations.items())[:5])}
- Vendors with high approval rates: {[v for v, rate in self.analyzer.approval_rate_by_vendor.items() if rate > 0.95][:3]}

QUESTION: {question}

CONTEXT: {json.dumps([r.get('evidence', {}) for r in results[:10]], indent=2)}

Remember:
- The Python rule engine is authoritative.
- Explain decisions, never change them.
- Reference learned vendor patterns when relevant.
- Only answer AP/invoice/audit/FinSight questions.
"""
        return base_prompt[:100000]


def save_training_data(analyzer: InvoicePatternAnalyzer, finetuner: FineStuningDataGenerator):
    """Persist training data for future sessions."""
    try:
        training_dir = "data/training"
        os.makedirs(training_dir, exist_ok=True)

        # Save patterns
        with open(f"{training_dir}/patterns.json", "w") as f:
            json.dump(analyzer.analyze_results([]), f, indent=2, default=str)

        # Export fine-tuning data
        ok, msg = finetuner.export_jsonl(f"{training_dir}/finetuning_examples.jsonl")
        return ok, f"Training data saved. {msg}"
    except Exception as exc:
        return False, str(exc)


def load_training_data() -> tuple[InvoicePatternAnalyzer, FineStuningDataGenerator]:
    """Load previously saved training data."""
    analyzer = InvoicePatternAnalyzer()
    finetuner = FineStuningDataGenerator()

    try:
        with open("data/training/patterns.json", "r") as f:
            patterns = json.load(f)
            if patterns:
                analyzer.vendor_patterns = patterns.get("vendor_patterns", {})
                analyzer.category_statistics = patterns.get("category_statistics", {})
    except FileNotFoundError:
        pass

    return analyzer, finetuner
