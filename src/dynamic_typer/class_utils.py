from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Protocol, cast

from inherit_docstring.utils import merge_docstring

if TYPE_CHECKING:
    from .typing import TyperArgs


def make_doc(args: TyperArgs) -> str:
    doc = ''
    for k, v in args.items():
        doc += f"    {k} : {v.get('type_str', v['type'].__name__)}\n"
        default = (
            '"' + v['default'] + '"'
            if isinstance(v['default'], str)
            else v['default']
        )
        doc += f"        {v['help']} (default: {default})\n"
    return doc


class CmdClass(Protocol):
    """Protocol for a command class."""

    __name__: str

    def run(self) -> None: ...


def typer_decorator(
    args: TyperArgs,
) -> Callable[[type[CmdClass]], type[CmdClass]]:
    def _decorator(cls: type[CmdClass]) -> type[CmdClass]:
        if not hasattr(cls, 'run') or not callable(cls.run):
            msg = f"{cls.__name__} must define a callable 'run' method."
            raise TypeError(msg)

        class WrappedClass(cls):  # type: ignore[misc,valid-type]
            def __init__(self, **kw: Any) -> None:  # noqa: ANN401
                for k in kw:
                    if k not in args:
                        msg = f'Unknown parameter: {k}'
                        raise ValueError(msg)
                for k, v in args.items():
                    setattr(self, k, kw.get(k, v['default']))

        doc_args = f"""
        Parameters
        ----------
        {make_doc(args)}
        """
        doc = merge_docstring(
            cls.__doc__ if cls.__doc__ else '', doc_args, indent=4
        )
        WrappedClass.__doc__ = doc
        return cast(type[CmdClass], WrappedClass)

    return _decorator
