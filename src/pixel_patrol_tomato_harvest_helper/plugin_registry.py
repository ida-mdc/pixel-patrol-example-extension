from pixel_patrol_tomato_harvest_helper.my_loader import TomatoLoader
from pixel_patrol_tomato_harvest_helper.my_processor import TomatoRipenessProcessor
from pathlib import Path


def register_loader_plugins():
    return [TomatoLoader]

def register_processor_plugins():
    return [TomatoRipenessProcessor]

def get_viewer_extension_dir():
    """Return the path to the bundled viewer extension directory."""
    return Path(__file__).parent / "viewer"