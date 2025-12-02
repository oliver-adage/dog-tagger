from pathlib import Path
from DocumentLayout import DocumentLayout


def test_from_pdf_returns_document_layout():
    sample_pdf = Path("./data/raw/Betalningsintyg.pdf")
    layout = DocumentLayout.from_pdf(sample_pdf)

    assert layout.path == sample_pdf
    assert len(layout.pages) >= 1
    assert len(layout.blocks) >= 1


def test_pages_have_consistent_numbers_and_blocks():
    sample_pdf = Path("./data/raw/Betalningsintyg.pdf")
    layout = DocumentLayout.from_pdf(sample_pdf)

    for page in layout.pages:
        assert page.number >= 1
        for block in page.blocks:
            # block.page must match its parent
            assert block.page == page.number
            # bbox must be 4-tuple
            assert len(block.bbox) == 4
            # no empty text blocks
            assert block.text.strip() != ""
