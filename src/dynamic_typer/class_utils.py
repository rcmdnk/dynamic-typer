from __future__ import annotations

from typing import TYPE_CHECKING, Any

from inherit_docstring.utils import merge_docstring

if TYPE_CHECKING:
    from types import FunctionType

    from .typing import TyperOpts


def make_doc(opts: TyperOpts) -> str:
    doc = ''
    for k, v in opts.items():
        doc += f"    {k} : {v.get('type_str', v['type'].__name__)}\n"
        default = (
            '"' + v['default'] + '"'
            if isinstance(v['default'], str)
            else v['default']
        )
        doc += f"        {v['help']} (default: {default})\n"
    return doc


def typer_decorator(opts: TyperOpts) -> FunctionType:
    def _decorator(cls: type) -> type:
        doc_opts = f"""
        Parameters
        ----------
        {make_doc(opts)}
        """
        cls.__doc__ = merge_docstring(
            cls.__doc__ if cls.__doc__ else '', doc_opts, indent=4
        )

        def init(self: Any, **kw: Any) -> None:  # noqa: ANN401
            for k in kw:
                if k not in opts:
                    raise ValueError(f'Unknown parameter: {k}')
            for k, v in opts.items():
                setattr(self, k, kw.get(k, v['default']))

        cls.__init__ = init  # type: ignore[misc]

        return cls

    return _decorator
