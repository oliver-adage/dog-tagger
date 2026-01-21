from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from document_context import DocumentContext

try:
    # package import
    from .DocumentLayout import DocumentLayout
except Exception:
    # fallback for direct execution
    from DocumentLayout import DocumentLayout


def build_document_context(
    document_path: Union[str, Path],
    classifier=None,
) -> DocumentContext:
    pdf_path = Path(document_path)
    layout = DocumentLayout.from_pdf(pdf_path)
    return DocumentContext.from_layout(layout, classifier=classifier)


if __name__ == "__main__":
    try:
        from .line_classifier import HeuristicLineClassifier
    except Exception:
        from line_classifier import HeuristicLineClassifier

    sample_path = Path("./data/raw").glob("*.pdf")
    for pdf_path in sorted(sample_path):
        ctx = build_document_context(pdf_path, classifier=HeuristicLineClassifier())
        print(f"{pdf_path.name}: {len(ctx.items)} lines, total={ctx.total:.2f}")

