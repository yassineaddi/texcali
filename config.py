import tomli
from pathlib import Path

path = Path(__file__).parent / "config.toml"

with path.open(mode="rb") as fp:
    cfg = tomli.load(fp)
