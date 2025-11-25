from __future__ import annotations
# define class document layout that saves layout information and text blocks that are extracted
# from pdfs and used to extract key information like supplier from header and total amount from body
# fields: metadata: dict with metadata information like author, title, creation date, pages, size
# pages: list of pages, each page is a list of text blocks
# text blocks: each text block has text content and layout information like position, font size, font style

# import list, union, dict from typing
from typing import List, Dict, Union, Tuple, Optional

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
from typing import Any, List, Tuple
from pydantic import BaseModel


BBox = Tuple[float, float, float, float]   # (x0, y0, x1, y1)


class Block(BaseModel):
    page: int                 # 1-based page number
    index: int                # block index on that page
    bbox: BBox                # coordinates on the page
    text: str                 # cleaned text content


class Page(BaseModel):
    number: int               # 1-based page number
    blocks: List[Block]


class DocumentLayout(BaseModel):
    path: Path
    pages: List[Page]

    @property
    def blocks(self) -> List[Block]:
        """Convenience: all blocks in document as a flat list."""
        return [b for page in self.pages for b in page.blocks]

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
                raw_blocks = page.get_text("blocks")
                page_blocks: List[Block] = []

                for (x0, y0, x1, y1, text, block_idx, block_type) in raw_blocks:
                    # keep only text blocks
                    if block_type != 0:
                        continue

                    cleaned = text.strip()
                    if not cleaned:
                        continue

                    page_blocks.append(
                        Block(
                            page=page_no,
                            index=block_idx,
                            bbox=(x0, y0, x1, y1),
                            text=cleaned,
                        )
                    )

                pages.append(Page(number=page_no, blocks=page_blocks))

        return cls(path=path, pages=pages)


if __name__ == "__main__":
    sample_pdf_path = Path("./data/raw/Betalningsintyg.pdf")
    layout = DocumentLayout.from_pdf(sample_pdf_path)

    print(f"Document: {layout.path.name}")
    print(f"Pages: {len(layout.pages)}")
    print(f"Total blocks: {len(layout.blocks)}")

    # Print first few blocks of first page
    first_page = layout.pages[0]
    for block in first_page.blocks[:5]:
        print("----")
        print(f"page={block.page}, idx={block.index}, bbox={block.bbox}")
        print(block.text)
