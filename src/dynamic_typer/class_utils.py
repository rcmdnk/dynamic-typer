from __future__ import annotations

from inherit_docstring.utils import merge_docstring
from .typing import TyperOpts
from typing import Any


def make_doc(opts: TyperOpts) -> str:
    doc = ""
    for k, v in opts.items():
        doc += f"    {k} : {v['type_str']}\n"
        default = (
            '"' + v["default"] + '"'
            if isinstance(v["default"], str)
            else v["default"]
        )
        doc += f"        {v['help']} (default: {default})\n"
    return doc


def typer_decorator(cls: type, opts: TyperOpts) -> type:
    doc_opts = f"""
    Parameters
    ----------
    {make_doc(opts)}
    """
    cls.__doc__ = merge_docstring(cls.__doc__ if cls.__doc__ else "",  doc_opts, indent=4)

    def init(self, **kw: Any) -> None:
        for k, v in opts.items():
            setattr(self, k, kw.get(k, v["default"]))

    setattr(cls, "__init__", init)

    return cls
