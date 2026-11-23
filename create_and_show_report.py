
"""
Minimal extension example.

Shows how a PixelPatrol extension adds a custom loader and processor (Python)
and viewer plugins (JavaScript) to the browser-based viewer.

The "Tomato Harvest Helper" dataset contains eight synthetic 32x32 RGB images
stored as NPZ files, organized into greenhouse and outdoors folders.
Each file stores the RGB pixel data and its season, which TomatoLoader
extracts directly from the NPZ file.

Steps
-----
1. Generate the tiny dataset (skipped if it already exists).
2. Process the NPZ images with the custom loader and processor.
The processor adds pixel counts for unripe, midripe and ripe tomatoes,
as well as a total tomato pixel count.
3. Serve the report with the viewer. The server auto-discovers viewer
extensions from installed packages (``pixel_patrol.viewer_extensions``
entry-point group) and loads the JS plugins bundled with this package.

Usage
-----
Install the package with uv, then run:

    uv run python create_and_show_report.py
"""

from pathlib import Path

from pixel_patrol_base.api import create_project, add_paths, process_files
from pixel_patrol_base.viewer_server import serve_viewer

from make_dataset import main as make_dataset, DESCRIPTION

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    data_dir = HERE / "data"
    if not data_dir.exists():
        make_dataset()

    output = HERE / "out" / "report.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)

    project = create_project(
        "Tomato Harvest Helper",
        data_dir,
        loader="tomato",
        output_path=output,
    )

    project = add_paths(project, ["greenhouse", "outdoors"])

    # The project description is shown below the title in the viewer
    # and stored in the report metadata, separately from the NPZ metadata.
    project = process_files(project, description=DESCRIPTION)

    serve_viewer(output)