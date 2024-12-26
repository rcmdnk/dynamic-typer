from pathlib import Path
from types import FunctionType

import pytest
import typer
from typer.testing import CliRunner

from dynamic_typer.class_utils import typer_decorator
from dynamic_typer.function_utils import (
    add_command,
    make_cmd_func,
    parse_args,
    read_conf,
    sys_args,
)


def test_sys_args(monkeypatch):
    arg_names = ['test', 'example', 'another_arg', 'not_given']
    with monkeypatch.context() as m:
        m.setattr(
            'sys.argv',
            [
                'main.py',
                '--test',
                1,
                '--example',
                1,
                '--another-arg',
                1,
                '--non-arg',
                '--test',
                '--not-given',
            ],
        )
        result = sys_args(arg_names)
        assert result == ['test', 'example', 'another_arg']


def test_parse_args(monkeypatch):
    input_args = {'test': 1, 'example': 1, 'another_arg': 1, 'not_given': 1}
    opts = {
        'test': None,
        'example': None,
        'another_arg': None,
        'not_given': None,
    }
    with monkeypatch.context() as m:
        m.setattr(
            'sys.argv',
            [
                'main.py',
                '--test',
                1,
                '--example',
                1,
                '--another-arg',
                1,
                '--non-arg',
                '--test',
                '--not-given',
            ],
        )
        result = parse_args(input_args, opts)
    assert result == {'test': 1, 'example': 1, 'another_arg': 1}


def test_read_conf_toml(tmp_path: Path):
    conf_path = tmp_path / 'config.toml'
    conf_content = """
    [global]
    key1 = "value1"
    [command]
    key2 = "value2"
    """
    conf_path.write_text(conf_content)

    result = read_conf(conf_path, 'toml')
    assert result == {
        'global': {'key1': 'value1'},
        'command': {'key2': 'value2'},
    }


def test_make_cmd_func():
    def dummy_callback(test):
        return test

    opts = {
        'test_str': {
            'type': str,
            'help': 'Str test argument',
            'default': 'default_value',
        },
        'test_int': {'type': int, 'help': 'Int test argument', 'default': 1},
    }

    func = make_cmd_func(
        app_name='test_app',
        command='test_command',
        opts=opts,
        callback=dummy_callback,
    )

    assert isinstance(func, FunctionType)
    assert func.__name__ == 'test_command'
    assert func.__annotations__['test_str'].__origin__ == str
    assert (
        func.__annotations__['test_str'].__metadata__[0].default
        == '--test-str'
    )
    assert (
        func.__annotations__['test_str'].__metadata__[0].help
        == 'Str test argument'
    )
    assert func.__annotations__['test_int'].__origin__ == int
    assert (
        func.__annotations__['test_int'].__metadata__[0].default
        == '--test-int'
    )
    assert (
        func.__annotations__['test_int'].__metadata__[0].help
        == 'Int test argument'
    )


def test_add_command(monkeypatch):
    app = typer.Typer()

    def dummy_callback(test: str = 'Hello'):
        typer.echo(f'Test: {test}')

    opts = {
        'test': {
            'type': str,
            'help': 'Test argument',
            'default': 'default_value',
        }
    }

    add_command(
        app,
        app_name='test_app',
        command='test_command',
        opts=opts,
        callback=dummy_callback,
        help='A test command',
    )

    runner = CliRunner()
    with monkeypatch.context() as m:
        args = []
        m.setattr('sys.argv', ['app'] + args)
        result = runner.invoke(app, args)

    assert result.exit_code == 0
    assert result.stdout == 'Test: Hello\n'

    with monkeypatch.context() as m:
        args = ['--test', 'Hello World']
        m.setattr('sys.argv', ['app'] + args)
        result = runner.invoke(app, args)

    assert result.exit_code == 0
    assert result.stdout == 'Test: Hello World\n'


def test_add_multi_command(monkeypatch):
    app = typer.Typer()

    def dummy_callback(test: str = 'Hello'):
        typer.echo(f'Test: {test}')

    opts = {
        'test': {
            'type': str,
            'help': 'Test argument',
            'default': 'default_value',
        }
    }

    add_command(
        app,
        app_name='test_app',
        command='test_command',
        opts=opts,
        callback=dummy_callback,
        help='A test command',
    )

    add_command(
        app,
        app_name='test_app',
        command='test_command2',
        opts=opts,
        callback=dummy_callback,
        help='A test command 2',
    )

    runner = CliRunner()
    with monkeypatch.context() as m:
        args = ['test_command']
        m.setattr('sys.argv', ['app'] + args)
        result = runner.invoke(app, args)

    assert result.exit_code == 0
    assert result.stdout == 'Test: Hello\n'

    with monkeypatch.context() as m:
        args = ['test_command', '--test', 'Hello World']
        m.setattr('sys.argv', ['app'] + args)
        result = runner.invoke(app, args)

    assert result.exit_code == 0
    assert result.stdout == 'Test: Hello World\n'


def test_typer_decorator():
    opts = {
        'test': {
            'type': str,
            'help': 'Test argument',
            'default': 'default_value',
            'type_str': 'str',
        }
    }

    @typer_decorator(opts)
    class TestClass:
        """A test class"""

    instance = TestClass()
    assert instance.test == 'default_value'
    assert 'Test argument' in TestClass.__doc__

    @typer_decorator(opts)
    class TestClass:
        """A test class"""

    instance = TestClass(test='Hello')
    assert instance.test == 'Hello'

    @typer_decorator({})
    class TestClass:
        """A test class"""

    with pytest.raises(ValueError) as e:
        instance = TestClass(test='Hello')
    assert str(e.value) == 'Unknown parameter: test'