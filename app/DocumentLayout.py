from __future__ import annotations
# define class document layout that saves layout information and text lines that are extracted
# from pdfs and used to extract key information like supplier from header and total amount from body
# fields: metadata: dict with metadata information like author, title, creation date, pages, size
# pages: list of pages, each page is a list of text lines with coordinates

# import list, union, dict from typing
from typing import List, Tuple

# Prefer fast PDF extraction via PyMuPDF; fallback to pdfminer.six
try:
    import fitz  # type: ignore  # PyMuPDF
    _PDF_BACKEND = "pymupdf"
except Exception:
    try:
        from pdfminer.high_level import extract_text as _pdfminer_extract_text  # type: ignore
        _PDF_BACKEND = "pdfminer"
    except Exception:
        _PDF_BACKEND = None


from pathlib import Path
from pydantic import BaseModel


BBox = Tuple[float, float, float, float]   # (x0, y0, x1, y1)


class Line(BaseModel):
    page: int                 # 1-based page number
    number: int               # 1-based line number on the page
    bbox: BBox                # coordinates covering all words in the line
    text: str                 # cleaned text content for the line


class Page(BaseModel):
    number: int               # 1-based page number
    lines: List[Line]
    width: float
    height: float


class DocumentLayout(BaseModel):
    path: Path
    pages: List[Page]

    @property
    def lines(self) -> List[Line]:
        """Convenience: all lines in document as a flat list."""
        return [line for page in self.pages for line in page.lines]
    
    @classmethod
    def from_pdf(cls, path: Path) -> DocumentLayout:
        """Build a DocumentLayout from a PDF using the configured backend."""
        if _PDF_BACKEND != "pymupdf":
            raise RuntimeError(
                "No PDF backend available for layout. "
                "Install 'pymupdf' or add another backend."
            )

        pages: List[Page] = []

        with fitz.open(path) as doc:  # type: ignore[name-defined]
            for page_no, page in enumerate(doc, start=1):
                raw_words = page.get_text("words", sort=True)
                rect = page.rect
                page_lines: List[Line] = []
                # merge words that sit on the same horizontal line, regardless of block
                line_merge_tolerance = 1.5  # points; small tolerance for float drift
                current_line_words: List[Tuple[float, float, float, float, str]] = []
                current_center_y: float | None = None

                for (x0, y0, x1, y1, word, _block_no, _line_no, _word_no) in raw_words:
                    cleaned = str(word).strip()
                    if not cleaned:
                        continue

                    center_y = (y0 + y1) / 2.0

                    if (
                        current_center_y is None
                        or abs(center_y - current_center_y) <= line_merge_tolerance
                    ):
                        current_line_words.append((x0, y0, x1, y1, cleaned))
                        # update center to the average to gently follow float drift
                        if current_center_y is None:
                            current_center_y = center_y
                        else:
                            current_center_y = (current_center_y * (len(current_line_words) - 1) + center_y) / len(current_line_words)
                    else:
                        # flush previous line
                        x0s, y0s, x1s, y1s, word_texts = zip(*current_line_words)
                        line_bbox: BBox = (min(x0s), min(y0s), max(x1s), max(y1s))
                        line_text = " ".join(word_texts)
                        page_lines.append(
                            Line(
                                page=page_no,
                                number=len(page_lines) + 1,
                                bbox=line_bbox,
                                text=line_text,
                            )
                        )
                        current_line_words = [(x0, y0, x1, y1, cleaned)]
                        current_center_y = center_y

                # flush trailing line
                if current_line_words:
                    x0s, y0s, x1s, y1s, word_texts = zip(*current_line_words)
                    line_bbox: BBox = (min(x0s), min(y0s), max(x1s), max(y1s))
                    line_text = " ".join(word_texts)
                    page_lines.append(
                        Line(
                            page=page_no,
                            number=len(page_lines) + 1,
                            bbox=line_bbox,
                            text=line_text,
                        )
                    )
                    current_line_words = []
                    current_center_y = None

                pages.append(Page(
                    number=page_no, 
                    lines=page_lines,
                    width=rect.width,
                    height=rect.height,))

        return cls(path=path, pages=pages)


if __name__ == "__main__":
    try:
        # when run as a package
        from .document_context import DocumentContext
    except Exception:
        # fallback for direct execution
        from document_context import DocumentContext

    raw_dir = Path("./data/raw")
    for pdf_path in sorted(raw_dir.glob("*.pdf")):
        print(f"\n=== {pdf_path.name} ===")
        layout = DocumentLayout.from_pdf(pdf_path)
        context = DocumentContext.from_layout(layout)

        for page in layout.pages:
            print(f"\nPage {page.number} lines:")
            for line in page.lines:
                print(line.number, line.bbox, line.text)

        if context.items:
            print("\nExtracted lines with detected amounts:")
            for item in context.items:
                print(
                    f"page {item.page} line {item.line_number}: "
                    f"text='{item.text}' bbox={item.bbox}"
                )
