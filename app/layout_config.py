"""
Layout grid configuration used to split PDF pages into structured regions.

The grid is expressed as normalized row/column slices to make it easy to
introduce multi-column layouts later (e.g., six or eight regions). For now,
we keep a single column and three rows (top, middle, bottom).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class GridSlice:
    """Normalized slice definition along one axis."""

    name: str
    start: float
    end: float


@dataclass(frozen=True)
class LayoutGrid:
    """Two-dimensional grid composed of row and column slices."""

    rows: Tuple[GridSlice, ...]
    columns: Tuple[GridSlice, ...]

    def multi_column(self) -> bool:
        return len(self.columns) > 1


LAYOUT_GRID = LayoutGrid(
    rows=(
        GridSlice("top", 0.0, 0.28),
        GridSlice("middle", 0.28, 0.72),
        GridSlice("bottom", 0.72, 1.0),
    ),
    columns=(
        # Single full-width column for now; add entries like ("left", 0.0, 0.5)
        # and ("right", 0.5, 1.0) to create multi-column grids later.
        GridSlice("full", 0.0, 1.0),
    ),
)

