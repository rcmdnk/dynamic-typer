import pytest

from dynamic_typer.class_utils import make_doc, typer_decorator


def test_make_doc() -> None:
    args = {
        'arg1': {
            'type': str,
            'help': 'Test argument 1',
            'default': 'value1',
            'type_str': 'str',
        },
        'arg2': {
            'type': int,
            'help': 'Test argument 2',
            'default': 10,
            'type_str': 'int',
        },
    }
    doc = make_doc(args)
    expected = (
        '    arg1 : str\n'
        '        Test argument 1 (default: "value1")\n'
        '    arg2 : int\n'
        '        Test argument 2 (default: 10)\n'
    )
    assert doc == expected


def test_typer_decorator() -> None:
    args = {
        'test': {
            'type': str,
            'help': 'Test argument',
            'default': 'default_value',
            'type_str': 'str',
        }
    }

    @typer_decorator(args)
    class TestClass:
        """A test class."""

    instance = TestClass()
    assert instance.test == 'default_value'
    assert 'Test argument' in TestClass.__doc__

    @typer_decorator(args)
    class TestClass:
        """A test class."""

    instance = TestClass(test='Hello')
    assert instance.test == 'Hello'

    @typer_decorator({})
    class TestClass:
        """A test class."""

    with pytest.raises(ValueError, match='Unknown parameter: test'):
        instance = TestClass(test='Hello')
