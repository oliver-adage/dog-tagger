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


def _extract_text_from_pdf(path: Path) -> str:
    """Extract text from a PDF using the available backend."""
    if _PDF_BACKEND == "pymupdf":
        parts: list[str] = []
        with fitz.open(path) as doc:  # type: ignore[name-defined]
            for page in doc:
                parts.append(page.get_text("text"))
        return "\n".join(parts)
    if _PDF_BACKEND == "pdfminer":
        return _pdfminer_extract_text(str(path))  # type: ignore[name-defined]
    raise RuntimeError("No PDF backend available. Install 'pymupdf' or 'pdfminer.six'.")


def _select_slice(value: float, slices: Sequence[GridSlice]) -> GridSlice:
    """
    Return the slice whose normalized [start, end) range contains ``value``.
    Falls back to the last slice when rounding pushes the value to the edge.
    """
    epsilon = 1e-6
    for slice_def in slices:
        upper = slice_def.end + (epsilon if slice_def.end == 1.0 else 0.0)
        if slice_def.start <= value < upper:
            return slice_def
    return slices[-1]


def _extract_layout_from_pdf(path: Union[str, Path]) -> DocumentLayout:
    """
    Extract a structured layout from a PDF and split each page into
    coarse regions (top, middle, bottom).
    """
    pdf_path = Path(path)
    if not pdf_path.exists() or not pdf_path.is_file():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    if _PDF_BACKEND != "pymupdf":
        raise RuntimeError("Layout extraction currently requires PyMuPDF.")

    layout = DocumentLayout()
    layout.add_metadata("file_name", pdf_path.name)
    layout.add_metadata("pdf_backend", _PDF_BACKEND)

    with fitz.open(pdf_path) as doc:  # type: ignore[name-defined]
        metadata = doc.metadata or {}
        for key, value in metadata.items():
            if value:
                layout.add_metadata(key, str(value))
        layout.add_metadata("page_count", str(doc.page_count))

        for page in doc:
            page_w = float(page.rect.width)
            page_h = float(page.rect.height)
            page_layout = PageLayout(
                page_w,
                page_h,
                origin="top-left",
                rotation=int(page.rotation),
            )

            region_map: dict[str, dict[str, Any]] = {}
            for row in LAYOUT_GRID.rows:
                for column in LAYOUT_GRID.columns:
                    region_key = f"{row.name}:{column.name}"
                    region_map[region_key] = {
                        "bbox": (
                            column.start * page_w,
                            row.start * page_h,
                            column.end * page_w,
                            row.end * page_h,
                        ),
                        "texts": [],
                        "label": f"{row.name}-{column.name}",
                    }

            for block in page.get_text("blocks"):
                if len(block) < 5:
                    continue
                x0, y0, x1, y1, block_text = block[:5]
                text = (block_text or "").strip()
                if not text:
                    continue
                cx_norm = ((x0 + x1) / 2.0) / page_w if page_w else 0.0
                cy_norm = ((y0 + y1) / 2.0) / page_h if page_h else 0.0
                row_slice = _select_slice(cy_norm, LAYOUT_GRID.rows)
                column_slice = _select_slice(cx_norm, LAYOUT_GRID.columns)
                key = f"{row_slice.name}:{column_slice.name}"
                region_map[key]["texts"].append(text)

            for region in region_map.values():
                texts = region.get("texts", [])
                if not texts:
                    continue
                combined_text = "\n".join(texts)
                bbox = region["bbox"]
                block = TextBlock(bbox, combined_text)
                page_layout.append(block)

            layout.add_page(page_layout)

    return layout


def extract_text_from_file(file_path: Union[str, Path]) -> str:
    """
    Extract text from a file if it is a PDF. Non-PDF files are ignored.

    Args:
        file_path: Path to the file.

    Returns:
        Extracted text for PDFs, otherwise an empty string.
    """
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    if path.suffix.lower() == ".pdf":
        return _extract_text_from_pdf(path)

    print(f"Ignoring non-PDF file: {path.name}")
    return ""
    


def extract_text_from_files(
    file_names: list[str], folder_path: str = "./data/raw/"
) -> Dict[str, str]:
    """
    Extract text content from multiple files. Non-PDFs are skipped.

    Args:
        file_names: List of file names.
        folder_path: Directory containing the files.

    Returns:
        Dict[file_name, text]: Only includes entries with extracted text.
    """
    base = Path(folder_path)
    if not base.exists() or not base.is_dir():
        print()
        raise FileNotFoundError(f"Directory not found: {folder_path}")

    texts: Dict[str, str] = {}
    for name in file_names:
        text = extract_text_from_file(base / name)
        if text:
            texts[name] = text
    return texts
