"""Repository-relative map paths and shallow, metadata-only map discovery."""

from dataclasses import dataclass
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[3]
DEFAULT_MAP = REPOSITORY / "map/mekong_15min"


def resolve_map(value=None, repository=REPOSITORY):
    path = Path(value).expanduser() if value is not None else Path(repository) / "map/mekong_15min"
    return (path if path.is_absolute() else Path(repository) / path).resolve()


@dataclass(frozen=True)
class MapOption:
    path: Path
    label: str


def discover_maps(repository=REPOSITORY):
    """Inspect immediate children only; MapReader validates headers, not full fields."""
    from map_reader import MapReader

    root = Path(repository) / "map"
    options = []
    if not root.is_dir():
        return options
    for path in sorted(root.iterdir(), key=lambda p: (p.name != "mekong_15min", p.name.lower())):
        if (path.name in ("tools", "src") or path.name.startswith((".", "tmp", "temp"))
                or not path.is_dir() or not (path / "params.txt").is_file()):
            continue
        try:
            reader = MapReader(path)
            if not reader.sources:
                continue
            g = reader.geometry
            options.append(MapOption(reader.path, f"{path.name} · {g.nx} × {g.ny} · {g.resolution * 60:g} arcmin"))
        except (OSError, ValueError):
            continue
    return options
