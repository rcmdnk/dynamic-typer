from pathlib import Path

import pytest

from dynamic_typer.utils import parse_args, read_conf, sys_args


def test_sys_args(monkeypatch: pytest.MonkeyPatch) -> None:
    arg_names = ['test', 'example', 'another_arg', 'not_given']
    with monkeypatch.context() as m:
        m.setattr(
            'sys.argv',
            [
                'main.py',
                '--test',
                '1',
                '--example',
                '1',
                '--another-arg',
                '1',
                '--non-arg',
                '--test',
                '--not-given',
            ],
        )
        result = sys_args(arg_names)
        assert result == ['test', 'example', 'another_arg']


def test_parse_args(monkeypatch: pytest.MonkeyPatch) -> None:
    input_args = {'test': 1, 'example': 1, 'another_arg': 1, 'not_given': 1}
    args = {
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
                '1',
                '--example',
                '1',
                '--another-arg',
                '1',
                '--non-arg',
                '--test',
                '--not-given',
            ],
        )
        result = parse_args(input_args, list(args))
    assert result == {'test': 1, 'example': 1, 'another_arg': 1}


def test_read_conf_toml(tmp_path: Path) -> None:
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


def test_read_conf_unsupported_extension() -> None:
    with pytest.raises(ValueError, match='Unsupported file extension: xml'):
        read_conf('config.xml', 'xml')
