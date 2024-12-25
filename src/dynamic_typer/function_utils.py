from __future__ import annotations

import sys
import typer
from typing_extensions import Annotated
from typing import Any
from types import FunctionType
from .typing import TyperOpts
from pathlib import Path
from copy import deepcopy


def sys_args(opts: dict[str, dict[str, Any]]) -> list[str]:
    arg_names = [
        x.lstrip("-").replace("-", "_")
        for x in sys.argv[1:]
        if x.startswith("--")
    ]
    return [x for x in arg_names if x in opts]


def parse_args(
    input_args: dict[str, Any], opts: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    sa = sys_args(opts)
    output_args = {x: input_args[x] for x in input_args if x in sa}
    return output_args


def read_conf(file_name: str | Path, ext: str) -> dict[Any, Any]:
    if ext == "toml":
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib
        with Path(file_name).open("rb") as f:
            return tomllib.load(f)
    elif ext in ["yaml", "yml"]:
        import yaml

        with Path(file_name).open() as f:
            return yaml.safe_load(f)
    elif ext == "json":
        import json

        with Path(file_name).open() as f:
            return json.load(f)
    else:
        msg = f"Unsupported file extension: {ext}"
        raise ValueError(msg)


def get_conf(
    conf_name: str, command: str, conf_file: str = "", conf_ext: str = "toml", conf_type: str = "both",
) -> dict[str, Any]:
    if not conf_file:
        from conf_finder import ConfFinder

        cf = ConfFinder(conf_name, conf_type=conf_type)
        conf_path = cf.conf(conf_ext)
    else:
        conf_path = Path(conf_file)
    conf_dict = {}
    if conf_path.is_file():
        conf_dict = read_conf(conf_path, conf_ext)
        conf = conf_dict.get("global", {})
        conf.update(conf_dict.get(command, {}))
    return conf


def make_annotated(name: str, opts: TyperOpts) -> Annotated[Any, Any]:
    return Annotated[
        opts["type"],
        typer.Option(
            "--" + name.replace("_", "-"),
            help=opts["help"],
        ),
    ]


def make_cmd_func(app_name: str, command: str, opts: TyperOpts, callback: FunctionType, add_conf_file: bool = False, conf_ext: str = "toml", conf_type: str = "both") -> FunctionType:
    opts = deepcopy(opts)
    if add_conf_file:
        opts["conf_file"] = {
            "type": str,
            "help": "Path to the configuration file",
            "default": "",
        }
    opts_str = ", ".join(opts)
    func_code = f"def {command}({opts_str}):"
    if add_conf_file:
        func_code += f"""
    conf = get_conf(conf_name="{app_name}", command="{command}", conf_file=conf_file, conf_ext="{conf_ext}", conf_type="{conf_type}")
    conf.update(parse_args(locals(), {opts}))
    callback(**conf)
"""
    func_code = f"""
def {name}({opts_str}):
"""

    code_obj = compile(func_code, "<string>", "exec")
    local_vars: dict[str, Any] = {"callback": callback}
    exec(code_obj, {}, local_vars)
    func = FunctionType(local_vars[command].__code__, globals())
    func.__defaults__ = tuple([x["default"] for x in opts.values()])
    func.__annotations__ = {
        key: make_annotated(key, value) for key, value in opts.items()
    }
    return func


def add_command(app: typer.Typer, app_name: str, command: str, opts: TyperOpts, callback: FunctionType, help: str, add_conf_file: bool = False, conf_ext: str = "toml", conf_type: str = "both") -> None:
    func = make_cmd_func(app_name, command, opts, callback, add_conf_file, conf_ext, conf_type)
    app.command(command, help=help)(func)
