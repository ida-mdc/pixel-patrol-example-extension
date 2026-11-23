"""Generate the synthetic Tomato Harvest Helper dataset.

Each image is a 32x32 RGB snapshot of a tomato plant, stored as a `.npz`
file containing the RGB pixel array and season metadata. The images are
synthetic, with a noisy green background, stems, leaves and small colored
tomatoes. The number and ripeness of tomatoes depend on the growing
environment (`greenhouse` or `outdoors`) and the season: greenhouses
generally have more tomatoes, summer has the most, spring has mostly
unripe tomatoes, autumn has many ripe ones, and winter has very few,
with none outdoors. Tomatoes are colored green-yellow (unripe), orange
(midripe) or red (ripe), using distinct RGB ranges.

This gives the TomatoRipenessProcessor recognizable colors to classify
tomato pixels by ripeness. One image is generated for each combination
of environment and season, giving eight images in total. The growing
environment is represented by the folder structure, while the season
is stored both in the filename and inside the NPZ file.

Run once to (re)create `data/`:

    uv run python make_dataset.py
"""


from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
IMAGE_SIZE = 32
SEED = 17

DESCRIPTION = (
    "A tiny tomato harvest helper: synthetic garden snapshots showing how "
    "tomato numbers and ripeness change with the season and growing environments."
)

# Distinct RGB ranges for the three ripeness classes.
TOMATO_COLOR_RANGES = {
    "unripe": {"r": (140, 170), "g": (175, 205), "b": (45, 75)},
    "midripe": {"r": (220, 250), "g": (125, 155), "b": (15, 45)},
    "ripe": {"r": (200, 235), "g": (25, 65), "b": (20, 50)},
}

# Tomato count and ripeness ranges for each environment and season.
# The midripe share is the remainder after unripe and ripe shares.
GROWING_PROFILES = {
    "greenhouse": {
        "spring": {"tomato_count": (6, 8), "unripe_share": (0.55, 0.80), "ripe_share": (0.00, 0.05)},
        "summer": {"tomato_count": (12, 16), "unripe_share": (0.00, 0.10), "ripe_share": (0.55, 0.80)},
        "autumn": {"tomato_count": (6, 9), "unripe_share": (0.00, 0.05), "ripe_share": (0.60, 0.85)},
        "winter": {"tomato_count": (2, 4), "unripe_share": (0.65, 0.90), "ripe_share": (0.00, 0.05)},
    },
    "outdoors": {
        "spring": {"tomato_count": (3, 5), "unripe_share": (0.65, 0.90), "ripe_share": (0.00, 0.02)},
        "summer": {"tomato_count": (7, 9), "unripe_share": (0.05, 0.25), "ripe_share": (0.35, 0.65)},
        "autumn": {"tomato_count": (4, 7), "unripe_share": (0.00, 0.02), "ripe_share": (0.75, 0.85)},
        "winter": {"tomato_count": (0, 0), "unripe_share": (0.00, 0.20), "ripe_share": (0.00, 0.05)},
    },
}

# One image per environment and season.
DATASET = [
    ("greenhouse", "spring"),
    ("greenhouse", "summer"),
    ("greenhouse", "autumn"),
    ("greenhouse", "winter"),
    ("outdoors", "spring"),
    ("outdoors", "summer"),
    ("outdoors", "autumn"),
    ("outdoors", "winter"),
]


def make_background(rng: np.random.Generator) -> Image.Image:
    """Paint a synthetic tomato plant background with noise, stems and leaves."""

    # Start with a slightly noisy green background.
    noise = rng.integers(-15, 16, size=(IMAGE_SIZE, IMAGE_SIZE, 3))
    base = np.array((65, 105, 45), dtype=np.int16)
    pixels = np.clip(base + noise, 0, 255).astype(np.uint8)

    image = Image.fromarray(pixels, mode="RGB")
    draw = ImageDraw.Draw(image)

    # Draw stems.
    for x in range(4, IMAGE_SIZE, 7):
        draw.line(
            [(x, IMAGE_SIZE), (x + rng.integers(-4, 5), 5)],
            fill=(45, 95, 40),
            width=1,
        )

    # Draw small pointed leaves.
    for _ in range(30):
        x = int(rng.integers(2, IMAGE_SIZE - 2))
        y = int(rng.integers(5, IMAGE_SIZE - 5))
        length = int(rng.integers(7, 11))
        width = int(rng.integers(2, 4))
        direction = rng.choice([-1, 1])

        points = [
            (x, y),
            (x + direction * width, y - length // 2),
            (x + direction * width, y - length),
            (x, y - length + 1),
            (x - direction * width, y - length // 2),
        ]

        draw.polygon(points, fill=(35, 85, 35))

    return image


def tomato_color(rng: np.random.Generator, ripeness_class: str) -> tuple[int, int, int]:
    """Generate a random RGB color within the selected ripeness range."""

    color_range = TOMATO_COLOR_RANGES[ripeness_class]
    return (
        int(rng.integers(*color_range["r"])),
        int(rng.integers(*color_range["g"])),
        int(rng.integers(*color_range["b"])),
    )


def stamp_tomato(image: Image.Image, rng: np.random.Generator, ripeness_class: str) -> None:
    """Paint one small tomato with subtle color variation and shading."""

    draw = ImageDraw.Draw(image)

    # Random tomato size and position.
    radius = int(rng.integers(2, 4))
    x = int(rng.integers(radius + 1, IMAGE_SIZE - radius - 1))
    y = int(rng.integers(radius + 2, IMAGE_SIZE - radius - 1))

    # Generate individual tomato color.
    color = tomato_color(rng, ripeness_class)
    color_range = TOMATO_COLOR_RANGES[ripeness_class]

    # Slightly darker edge, staying within the ripeness range.
    edge_color = tuple(
        max(color_range[channel][0], int(value * 0.88))
        for channel, value in zip(("r", "g", "b"), color)
    )

    # Draw darker outer shape.
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=edge_color)
    
    # Draw slightly brighter center.
    draw.ellipse([x - radius + 1, y - radius + 1, x + radius - 1, y + radius - 1],fill=color)
    
    # Small highlight.
    highlight_color = tuple(
        min(color_range[channel][1] - 1, value + 3)
        for channel, value in zip(("r", "g", "b"), color)
    )
    draw.point((x - 1, y - 1), fill=highlight_color)

    # Small green calyx.
    draw.point((x, y - radius), fill=(35, 90, 35))


def make_image(rng: np.random.Generator, environment: str, season: str) -> Image.Image:
    """Paint one synthetic tomato-plant snapshot."""

    profile = GROWING_PROFILES[environment][season]
    image = make_background(rng)

    # Determine the number of tomatoes.
    count_lo, count_hi = profile["tomato_count"]
    tomato_count = int(rng.integers(count_lo, count_hi + 1))

    # Determine the ripeness proportions.
    unripe_lo, unripe_hi = profile["unripe_share"]
    ripe_lo, ripe_hi = profile["ripe_share"]

    unripe_share = rng.uniform(unripe_lo, unripe_hi)
    ripe_share = rng.uniform(ripe_lo, ripe_hi)

    # The remaining proportion consists of midripe tomatoes.
    midripe_share = 1.0 - unripe_share - ripe_share
    shares = np.array([unripe_share, midripe_share, ripe_share])

    # Convert proportions into whole tomato counts.
    class_counts = rng.multinomial(tomato_count, shares)

    ripeness_classes = (
        ["unripe"] * int(class_counts[0])
        + ["midripe"] * int(class_counts[1])
        + ["ripe"] * int(class_counts[2])
    )

    # Shuffle the ripeness classes before drawing.
    rng.shuffle(ripeness_classes)

    # Paint all tomatoes.
    for ripeness_class in ripeness_classes:
        stamp_tomato(image, rng, ripeness_class)

    return image


def main() -> None:
    """Generate one image per environment and season."""

    rng = np.random.default_rng(SEED)
    data_dir = HERE / "data"

    for environment, season in DATASET:
        out_dir = data_dir / environment
        out_dir.mkdir(parents=True, exist_ok=True)

        image = make_image(rng, environment, season)
        out_path = out_dir / f"tomato_{season}.npz"

        # Save the RGB image and season metadata as a compressed NPZ file.
        np.savez_compressed(out_path, image=np.asarray(image), season=season)

        print(f"wrote {out_path.relative_to(HERE)}")


if __name__ == "__main__":
    main()