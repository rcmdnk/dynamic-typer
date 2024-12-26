from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from types import FunctionType
from typing import TYPE_CHECKING, Annotated, Any, Callable

import typer

if TYPE_CHECKING:
    from .class_utils import CmdClass
    from .typing import TyperArgs, TyperCommands


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
    cmd_name: str,
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
        conf.update(conf_dict.get(cmd_name, {}))
    return conf


def make_annotated(name: str, arg: dict[str, Any]) -> Annotated[Any, Any]:  # noqa: ANN401
    return Annotated[
        arg['type'],
        typer.Option(
            '--' + name.replace('_', '-'),
            help=arg.get('help', ''),
        ),
    ]


def make_cmd_func(
    app_name: str,
    cmd_name: str,
    cmd_obj: FunctionType | type[CmdClass],
    args: TyperArgs,
    use_conf: bool = False,
    conf_ext: str = 'toml',
    conf_type: str = 'both',
) -> Callable[..., Any]:
    args = deepcopy(args)
    if use_conf:
        args['conf_file'] = {
            'type': str,
            'help': 'Path to the configuration file',
            'default': '',
        }
    args_str = ', '.join(args)
    func_code = f'def {cmd_name}({args_str}):'
    if use_conf:
        func_code += f"""
    conf = get_conf(
        conf_name="{app_name}",
        cmd_name="{cmd_name}",
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
    conf.update(parse_args(locals(), {list(args)}))
    """

    if isinstance(cmd_obj, FunctionType):
        func_code += """
    cmd_obj(**conf)
"""
    else:
        func_code += """
    cmd_obj(**conf).run()
"""

    local_vars: dict[str, Any] = {
        'get_conf': get_conf,
        'parse_args': parse_args,
        'cmd_obj': cmd_obj,
    }
    exec(func_code, local_vars)  # noqa: S102
    func = local_vars[cmd_name]
    func.__defaults__ = tuple([x['default'] for x in args.values()])
    func.__annotations__ = {
        key: make_annotated(key, value) for key, value in args.items()
    }
    return func


def add_command(
    app: typer.Typer,
    app_name: str,
    cmd_name: str,
    cmd_obj: FunctionType | type[CmdClass],
    args: TyperArgs,
    help: str = '',  # noqa: A002
    use_conf: bool = False,
    conf_ext: str = 'toml',
    conf_type: str = 'both',
) -> None:
    """Add a function as a command to the Typer app.

    Parameters
    ----------
    app : typer.Typer
        The Typer app to add the command to.
    app_name : str
        The name of the app. This is used to find the configuration file.
    cmd_name : str
        The command name to add.
    cmd_obj : FunctionType | Type[CmdClass]
        The command object (callback function or CmdClass) to add.
    args : dict
        The arguments for the command. The keys are the argument names and the
        values are dictionaries with keys 'type', 'help', and 'default'. The
        'type' key is the type of the argument. The 'help' key is the help text
        for the argument. The 'default' key is the default value for the
        argument.
    help : str
        The help text for the command.
    use_conf : bool
        Whether to use a configuration file.
    conf_ext : str
        The extension of the configuration file.
    conf_type : str
        The type of the configuration file.

    """
    func = make_cmd_func(
        app_name, cmd_name, cmd_obj, args, use_conf, conf_ext, conf_type
    )
    app.command(cmd_name, help=help)(func)


def add_commands(
    app: typer.Typer,
    app_name: str,
    commands: TyperCommands,
    conf_ext: str = 'toml',
    conf_type: str = 'both',
) -> None:
    """Add multiple commands to the Typer app.

    Parameters
    ----------
    app : typer.Typer
        The Typer app to add the commands to.
    app_name : str
        The name of the app. This is used to find the configuration file.
    commands : dict
        The commands to add. The keys are the command names and the values are
        dictionaries with keys 'cmd_obj', 'args', 'help', and 'use_conf'. The
        'cmd_obj' key is the command object (callback function or CmdClass) to
        be added to the app. The 'help' key is the help text for the command.
        The 'args' key is a dictionary with the argument names as keys and
        dictionaries with keys 'type', 'help', and 'default' as values. The
        'use_conf' key is a boolean indicating whether to use a configuration
        file. If 'use_conf' is True, the 'conf_ext' and 'conf_type' keys are
        also required. The 'conf_ext' key is the extension of the configuration
        file. The 'conf_type' key is the type of the configuration file. The
        'conf_ext' and 'conf_type' keys default to 'toml' and 'both',
        respectively. If 'use_conf' is False, the 'conf_ext' and 'conf_type'
        keys are ignored.
    conf_ext : str
        The extension of the configuration file.
    conf_type : str
        The type of the configuration file.

    """
    for cmd_name, data in commands.items():
        add_command(
            app=app,
            app_name=app_name,
            cmd_name=cmd_name,
            cmd_obj=data['cmd_ojb'],
            args=data['args'],
            help=data.get('help', ''),
            use_conf=data.get('use_conf', False),
            conf_ext=conf_ext,
            conf_type=conf_type,
        )
