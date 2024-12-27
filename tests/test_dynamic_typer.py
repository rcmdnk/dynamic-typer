import pytest
import typer
from typer.testing import CliRunner

from dynamic_typer.class_utils import typer_decorator
from dynamic_typer.utils import add_command, add_commands, make_cmd_func


def test_make_cmd_func() -> None:
    def dummy_callback(test: str = '') -> None:
        pass

    args = {
        'test_str': {
            'type': str,
            'help': 'Str test argument',
            'default': 'default_value',
        },
        'test_int': {'type': int, 'help': 'Int test argument', 'default': 1},
    }

    func = make_cmd_func(
        app_name='test_app',
        cmd_name='test_command',
        cmd_obj=dummy_callback,
        args=args,
    )

    assert func.__name__ == 'test_command'
    assert func.__annotations__['test_str'].__origin__ is str
    assert func.__annotations__['test_int'].__origin__ is int


def test_add_command(monkeypatch: pytest.MonkeyPatch) -> None:
    app = typer.Typer()

    def dummy_callback(test: str = 'Hello') -> None:
        typer.echo(f'Test: {test}')

    args = {
        'test': {
            'type': str,
            'help': 'Test argument',
            'default': 'default_value',
        }
    }

    add_command(
        app,
        app_name='test_app',
        cmd_name='test_command',
        cmd_obj=dummy_callback,
        args=args,
        help='A test command',
    )

    runner = CliRunner()
    with monkeypatch.context() as m:
        args = []
        m.setattr('sys.argv', ['app', *args])
        result = runner.invoke(app, args)

    assert result.exit_code == 0
    assert result.stdout == 'Test: Hello\n'


def test_add_multi_command(monkeypatch: pytest.MonkeyPatch) -> None:
    app = typer.Typer()

    def dummy_callback(test: str = 'Hello') -> None:
        typer.echo(f'Test: {test}')

    args = {
        'test': {
            'type': str,
            'help': 'Test argument',
            'default': 'default_value',
        }
    }

    add_command(
        app,
        app_name='test_app',
        cmd_name='test_command',
        cmd_obj=dummy_callback,
        args=args,
        help='A test command',
    )

    add_command(
        app,
        app_name='test_app',
        cmd_name='test_command2',
        cmd_obj=dummy_callback,
        args=args,
        help='A test command 2',
    )

    runner = CliRunner()
    with monkeypatch.context() as m:
        args = ['test_command']
        m.setattr('sys.argv', ['app', *args])
        result = runner.invoke(app, args)

    assert result.exit_code == 0
    assert result.stdout == 'Test: Hello\n'


def test_add_commands_integration(monkeypatch: pytest.MonkeyPatch) -> None:
    app = typer.Typer()

    args = {
        'test_arg': {
            'type': str,
            'help': 'Test argument',
            'default': 'default_value',
        }
    }

    @typer_decorator(args)
    class TestCmd:
        def run(self) -> None:
            typer.echo(f'Test argument: {self.test_arg}')

    commands = {
        'test_cmd1': {
            'cmd_ojb': TestCmd,
            'args': args,
            'help': 'Command 1',
            'use_conf': False,
        },
        'test_cmd2': {
            'cmd_ojb': TestCmd,
            'args': args,
            'help': 'Command 2',
            'use_conf': False,
        },
    }

    add_commands(app, 'test_app', commands)

    runner = CliRunner()
    with monkeypatch.context() as m:
        args = ['test_cmd1']
        m.setattr('sys.argv', ['app', *args])
        result = runner.invoke(app, args)

    assert result.exit_code == 0
    assert result.stdout == 'Test argument: default_value\n'
