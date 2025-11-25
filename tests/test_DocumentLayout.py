from __future__ import annotations

import pytest

from app.DocumentLayout import DocumentLayout, PageLayout, TextBlock


@pytest.fixture()
def sample_layout() -> DocumentLayout:
    doc = DocumentLayout()
    doc.add_metadata("author", "Unit Test")
    doc.add_metadata("title", "Layout Smoke Test")

    page = PageLayout(200.0, 100.0)
    header = TextBlock((0, 0, 200, 20), "Header Text")
    body = TextBlock((0, 25, 200, 80), "Body Text\nwith multiple lines")
    page.append(header)
    page.append(body)
    doc.add_page(page)

    footer = TextBlock((0, 85, 200, 100), "Footer")
    doc.add_text_block_to_page(0, footer)

    return doc


def test_metadata_and_page_registration(sample_layout: DocumentLayout):
    page = sample_layout.pages[0]

    assert sample_layout.metadata["author"] == "Unit Test"
    assert sample_layout.metadata["title"] == "Layout Smoke Test"
    assert len(sample_layout.pages) == 1

    assert page.page_w == pytest.approx(200.0)
    assert page.page_h == pytest.approx(100.0)
    assert len(page.text_blocks) == 3


def test_text_blocks_have_normalized_bboxes(sample_layout: DocumentLayout):
    page = sample_layout.pages[0]

    for block in page.text_blocks:
        assert block.bbox_norm is not None, "Normalized bbox should be computed"
        x0, y0, x1, y1 = block.bbox_norm
        for coord in (x0, y0, x1, y1):
            assert 0.0 <= coord <= 1.0
        assert x0 <= x1 and y0 <= y1


def test_add_text_block_to_page_out_of_range():
    doc = DocumentLayout()
    page = PageLayout(100.0, 100.0)
    doc.add_page(page)

    with pytest.raises(IndexError):
        doc.add_text_block_to_page(5, TextBlock((0, 0, 10, 10), "oops"))
