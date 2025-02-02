# Dynamic Typer

[![test](https://github.com/rcmdnk/dynamic-typer/actions/workflows/test.yml/badge.svg)](https://github.com/rcmdnk/dynamic-typer/actions/workflows/test.yml)
[![test coverage](https://img.shields.io/badge/coverage-check%20here-blue.svg)](https://github.com/rcmdnk/dynamic-typer/tree/coverage)

**DynamicTyper** is a Python library built on top of [Typer](https://typer.tiangolo.com/). While Typer already supports automatic extraction of function argument information and command registration, Dynamic Typer extends these capabilities with a focus on dynamic argument handling. Even if your function definitions do not specify Typer metadata (such as `OptionInfo` or `ArgumentInfo`), you can supply the necessary details via the `args` parameter of DynamicTyper. DynamicTyper will dynamically rewrite and register your functions with the provided argument information.
It is useful especially some of commands have same arguments.

In addition, DynamicTyper integrates configuration settings from files (such as TOML, YAML, or JSON) using [conf-finder](https://github.com/rcmdnk/conf-finder) to extract default values for arguments.

Useful for cases where your want to make commands which have common arguments.

## Requirement

- Python >= 3.7

## Installation

You can install `dynamic-typer` from [PyPI](https://pypi.org/):

```bash
pip install dynamic-typer
```

## Usage

Below is a example with args.

```python:greet.py
from typer import Argument, Option
from dynamic_typer.dynamic_typer import DynamicTyper, TyperArg

common_args = {
    'name': TyperArg(
        type=str, default='World', info=Argument(help='help for name')
    ),
    'time': TyperArg(
        type=str, default='12:00', info=Option(help='help for time')
    ),
    'greet': TyperArg(
        type=str, default='Hello', info=Option(help='help for greet')
    ),
}
app = DynamicTyper(name='app', args=common_args)


@app.command()
def greet1(greet, name, time) -> None:
    typer.echo(f'{greet} {name} ({time})')


@app.command(
    args={
        'name': TyperArg(
            type=str, default='Bob', info=Argument(help='help for name')
        )
    }
)
def greet2(greet, name, time) -> None:
    typer.echo(f'{greet} {name} ({time})')


if __name__ == '__main__':
    app()
```

First, `common_args` is passed to DynamicTyper.
If the argument of the function for the command is in `common_args`,
metadata and default value are added to the function
if the original argument does not have these inforamtion.

`args` can be given by the argument of `command` decorator to specialized for the function.

```bash
$ python greet.py greet1 --help

 Usage: greet.py greet1 [OPTIONS] [NAME]

╭─ Arguments ───────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   name      [NAME]  help for name [default: World]                                                                        │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --greet        TEXT  help for greet [default: Hello]                                                                      │
│ --time         TEXT  help for time [default: 12:00]                                                                       │
│ --help               Show this message and exit.                                                                          │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

$ python greet.py greet2 --help

 Usage: greet.py greet2 [OPTIONS] [NAME]

╭─ Arguments ───────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   name      [NAME]  help for name [default: Bob]                                                                          │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --greet        TEXT  help for greet [default: Hello]                                                                      │
│ --time         TEXT  help for time [default: 12:00]                                                                       │
│ --help               Show this message and exit.                                                                          │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
```

Based on [rcmdnk/python-template](https://github.com/rcmdnk/python-template), v0.1.2
