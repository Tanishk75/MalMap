"""Heatmap-to-source-byte resolution (Module Interface Spec Section 6, ADR-0008).

gradcam_explain and map_ranges_to_pe_sections need a real trained model and a
real PE, respectively, and are out of reach before Milestone 1/7 data exists.
heatmap_to_byte_ranges needs neither -- only the offset map image_prep already
writes -- so it can be built and tested now, and doing so is the only way to
check that the offset map actually carries what this function needs.
"""

from __future__ import annotations

import numpy as np


def heatmap_to_byte_ranges(
    heatmap: np.ndarray, offset_map: dict
) -> list[tuple[int, int, float]]:
    """Resolves heatmap coordinates to (start_offset, end_offset, score) in the
    SOURCE file, using the map cached beside the tensor (ADR-0008).

    Granularity is coarse for large files -- one heatmap pixel can average
    many source bytes across several natural-resolution rows -- and each
    returned range reflects exactly the byte span its pixel maps to, rather
    than implying byte-level precision the resize already discarded.
    """
    target_h, target_w = offset_map["target_shape"]
    if heatmap.shape != (target_h, target_w):
        raise ValueError(
            f"heatmap shape {heatmap.shape} does not match offset_map "
            f"target_shape {(target_h, target_w)}"
        )

    height = offset_map["natural_height"]
    width = offset_map["reshape_width"]
    original_length = offset_map["original_length"]
    row_scale = height / target_h
    col_scale = width / target_w

    ranges: list[tuple[int, int, float]] = []
    for r in range(target_h):
        natural_row = int(r * row_scale)
        row_start = natural_row * width
        for c in range(target_w):
            col_start = int(c * col_scale)
            col_end = max(int((c + 1) * col_scale), col_start + 1)

            start_offset = min(row_start + col_start, original_length)
            end_offset = min(row_start + col_end, original_length)
            if start_offset < end_offset:
                ranges.append((start_offset, end_offset, float(heatmap[r, c])))

    return ranges
