from pathlib import Path
from dynamic_yaml import load

with (Path(__file__).parent / 'config.yaml').open() as f:
    CONFIG = load(f)
