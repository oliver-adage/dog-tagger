# define class document layout that saves layout information and text blocks that are extracted
# from pdfs and used to extract key information like supplier from header and total amount from body
# fields: metadata: dict with metadata information like author, title, creation date, pages, size
# pages: list of pages, each page is a list of text blocks
# text blocks: each text block has text content and layout information like position, font size, font style

# import list, union, dict from typing
from typing import List, Dict, Union, Tuple, Optional


def to_bbox_norm(
    bbox: Tuple[float, float, float, float],
    page_w: float,
    page_h: float,
    *,
    origin: str = "top-left",
    rotation: int = 0,
    clip: bool = True,
    precision: int = 6,
) -> Tuple[float, float, float, float]:
    """
    Normalize a PDF bbox to [0,1] coordinates with a top-left origin.

    Args:
        bbox: (x0, y0, x1, y1) in page coordinate space.
        page_w: Page width in points.
        page_h: Page height in points.
        origin: 'top-left' (default) or 'bottom-left' for the input bbox.
        rotation: Page rotation in degrees (0, 90, 180, 270).
        clip: Clamp coordinates to page extents before normalization.
        precision: Decimal places to round the normalized coords.

    Returns:
        (x0_n, y0_n, x1_n, y1_n) each in [0,1].
    """
    if page_w <= 0 or page_h <= 0:
        raise ValueError("page_w and page_h must be positive")

    x0, y0, x1, y1 = bbox
    # Order the box
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0

    # Convert origin to top-left if needed (pdfminer-like is bottom-left)
    if origin.lower() == "bottom-left":
        y0, y1 = page_h - y1, page_h - y0
    elif origin.lower() != "top-left":
        raise ValueError("origin must be 'top-left' or 'bottom-left'")

    # Apply rotation if coordinates are not rotation-aligned
    rot = rotation % 360
    if rot not in (0, 90, 180, 270):
        raise ValueError("rotation must be 0, 90, 180, or 270")

    pw, ph = page_w, page_h
    if rot == 90:
        # (x, y) -> (ph - y, x)
        x0, y0 = ph - y0, x0
        x1, y1 = ph - y1, x1
        pw, ph = page_h, page_w
    elif rot == 180:
        x0, y0 = pw - x0, ph - y0
        x1, y1 = pw - x1, ph - y1
    elif rot == 270:
        # (x, y) -> (y, pw - x)
        x0, y0 = y0, pw - x0
        x1, y1 = y1, pw - x1
        pw, ph = page_h, page_w

    # Re-order after rotation
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0

    # Clip to page bounds if requested
    if clip:
        x0 = max(0.0, min(pw, x0))
        x1 = max(0.0, min(pw, x1))
        y0 = max(0.0, min(ph, y0))
        y1 = max(0.0, min(ph, y1))

    # Normalize
    x0_n = x0 / pw
    x1_n = x1 / pw
    y0_n = y0 / ph
    y1_n = y1 / ph

    # Final order and rounding
    if x0_n > x1_n:
        x0_n, x1_n = x1_n, x0_n
    if y0_n > y1_n:
        y0_n, y1_n = y1_n, y0_n

    if precision is not None and precision >= 0:
        r = lambda v: round(v, precision)
        return (r(x0_n), r(y0_n), r(x1_n), r(y1_n))
    return (x0_n, y0_n, x1_n, y1_n)

class TextBlock:
    def __init__(self, bbox: tuple[float, float, float, float], text: str):
        self.bbox = bbox  # (x0, y0, x1, y1)
        self.text = text
        # Will be set by make_bbox_norm when page size is known
        self.bbox_norm: Optional[Tuple[float, float, float, float]] = None

    def make_bbox_norm(
        self,
        page_w: float,
        page_h: float,
        *,
        origin: str = "top-left",
        rotation: int = 0,
        precision: int = 6,
    ) -> Tuple[float, float, float, float]:
        """
        Compute and cache a standardized normalized bbox for this block.
        """
        self.bbox_norm = to_bbox_norm(
            self.bbox,
            page_w,
            page_h,
            origin=origin,
            rotation=rotation,
            precision=precision,
        )
        return self.bbox_norm


class PageLayout:
    def __init__(
        self,
        page_w: float,
        page_h: float,
        *,
        origin: str = "top-left",
        rotation: int = 0,
    ):
        self.page_w = page_w
        self.page_h = page_h
        self.origin = origin
        self.rotation = rotation
        self.text_blocks: List[TextBlock] = []

    def append(self, text_block: TextBlock):
        self.text_blocks.append(text_block)
        # Automatically compute normalized bbox when a block is added
        text_block.make_bbox_norm(
            self.page_w,
            self.page_h,
            origin=self.origin,
            rotation=self.rotation,
        )

class DocumentLayout:
    def __init__(self):
        self.metadata: Dict[str, str] = {}
        self.pages: List[PageLayout] = []

    def add_metadata(self, key: str, value: str):
        self.metadata[key] = value

    def add_page(self, page: PageLayout):
        # Ensure all existing blocks on the page have normalized boxes
        for block in page.text_blocks:
            if getattr(block, "bbox_norm", None) is None:
                block.make_bbox_norm(
                    page.page_w,
                    page.page_h,
                    origin=page.origin,
                    rotation=page.rotation,
                )
        self.pages.append(page)

    def add_text_block_to_page(self, page_index: int, text_block: TextBlock):
        if page_index < len(self.pages):
            self.pages[page_index].append(text_block)
        else:
            raise IndexError("Page index out of range")


if __name__ == "__main__":
    doc_layout = DocumentLayout()
    doc_layout.add_metadata("author", "John Doe")
    doc_layout.add_metadata("title", "Sample Document")

    # Create an A4 page in points: 595 x 842
    page1 = PageLayout(595.0, 842.0)
    tb1 = TextBlock((0, 0, 100, 50), "This is a header")
    tb2 = TextBlock((0, 60, 100, 200), "This is the body text of the document.")
    page1.append(tb1)
    page1.append(tb2)

    doc_layout.add_page(page1)

    print("Document Metadata:", doc_layout.metadata)
    for i, page in enumerate(doc_layout.pages):
        print(f"Page {i+1} Text Blocks:")
        for block in page.text_blocks:
            print(f"  BBox: {block.bbox}, BBox_norm: {block.bbox_norm}, Text: {block.text}")
