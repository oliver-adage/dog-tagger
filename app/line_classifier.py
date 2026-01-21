from __future__ import annotations

"""
Simple, pluggable line classifier.
Extend or swap this module to integrate ML/NLP models.
"""

from typing import Any, Iterable,Sequence

try:
    # package import
    from .document_context import ClassifiedLine
except Exception:
    # fallback for direct execution
    from document_context import ClassifiedLine  # type: ignore

from transformers import pipeline


class HeuristicLineClassifier:
    def classify(self, line: ClassifiedLine) -> str:
        # placeholder rule: if line ends with digits, treat as amount line
        stripped = line.text.strip()
        if stripped and stripped[-1].isdigit():
            return "amount_line"
        return "other"



class BertLineClassifier:
    def __init__(self, model_name: str = "facebook/bart-large-mnli") -> None:
        # map human-readable descriptions → simple tags
        self.label_descriptions = {
            "item_line": "item",
            "total_line": "total",
            "balance_due": "balance due",
            "header": "supplier name or adress",
            "other": "not item, total or adress",
        }
        self.labels = list(self.label_descriptions.keys())

        self._clf = pipeline(
            task="zero-shot-classification",
            model=model_name,
        )

    def classify(self, line: ClassifiedLine) -> str:
        text = line.text.strip()
        if not text:
            return "other"

        result = self._clf(
            text,
            candidate_labels=list(self.label_descriptions.values()),
            multi_label=False,
        )

        # map back from description → tag
        best_desc = result["labels"][0]
        # invert the dict (return key that matches the best returned description)
        for tag, desc in self.label_descriptions.items():
            if desc == best_desc:
                return tag

        return "other"


