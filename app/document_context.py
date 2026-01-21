from __future__ import annotations

import re
import warnings
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

try:
    # package import
    from .DocumentLayout import DocumentLayout, BBox
except Exception:
    # fallback for direct execution
    from DocumentLayout import DocumentLayout, BBox


@dataclass
class ClassifiedLine:
    page: int                      # 1-based page number from originating line
    line_number: int               # line number on that page
    text: str                      # full line text (as extracted)
    bbox: BBox                     # reuse line bbox
    classification: str = field(default="unclassified")  # label assigned by classifier


class DocumentContext(BaseModel):
    layout: DocumentLayout
    items: List[ClassifiedLine]
    total: float = 0.0
    item_totals: Dict[str, float] = Field(default_factory=dict)

    @staticmethod
    def _parse_amount(raw: str) -> Optional[float]:
        cleaned = raw.replace(" ", "").replace("\u00A0", "")
        if not cleaned:
            return None

        sign = ""
        if cleaned[0] == "-":
            sign = "-"
            cleaned = cleaned[1:]

        last_comma = cleaned.rfind(",")
        last_dot = cleaned.rfind(".")
        decimal_index = max(last_comma, last_dot)

        if decimal_index >= 0:
            integer_part = cleaned[:decimal_index].replace(",", "").replace(".", "")
            fraction_part = cleaned[decimal_index + 1 :]
            normalized = f"{sign}{integer_part}.{fraction_part}"
        else:
            normalized = f"{sign}{cleaned.replace(',', '').replace('.', '')}"

        try:
            return float(normalized)
        except ValueError:
            return None

    @classmethod
    def from_layout(cls, layout: DocumentLayout, classifier=None) -> "DocumentContext":
        items: List[ClassifiedLine] = []
        item_totals: Dict[str, float] = {}
        last_total_amount: Optional[float] = None
        amount_re = re.compile(r"(-?\d{1,3}(?:[ \u00A0]\d{3})*(?:[.,]\d{2})|-?\d+(?:[.,]\d{2}))\s*$")

        for page in layout.pages:
            for line in page.lines:
                match = amount_re.search(line.text)
                if not match:
                    continue

                classified = ClassifiedLine(
                    page=page.number,
                    line_number=line.number,
                    text=line.text,
                    bbox=line.bbox,
                )
                if classifier is not None:
                    if hasattr(classifier, "classify"):
                        classified.classification = classifier.classify(classified)
                    else:
                        classified.classification = classifier(classified)

                items.append(classified)

                amount = cls._parse_amount(match.group(1))
                if amount is not None:
                    if classifier is None or classified.classification == "item_line":
                        name = line.text[: match.start()].strip()
                        if name:
                            item_totals[name] = item_totals.get(name, 0.0) + amount
                    if classifier is not None and classified.classification == "total_line":
                        last_total_amount = amount

        sum_items = sum(item_totals.values())
        if last_total_amount is not None:
            total = last_total_amount
            if abs(sum_items - total) > 0.01:
                warnings.warn(
                    f"Item sum {sum_items:.2f} does not match total {total:.2f}.",
                    RuntimeWarning,
                )
        else:
            total = sum_items
        return cls(layout=layout, items=items, total=total, item_totals=item_totals)

if __name__ == "__main__":
    try:
        from .line_classifier import HeuristicLineClassifier
    except Exception:
        from line_classifier import HeuristicLineClassifier

    raw_dir = Path("./data/raw")
    for pdf_path in sorted(raw_dir.glob("*.pdf")):
        print(f"\n=== {pdf_path.name} ===")
        layout = DocumentLayout.from_pdf(pdf_path)
        ctx = DocumentContext.from_layout(layout, classifier=HeuristicLineClassifier())
        if not ctx.items:
            print("No lines with detectable trailing amounts.")
            continue
        print(f"Found {len(ctx.items)} extracted lines:")
        for item in ctx.items:
            print(
                f"page {item.page} line {item.line_number}: "
                f"text='{item.text}' bbox={item.bbox} class={item.classification}"
            )
