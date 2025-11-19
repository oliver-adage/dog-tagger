# Module that handles PDF processing and text extraction
# Contains functions to extract text from PDF files using different backends
# and to list documents in a directory.
# creates a clean dictionary of extracted texts from PDF files.

from pathlib import Path
from typing import Union, Dict

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


def _extract_layout_from_pdf(path: Union[str,Path]) -> DocumentLayout:


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
