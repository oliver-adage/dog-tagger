# Module that handles PDF processing and text extraction
# Contains functions to extract text from PDF files using different backends
# and to list documents in a directory.
# creates a clean dictionary of extracted texts from PDF files.

from pathlib import Path
from typing import Any, Dict, Sequence, Union

try:  # Prefer package-style imports when available.
    from app.DocumentLayout import DocumentLayout, PageLayout, TextBlock
    from app.layout_config import LAYOUT_GRID, GridSlice
except ImportError:  # Fallback for scripts executed from within the app folder.
    from DocumentLayout import DocumentLayout, PageLayout, TextBlock  # type: ignore
    from layout_config import LAYOUT_GRID, GridSlice  # type: ignore

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

def list_documents(path: str = "./data/raw/") -> list[str]:
    """
    Lists all files in the specified directory.

    Args:
        path (str): Directory path containing documents.

    Returns:
        list[str]: List of file names (not full paths).
    """
    doc_path = Path(path)
    if not doc_path.exists() or not doc_path.is_dir():
        print()
        raise FileNotFoundError(f"Directory not found: {path}")
    
    return [f.name for f in doc_path.iterdir() if f.is_file()]



def _extract_text_as_block(path: Path) -> DocumentLayout:
    """Legacy-style helper that now returns a DocumentLayout."""
    return DocumentLayout.from_pdf(path)


# test for one pdf file
if __name__ == "__main__":
    sample_pdf_path = Path("./data/raw/Betalningsintyg.pdf")
    layout = _extract_text_as_block(sample_pdf_path)

    print(f"Document: {layout.path.name}")
    print(f"Pages: {len(layout.pages)}")
    print(f"Total blocks: {len(layout.blocks)}")

    # Print first few blocks of first page
    first_page = layout.pages[0]
    for block in first_page.blocks[:5]:
        print("----")
        print(f"page={block.page}, idx={block.index}, bbox={block.bbox}")
        print(block.text)