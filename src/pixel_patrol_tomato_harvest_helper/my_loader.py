
from pathlib import Path
from typing import Any, Dict, Iterator, List, Set, Tuple

import numpy as np

from pixel_patrol_base.core.contracts import FileInfo
from pixel_patrol_base.core.record import Record, record_from


class TomatoLoader:
    """Reads a tomato RGB image and its season metadata from an NPZ file.

    Each file contains a 32x32 RGB pixel array and a season value
    (spring, summer, autumn or winter).
    """

    NAME = "tomato"
    DESCRIPTION = "Reads tomato RGB images and season metadata from NPZ files."

    SUPPORTED_EXTENSIONS: Set[str] = {"npz"}
    FOLDER_EXTENSIONS: Set[str] = set()
    CONTAINER_EXTENSIONS: Set[str] = set()

    OUTPUT_SCHEMA: Dict[str, Any] = {"season": str}
    OUTPUT_SCHEMA_PATTERNS: List[tuple] = []
    OUTPUT_SCHEMA_DESCRIPTIONS: Dict[str, str] = {
        "season": "Season associated with the tomato image.",
    }

    def is_folder_supported(self, path: Path) -> bool:
        return False

    def read_header(self, file_path: Path) -> FileInfo:
        with np.load(file_path, allow_pickle=False) as data:
            pixels = data["image"]
            return FileInfo(shape=pixels.shape, dtype=pixels.dtype, dim_order="YXC")

    def load(self, file_path: Path) -> Record:
        with np.load(file_path, allow_pickle=False) as data:
            pixels = data["image"]
            season = str(data["season"].item())

        meta = {"season": season, "dim_order": "YXC", "channel_names": ["R", "G", "B"]}
        return record_from(pixels, meta, kind="intensity")

    def load_range(self, file_path: Path, start: int, stop: int) -> Iterator[Tuple[str, Record]]:
        raise NotImplementedError("tomato is not a container format")