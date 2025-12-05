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
    wdith: float
    height: float


class DocumentLayout(BaseModel):
    path: Path
    pages: List[Page]

    @property
    def blocks(self) -> List[Block]:
        """Convenience: all blocks in document as a flat list."""
        return [b for page in self.pages for b in page.blocks]
    
    def page_regions(
        self,
        header_ratio: float = 0.2,
        footer_ratio: float = 0.2,
    ) -> Dict[int, Dict[str, List[Block]]]:
        """
        For each page number, return its header/body/footer blocks.
        """
        regions: Dict[int, Dict[str, List[Block]]] = {}
        for page in self.pages:
            regions[page.number] = split_page_into_regions(
                page,
                header_ratio=header_ratio,
                footer_ratio=footer_ratio,
            )
        return regions

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
                rect = page.rect
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

                pages.append(Page(
                    number=page_no, 
                    blocks=page_blocks,
                    wdith=rect.width,
                    height=rect.height,))

        return cls(path=path, pages=pages)


from typing import Dict

def split_page_into_regions(
    page: Page,
    header_ratio: float = 0.2,
    footer_ratio: float = 0.2,
) -> Dict[str, List[Block]]:
    """
    Split a Page into header / body / footer by vertical position.
    Uses the vertical centre of each block.
    """
    h = page.height
    header_max_y = h * header_ratio
    footer_min_y = h * (1.0 - footer_ratio)

    header: List[Block] = []
    body: List[Block] = []
    footer: List[Block] = []

    for block in page.blocks:
        _, y0, _, y1 = block.bbox
        center_y = (y0 + y1) / 2.0

        if center_y <= header_max_y:
            header.append(block)
        elif center_y >= footer_min_y:
            footer.append(block)
        else:
            body.append(block)

    return {"header": header, "body": body, "footer": footer}


if __name__ == "__main__":
    sample_pdf_path = Path("./data/raw/Betalningsintyg.pdf")
    layout = DocumentLayout.from_pdf(sample_pdf_path)

    regions_by_page = layout.page_regions()

    first_page_regions = regions_by_page[1]
    print("Header blocks on page 1:")
    for b in first_page_regions["header"]:
        print(b.bbox, b.text)

    print("\nFooter blocks on page 1:")
    for b in first_page_regions["footer"]:
        print(b.bbox, b.text)

