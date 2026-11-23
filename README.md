# Minimal Extension Example - Tomato Harvest Helper

<img src="assets/tomato.png" alt="A happy little cartoon tomato" width="260" align="right">

A guide to building your own PixelPatrol extension - shown here as a
complete, self-contained example. It walks through the **entire** extension
surface: a custom **loader**, a custom **processor**, and two custom
**viewer widgets** (both visualising loader metadata and processor output).

**You almost certainly don't need all four.** A loader, a processor, and a
viewer widget are independent - ship just the one you need and skip the rest.
"[Defining the package](#defining-the-package)" shows how each is declared
on its own.

```
minimal-extension/
├── src/
│   └── pixel_patrol_tomato_harvest_helper/
│       ├── my_loader.py          custom loader
│       ├── my_processor.py       custom processor
│       ├── plugin_registry.py    registers loader, processor & viewer extension
│       └── viewer/               custom viewer widgets
└── pyproject.toml
```

(There are a few more files in the folder - a script that generates a tiny
toy dataset and one that runs the pipeline end to end - but those are just
helpers, not part of the extension itself.)

---

## The loader

**If PixelPatrol can't read your file format - or doesn't read it (and its
metadata) the way you want - write a loader extension.**

`src/pixel_patrol_tomato_harvest_helper/my_loader.py` implements `TomatoLoader`
(name: `tomato`).

A loader is any class that satisfies the `PixelPatrolLoader` protocol from
`pixel_patrol_base.core.contracts` - a [`typing.Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol),
not a base class, so `TomatoLoader` needs no import or inheritance from
`pixel_patrol_base`; matching the shape below is enough. It needs:

| Member | Type | Required? | Purpose |
|---|---|---|---|
| `NAME` | `str` | yes | unique identifier passed to `create_project(..., loader=...)` |
| `SUPPORTED_EXTENSIONS` | `set[str]` | yes | file extensions this loader can read (lower-case, no dot) |
| `OUTPUT_SCHEMA` | `dict[str, type]` | yes | extra metadata columns this loader adds to the table, with their types |
| `read_header(path)` | `(Path) -> FileInfo` | yes | cheap shape/dtype/dim-order probe, **no pixel data loaded** |
| `load(path)` | `(Path) -> Record` | yes | loads one image and returns a `Record` |
| `load_range(path, start, stop)` | `(Path, int, int) -> Iterator[(str, Record)]` | yes | yields sub-images for container formats; raise `NotImplementedError` otherwise |
| `FOLDER_EXTENSIONS` | `set[str]` | no - defaults to empty | "extensions" that mark a *folder* as a single loadable unit (e.g. OME-Zarr stores) |
| `CONTAINER_EXTENSIONS` | `set[str]` | no - defaults to empty | extensions that may contain more than one image (multi-series OME-TIFF, LMDB, ...) |
| `OUTPUT_SCHEMA_PATTERNS` | `list[tuple[str, type]]` | no - defaults to empty | regex/type pairs for dynamically-named metadata columns (e.g. `pixel_size_X`) |
| `is_folder_supported(path)` | `(Path) -> bool` | no - only if `FOLDER_EXTENSIONS` is non-empty | whether a *folder* (not a file) should be treated as one image |

`dim_order` is the only metadata field that must be correct - `shape`/`dtype` are always derived from the pixel array, not from `meta`. The pipeline also overwrites `ndim`, `num_pixels`, `size_<axis>`, `dim_<axis>`, and the filesystem columns (`path`, `name`, `type`, `parent`, `depth`, `size_bytes`, `file_extension`, `modification_date`, `imported_path`, `common_base`, `child_id`) after loading, so don't bother setting these. `OUTPUT_SCHEMA` is documentation only: any other field in `meta` reaches the table whether or not it's declared there, so a loader can pass through metadata fields it doesn't fully understand.

In our toy example here, `TomatoLoader` reads a `.npz` file with NumPy,
extracts its 32x32 RGB `uint8` pixel array and the `season` metadata
(spring, summer, autumn or winter), and wraps it all with
`record_from(..., kind="intensity")` - the `kind` is what lets the *built-in*
processors (basic metrics, histogram, thumbnail) pick the patches up
automatically too, right alongside our custom one.

---

## The processor

**If you want to compute a metric on images - any images, regardless of who
loaded them - write a processor extension.**

`src/pixel_patrol_tomato_harvest_helper/my_processor.py` implements `TomatoRipenessProcessor`
(name: `tomato-ripeness`).

A processor is any class that satisfies the `PixelPatrolProcessor` protocol -
every member below is required:

| Member | Type | Purpose |
|---|---|---|
| `NAME` | `str` | unique identifier (shown in pipeline logs) |
| `CHUNK_KIND` | `ChunkKind` | `LEAF` (user-configured tiles/slices) or `MEMORY` (whole record, memory-safe chunking) |
| `INPUT` | `RecordSpec` | which records this processor runs on (`kinds`, `axes`, `capabilities`, ...) |
| `OUTPUT` | `"features" \| "record"` | whether `run_chunk` returns columns to merge, or a brand-new `Record` |
| `OUTPUT_SCHEMA` | `dict[str, type]` | the columns this processor adds, with their types |
| `run_chunk(record)` | `(Record) -> dict` | does the actual computation on one chunk |
| `get_aggregation(name)` | `(str) -> Callable \| None` | how to combine multiple chunks' values for column `name` into the per-image value |

In our toy example here, `TomatoRipenessProcessor` analyses the RGB
pixel data of tomato images and adds four integer columns:
`unripe_tomato_pixels`, `midripe_tomato_pixels`, `ripe_tomato_pixels`,
and `total_tomato_pixels`. It classifies tomato-colored pixels by their
RGB values and counts the pixels in each ripeness category - not the
number of individual tomatoes. The synthetic images contain green-yellow
(unripe), orange (midripe) and red (ripe) tomatoes.

Notice `TomatoRipenessProcessor` never imports or refers to `TomatoLoader` by
name - it only declares the *kind* of image record it needs and processes
matching records regardless of which loader produced them.

---

## The viewer widgets

**If you want to visualise your data as an interactive report in the browser - your own extension's
columns or anyone else's - write a viewer widget.**

`src/pixel_patrol_tomato_harvest_helper/viewer/` ships **two** widgets:

- **`plugin_tomato_pixel_count.js`** ("Tomato Pixels by Season") visualises
  a **metric derived from the pixel data**: a scatter plot of
  `total_tomato_pixels` (computed by `TomatoRipenessProcessor`) against
  `season`, split by growing environment (`greenhouse` or `outdoors`).
  A scatter rather than a box/violin plot is used because each season
  contains only a handful of observations.
- **`plugin_tomato_ripeness.js`** ("Tomato Ripeness by Season") visualises
  the proportions of unripe, midripe and ripe tomato pixels as a
  100%-stacked bar chart, with greenhouse and outdoors shown side by side
  for each season.

The `season` metadata comes from `TomatoLoader`, while the growing
environment comes from the folder structure and is available as `parent0`
in the report. Both widgets are auto-discovered through
`viewer/extension.json` and declare `group: 'Tomato Harvest Helper'` so they
appear in their own sidebar section instead of "Other Widgets".

A plugin is a JS module that exports a single default object:

```js
export default {
  id:    'my-widget',          // unique across all loaded plugins
  label: 'My Widget',          // shown in the sidebar widget list
  group: 'My Extension Name',  // optional - gives the widget its own sidebar section
  scope: 'image',              // optional - 'file' | 'image' | 'slice', shown as a badge
                               // describing what one datapoint in this widget represents.
                               // If render() changes this at runtime (e.g. a "Slice by"
                               // toggle), call ctx.plot.setScopeBadge(el, scope) to keep
                               // it honest - and make sure overviewPlot always reflects
                               // the base scope, since collapsing a tile doesn't re-run render()

  requires(schema) {
    // return false to hide the widget when its columns are absent
    return schema.allCols.includes('my_column');
  },

  async render(container, ctx) {
    const rows = await ctx.queryRows(`
      SELECT my_column, COUNT(*) AS cnt
      FROM pp_data
      ${ctx.where}
      GROUP BY 1 ORDER BY 2 DESC
    `);
    // write into `container` using plain DOM, Plotly (window.Plotly), or any CDN library
  },

  // To show your widget correctly in Overview mode (the default tile-gallery view),
  // also define these. Both optional:

  async overviewMessage(ctx) {
    // one short summary sentence shown on the tile, e.g. "Found 42 matches."
    return 'Found some matches.';
  },

  async overviewPlot(container, ctx) {
    // small preview plot drawn into the tile; return false to skip it.
    // Apply ctx.where here too - it's a separate query path from render(),
    // so filters aren't inherited automatically.
  },
};
```

The DuckDB table is always named `pp_data`; `Plotly` is exposed globally as
`window.Plotly`. The extension manifest just lists the plugin files:

```json
{
  "name": "Tomato Harvest Helper",
  "auto_detect": true
}
```

### `ctx` reference

| Field | Type | Description |
|---|---|---|
| `ctx.queryRows(sql)` | `async → object[]` | query returning plain JS objects |
| `ctx.query(sql)` | `async → Arrow Table` | raw Arrow result (for binary/blob columns) |
| `ctx.querySample(cols, n)` | `async → object[]` | sampled scalar shorthand |
| `ctx.schema` | `object` | `{ metricCols, groupCols, dimensionInfo, allCols, blobCols }` |
| `ctx.state` | `object` | `{ palette, groupCol, filter, dimensions }` |
| `ctx.colorMap` | `object` | `{ groupValue: hexColor }` |
| `ctx.color.getColors(palette, n)` | `(string, number) → string[]` | `n` colors from the named palette - for ad-hoc groupings not covered by `colorMap` |
| `ctx.color.getPaletteNames()` | `() → string[]` | palette names accepted by `ctx.color.getColors` |
| `ctx.where` | `string` | SQL `WHERE` clause for the active filter (or `''`) - merge with `AND` if your query has its own `WHERE` |
| `ctx.groups` | `string[]` | distinct values of the active group column |
| `ctx.filteredCount` / `ctx.totalRows` | `number` | row counts |
| `ctx.plot` | `object` | plotting/DOM helpers (`appendMini`, `setScopeBadge`, `niceName`, ...) |


Notice neither widget imports anything from the Python side or refers to
`TomatoLoader`/`TomatoRipenessProcessor` by name - they just query for the
columns they need (`season`, `total_tomato_pixels`, `unripe_tomato_pixels`, `midripe_tomato_pixels`, `ripe_tomato_pixels`) and hide themselves via
`requires()` when those columns are missing. A viewer widget queries the table and renders a visualization — it activates whenever the right columns are present in the table.

---

## Defining the package

Any extension is a regular, installable Python package. The pieces that make
PixelPatrol find it:

1. **`pyproject.toml` entry points** - three optional groups, each pointing at
   a function in your `plugin_registry` module:

   ```toml
   [project.entry-points."pixel_patrol.loader_plugins"]
   my_extension_loaders = "my_package.plugin_registry:register_loader_plugins"

   [project.entry-points."pixel_patrol.processor_plugins"]
   my_extension_processors = "my_package.plugin_registry:register_processor_plugins"

   [project.entry-points."pixel_patrol.viewer_extensions"]
   my_extension_viewer = "my_package.plugin_registry:get_viewer_extension_dir"
   ```

2. **`plugin_registry.py`** - `register_loader_plugins` / `register_processor_plugins`
   each return a *list of classes* (not instances); `get_viewer_extension_dir`
   returns the `Path` to the folder containing `extension.json`:

   ```python
   # my_package/plugin_registry.py
   from pathlib import Path
   from my_package.my_loader import MyLoader
   from my_package.my_processor import MyProcessor

   def register_loader_plugins():
       return [MyLoader]

   def register_processor_plugins():
       return [MyProcessor]

   def get_viewer_extension_dir():
       return Path(__file__).parent / "viewer"
   ```

**You only need to declare the entry-point groups your extension actually
uses** - this is the crux of "pick and choose." Shipping only a processor?
Drop the `loader_plugins` and `viewer_extensions` groups (and the
`my_loader.py`/`viewer/` files) entirely; `register_processor_plugins` is the
only function `plugin_registry.py` needs. A viewer-only extension can drop
both Python groups and ship `plugin_registry.py` with nothing but
`get_viewer_extension_dir`. Nothing about the discovery mechanism assumes
you've implemented all three.

Once the package is installed in the same environment as `pixel_patrol_base`,
everything is discovered automatically at runtime - no explicit registration
or path needed when calling `create_project(..., loader="tomato")` or
`serve_viewer(report_path)`.

### Licensing

For easy redistribution, use a permissive license - it also matches the rest of the pixel-patrol ecosystem. Add a `LICENSE` file and declare it in `pyproject.toml`:

```toml
[project]
license = "MIT"
license-files = ["LICENSE"]
```

See the [Extensions docs](https://pixelpatrol.app/docs/extensions/#licensing) for guidance on which licenses and dependencies are appropriate.

---

## Running locally

PixelPatrol discovers loaders, processors, and viewer extensions through
Python entry points - which only works if your package is installed in the
*same environment* as `pixel_patrol_base`.

**Option 1: PixelPatrol is already installed**

If you already have PixelPatrol installed, make sure you're in that
environment, then install this package into it:

```sh
uv pip install -e .
```

To test the extension with the toy data, run the pipeline using the Python
interpreter from that environment:

```sh
python create_and_show_report.py
```

**Option 2: Fresh installation**

If you don't have PixelPatrol installed yet, you can set up the project and
its dependencies (including `pixel_patrol_base`) with:

```sh
uv sync
```

Then run the pipeline:

```sh
uv run python create_and_show_report.py
```

Both options (re)generate the tiny dataset if `data/` is missing, process it with
the custom loader and processor, save `out/report.parquet`, and serve the
viewer at `http://127.0.0.1:8052`. The viewer extension is loaded
automatically because `serve_viewer` discovers the `pixel_patrol.viewer_extensions`
entry-point declared in `pyproject.toml` - no explicit path needed.

---

## Writing your own extension

Ready to build? Copy this folder, then work through it one piece at a time:

1. Decide which piece(s) you actually need - loader/processor/widget (see the
   table at the top).
2. Update `pyproject.toml`'s `[project]` metadata and keep only the
   entry-point groups you need.
3. Replace `my_loader.py` / `my_processor.py` / `viewer/*.js` with your own
   - or delete the files (and the corresponding registry function) for the
   pieces you're skipping.
4. You probably want to create your own toy dataset to test your new
   extension, and run the full pipeline on it.

Check out our [docs](https://pixelpatrol.app/docs/) and
[tutorials](https://pixelpatrol.app/docs/tutorials/) for more
info on how to create your own PixelPatrol extension.