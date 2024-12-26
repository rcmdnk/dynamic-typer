from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

import typer

if TYPE_CHECKING:
    from types import FunctionType

    from .typing import TyperOpts


def sys_args(arg_names: list[str]) -> list[str]:
    args = sys.argv
    names = []
    i = 0
    while i < len(args):
        if args[i] == '--':
            break
        if args[i].startswith('--'):
            name = args[i].lstrip('-').replace('-', '_')
            if name in arg_names:
                if name not in names:
                    names.append(name)
                i += 1
        i += 1
    return names


def parse_args(
    input_args: dict[str, Any], arg_names: list[str]
) -> dict[str, Any]:
    sa = sys_args(arg_names)
    return {x: input_args[x] for x in input_args if x in sa}


def read_conf(file_name: str | Path, ext: str) -> dict[Any, Any]:
    if ext == 'toml':
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib
        with Path(file_name).open('rb') as f:
            return tomllib.load(f)
    elif ext in ['yaml', 'yml']:
        import yaml

        with Path(file_name).open() as f:
            return yaml.safe_load(f)
    elif ext == 'json':
        import json

        with Path(file_name).open() as f:
            return json.load(f)
    else:
        msg = f'Unsupported file extension: {ext}'
        raise ValueError(msg)


def get_conf(
    conf_name: str,
    command: str,
    conf_file: str = '',
    conf_ext: str = 'toml',
    conf_type: str = 'both',
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
        conf = conf_dict.get('global', {})
        conf.update(conf_dict.get(command, {}))
    return conf


def make_annotated(name: str, opt: dict[str, Any]) -> Annotated[Any, Any]:  # noqa: ANN401
    return Annotated[
        opt['type'],
        typer.Option(
            '--' + name.replace('_', '-'),
            help=opt['help'],
        ),
    ]


def make_cmd_func(
    app_name: str,
    command: str,
    opts: TyperOpts,
    callback: FunctionType,
    use_conf: bool = False,
    conf_ext: str = 'toml',
    conf_type: str = 'both',
) -> FunctionType:
    opts = deepcopy(opts)
    if use_conf:
        opts['conf_file'] = {
            'type': str,
            'help': 'Path to the configuration file',
            'default': '',
        }
    opts_str = ', '.join(opts)
    func_code = f'def {command}({opts_str}):'
    if use_conf:
        func_code += f"""
    conf = get_conf(
        conf_name="{app_name}",
        command="{command}",
        conf_file=conf_file,
        conf_ext="{conf_ext}",
        conf_type="{conf_type}"
    )
    """
    else:
        func_code += """
    conf = {}
    """

    func_code += f"""
    conf.update(parse_args(locals(), {list(opts.keys())}))
    callback(**conf)
    """

    local_vars: dict[str, Any] = {
        'get_conf': get_conf,
        'parse_args': parse_args,
        'callback': callback,
    }
    exec(func_code, local_vars)  # noqa: S102
    func = local_vars[command]
    func.__defaults__ = tuple([x['default'] for x in opts.values()])
    func.__annotations__ = {
        key: make_annotated(key, value) for key, value in opts.items()
    }
    return func


def add_command(
    app: typer.Typer,
    app_name: str,
    command: str,
    opts: TyperOpts,
    callback: FunctionType,
    help: str,  # noqa: A002
    use_conf: bool = False,
    conf_ext: str = 'toml',
    conf_type: str = 'both',
) -> None:
    func = make_cmd_func(
        app_name, command, opts, callback, use_conf, conf_ext, conf_type
    )
    app.command(command, help=help)(func)
