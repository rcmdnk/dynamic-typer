from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from inherit_docstring.utils import merge_docstring

if TYPE_CHECKING:
    from typing import Callable

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


def typer_decorator(args: TyperArgs) -> Callable[[type], type]:
    def _decorator(cls: type) -> type:
        doc_args = f"""
        Parameters
        ----------
        {make_doc(args)}
        """
        cls.__doc__ = merge_docstring(
            cls.__doc__ if cls.__doc__ else '', doc_args, indent=4
        )

        def init(self: Any, **kw: Any) -> None:  # noqa: ANN401
            for k in kw:
                if k not in args:
                    msg = f'Unknown parameter: {k}'
                    raise ValueError(msg)
            for k, v in args.items():
                setattr(self, k, kw.get(k, v['default']))

        cls.__init__ = init  # type: ignore[misc]

        return cls

    return _decorator


class CmdClass(ABC):
    """Abstract class for command classes."""

    @abstractmethod
    def run(self) -> None: ...
