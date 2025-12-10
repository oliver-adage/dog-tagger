from __future__ import annotations

import re
from typing import List
from pathlib import Path
from dataclasses import dataclass, field

from pydantic import BaseModel

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

    @classmethod
    def from_layout(cls, layout: DocumentLayout) -> "DocumentContext":
        items: List[ClassifiedLine] = []
        amount_re = re.compile(r"(-?\d{1,3}(?:[ \u00A0]\d{3})*(?:[.,]\d{2})|-?\d+(?:[.,]\d{2}))\s*$")

        for page in layout.pages:
            for line in page.lines:
                match = amount_re.search(line.text)
                if not match:
                    continue

                items.append(
                    ClassifiedLine(
                        page=page.number,
                        line_number=line.number,
                        text=line.text,
                        bbox=line.bbox,
                    )
                )

        return cls(layout=layout, items=items)

    def classify_lines(self, classifier) -> None:
        """
        Classify each extracted line using an external classifier.
        The classifier can be any callable or object with `classify(line)` method.
        """
        for line in self.items:
            if hasattr(classifier, "classify"):
                line.classification = classifier.classify(line)
            else:
                line.classification = classifier(line)


if __name__ == "__main__":
    try:
        from .line_classifier import HeuristicLineClassifier
    except Exception:
        from line_classifier import HeuristicLineClassifier

    raw_dir = Path("./data/raw")
    for pdf_path in sorted(raw_dir.glob("*.pdf")):
        print(f"\n=== {pdf_path.name} ===")
        layout = DocumentLayout.from_pdf(pdf_path)
        ctx = DocumentContext.from_layout(layout)
        ctx.classify_lines(HeuristicLineClassifier())
        if not ctx.items:
            print("No lines with detectable trailing amounts.")
            continue
        print(f"Found {len(ctx.items)} extracted lines:")
        for item in ctx.items:
            print(
                f"page {item.page} line {item.line_number}: "
                f"text='{item.text}' bbox={item.bbox} class={item.classification}"
            )
