
from __future__ import annotations

from typing import Dict, Optional

import numpy as np

from pixel_patrol_base.core.contracts import ChunkKind
from pixel_patrol_base.core.record import Record
from pixel_patrol_base.core.specs import RecordSpec


class TomatoRipenessProcessor:
    """Classifies tomato pixels by their ripeness.

    Tomato pixels are classified into three categories:
    unripe (green), mid-ripe (orange), and ripe (red).

    The processor analyzes RGB colors pixel by pixel.
    It does not identify individual tomatoes.
    """

    NAME = "tomato-ripeness"
    DESCRIPTION = "Counts tomato pixels by ripeness category."

    CHUNK_KIND = ChunkKind.MEMORY
    INPUT = RecordSpec(axes={"X", "Y"})
    OUTPUT = "features"

    OUTPUT_SCHEMA = {
        "unripe_tomato_pixels": int,
        "midripe_tomato_pixels": int,
        "ripe_tomato_pixels": int,
        "total_tomato_pixels": int,
    }

    OUTPUT_SCHEMA_PATTERNS = []

    OUTPUT_SCHEMA_DESCRIPTIONS = {
        "unripe_tomato_pixels": "Number of unripe green tomato pixels.",
        "midripe_tomato_pixels": "Number of mid-ripe orange tomato pixels.",
        "ripe_tomato_pixels": "Number of ripe red tomato pixels.",
        "total_tomato_pixels": "Total number of classified tomato pixels.",
    }

    def run_chunk(self, record: Record) -> Dict:
        arr = (
            record.data.compute()
            if hasattr(record.data, "compute")
            else np.asarray(record.data)
        )

        arr = np.asarray(arr)

        if arr.ndim != 3 or arr.shape[-1] != 3:
            raise ValueError(
                f"TomatoRipenessProcessor expects an RGB image "
                f"with shape (Y, X, 3), got {arr.shape}"
            )

        arr = arr.astype(np.float32)

        red = arr[:, :, 0]
        green = arr[:, :, 1]
        blue = arr[:, :, 2]

        # Identify tomato-like pixels.
        tomato_mask = (red > 120) & (red > blue)

        # Classify tomato pixels by dominant color.
        unripe_mask = tomato_mask & (green > red)
        midripe_mask = tomato_mask & (green <= red) & (green > 0.45 * red)
        ripe_mask = tomato_mask & (green <= 0.45 * red)

        unripe_count = int(np.sum(unripe_mask))
        midripe_count = int(np.sum(midripe_mask))
        ripe_count = int(np.sum(ripe_mask))

        total_count = unripe_count + midripe_count + ripe_count

        return {
            "unripe_tomato_pixels": unripe_count,
            "midripe_tomato_pixels": midripe_count,
            "ripe_tomato_pixels": ripe_count,
            "total_tomato_pixels": total_count,
        }

    def get_aggregation(self, col: str) -> Optional[callable]:
        count_columns = {
            "unripe_tomato_pixels",
            "midripe_tomato_pixels",
            "ripe_tomato_pixels",
            "total_tomato_pixels",
        }

        if col not in count_columns:
            return None

        return lambda rows, g_dims: sum(
            row[col] for row in rows
        )
