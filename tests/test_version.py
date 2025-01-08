from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from dynamic_typer import __version__


def test_version() -> None:
    with (Path(__file__).parents[1] / 'pyproject.toml').open('rb') as f:
        version = tomllib.load(f)['project']['version']
    assert version == __version__
