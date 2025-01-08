from pathlib import Path
from typing import Annotated

import pytest
from typer import Argument, Option
from typer.testing import CliRunner

from dynamic_typer import (
    DynamicTyper,
    TyperArg,
)
from dynamic_typer.dynamic_typer import (
    get_args_from_func,
    get_cmd_conf,
    get_conf,
    make_cmd_func,
    set_args,
)


def test_get_conf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert get_conf('test_conf_not_exist') == {}
    Path('.test.toml')
    with Path('.test.toml').open('w') as f:
        f.write("""
[global]
a = 1
[cmd1]
b = 1
""")
    assert get_conf('test') == {'global': {'a': 1}, 'cmd1': {'b': 1}}


def test_get_cmd_conf() -> None:
    conf = {
        'global': {'global_key': 'global_value'},
        'cmd_name': {'cmd_key': 'cmd_value'},
    }

    result = get_cmd_conf(conf, 'cmd_name')
    assert result == {
        'global_key': 'global_value',
        'cmd_key': 'cmd_value',
    }


def test_get_args_from_func() -> None:
    def sample_func(arg1: int, arg2: str = 'default') -> None:
        pass

    args = {'arg1': TyperArg(type=int), 'arg2': TyperArg(type=str)}
    conf = {'arg2': 'configured_value'}

    result = get_args_from_func(sample_func, args, conf)

    assert result['arg1'].type is int
    assert result['arg2'].default == 'configured_value'


def test_set_args() -> None:
    def sample_func(arg1: int):  # noqa: ANN202
        return arg1

    args = {
        'arg1': TyperArg(
            type=int, default=10, info=Argument(help='help for arg1')
        )
    }

    updated_func = set_args(sample_func, args)

    assert (
        updated_func.__annotations__['arg1']
        == Annotated[int, args['arg1'].info]
    )
    assert updated_func.__defaults__ == (10,)


def test_make_cmd_func() -> None:
    def sample_func(arg1: int):  # noqa: ANN202
        return arg1

    args = {
        'arg1': TyperArg(
            type=int, default=10, info=Option(help='help for arg1')
        )
    }
    conf = {'arg1': 20}

    cmd_func = make_cmd_func(sample_func, 'cmd_name', args=args, conf=conf)

    assert callable(cmd_func)
    assert cmd_func.__name__ == 'cmd_name'
    assert cmd_func(30) == 30


def test_dynamic_typer_single_command() -> None:
    args = {
        'name': TyperArg(
            type=str, default='World', info=Argument(help='help for name')
        ),
        'greet': TyperArg(
            type=str, default='Hello', info=Option(help='help for greet')
        ),
    }
    app = DynamicTyper(name='app', args=args)

    @app.command()
    def hello(greet, name) -> None:
        pass

    runner = CliRunner()

    result = runner.invoke(app)
    assert result.exit_code == 0
    assert result.stdout == 'Hello World\n'

    result = runner.invoke(app, ['Alice'])
    assert result.exit_code == 0
    assert result.stdout == 'Hello Alice\n'

    result = runner.invoke(app, ['Alice', '--greet', 'Hi'])
    assert result.exit_code == 0
    assert result.stdout == 'Hi Alice\n'


def test_dynamic_typer_command() -> None:
    args = {
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
    app = DynamicTyper(name='app', args=args)

    @app.command()
    def cmd1(greet, name, time) -> None:
        pass

    @app.command(
        args={
            'name': TyperArg(
                type=str, default='Bob', info=Argument(help='help for name')
            )
        }
    )
    def cmd2(greet, name, time) -> None:
        pass

    runner = CliRunner()

    result = runner.invoke(app, ['cmd1'])
    assert result.exit_code == 0
    assert result.stdout == 'Hello World (12:00)\n'

    result = runner.invoke(app, ['cmd2'])
    assert result.exit_code == 0
    assert result.stdout == 'Hello Bob (12:00)\n'

    result = runner.invoke(
        app, ['cmd2', 'Alice', '--greet', 'Hi', '--time', '13:00']
    )
    assert result.exit_code == 0
    assert result.stdout == 'Hi Alice (13:00)\n'
