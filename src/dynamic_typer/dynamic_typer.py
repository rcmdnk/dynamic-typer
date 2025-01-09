from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Annotated, Any, Callable, cast

import typer
from conf_finder import CONF_TYPE, EXT, ConfFinder
from typer.models import ArgumentInfo, CommandFunctionType, OptionInfo
from typing_extensions import _AnnotatedAlias


@dataclass
class TyperArg:
    """Representation of an argument used in a function for Typer commands.

    Attributes
    ----------
    type : type
        The expected type of the argument.
    info : OptionInfo | ArgumentInfo
        Typer metadata about the argument.
    default : Any
        The default value for the argument.

    """

    type: type | None = None
    info: OptionInfo | ArgumentInfo | None = None
    default: Any = inspect.Parameter.empty


def get_conf(
    app_name: str,
    conf_file: str = '',
    conf_ext: EXT = 'toml',
    conf_type: CONF_TYPE = 'both',
) -> dict[str, Any]:
    return ConfFinder(
        name=app_name, conf_name=conf_file, conf_type=conf_type
    ).read(conf_ext)


def get_cmd_conf(conf: dict[str, Any], cmd_name: str) -> dict[str, Any]:
    global_conf = conf.get('global', {})
    cmd_conf = conf.get(cmd_name, {})
    return {**global_conf, **cmd_conf}


def get_args_from_func(
    func: CommandFunctionType,
    args: dict[str, TyperArg],
    conf: dict[str, Any],
) -> dict[str, TyperArg]:
    sig = inspect.signature(func)
    func_args: dict[str, TyperArg] = {}

    for name, param in sig.parameters.items():
        if name in ['self', 'cls']:
            continue

        arg = args.get(name, TyperArg())

        if name in conf:
            arg.default = conf[name]
        elif arg.default is not inspect.Parameter.empty:
            pass
        else:
            arg.default = param.default

        if arg.type is None:
            if param.annotation is not inspect.Parameter.empty:
                if isinstance(param.annotation, _AnnotatedAlias):
                    arg.type = param.annotation.__origin__
                    if len(param.annotation.__metadata__) > 0 and isinstance(
                        param.annotation.__metadata__[0],
                        (typer.models.ArgumentInfo, typer.models.OptionInfo),
                    ):
                        arg.info = param.annotation.__metadata__[0]
                else:
                    arg.type = param.annotation
            elif arg.default is not inspect.Parameter.empty:
                arg.type = type(arg.default)
            else:
                arg.type = str
        arg.info = arg.info or typer.Argument(help=f'Set {name}.')
        func_args[name] = arg

    return func_args


def set_args(
    func: CommandFunctionType, args: dict[str, TyperArg]
) -> CommandFunctionType:
    func.__annotations__.update(
        {name: Annotated[arg.type, arg.info] for name, arg in args.items()}
    )
    func.__defaults__ = tuple(arg.default for arg in args.values())
    return func


def make_cmd_func(
    func: CommandFunctionType,
    name: str,
    args: dict[str, TyperArg] | None = None,
    conf: dict[str, Any] | None = None,
) -> CommandFunctionType:
    args = args or {}
    conf = conf or {}

    cmd_args = get_args_from_func(func, args, get_cmd_conf(conf, name))

    args_str = ', '.join(cmd_args)
    func_code = f"""
def {name}({args_str}):
    return func(**locals())
"""
    local_vars: dict[str, Any] = {'func': func}
    exec(func_code, local_vars)  # noqa: S102

    return set_args(local_vars[name], cmd_args)


class DynamicTyper(typer.Typer):
    """Class for creating a Typer app dynamically."""

    def __init__(  # type: ignore[no-untyped-def]
        self,
        args: dict[str, TyperArg] | None = None,
        use_conf: bool = True,
        conf_file: str = '',
        conf_ext: EXT = 'toml',
        conf_type: CONF_TYPE = 'both',
        **kw,  # noqa: ANN003
    ) -> None:
        """Initialize Dynamic Typer.

        Parameters
        ----------
        args : dict[str, TyperArg] | None
            Dictionary of Typer arguments, by default None
        use_conf : bool
            Whether to use configuration file, by default True
        conf_file : str
            Configuration file, by default ''
        conf_ext : Literal['', 'toml', 'yaml', 'yml', 'json']
            Configuration file extension, by default 'toml'
        conf_type : Literal['both', 'file', 'dir']
            Configuration file type, by default 'both'
        **kw : Any
            Arguments for Typer class

        """
        super().__init__(**kw)
        self.args = args or {}

        if isinstance(self.info.name, typer.models.DefaultPlaceholder):
            self.info.name = Path(sys.argv[0]).stem

        self.conf: dict[str, Any] = {}
        if use_conf or conf_file:
            self.conf = get_conf(
                app_name=cast(str, self.info.name),
                conf_file=conf_file,
                conf_ext=conf_ext,
                conf_type=conf_type,
            )

    def command(
        self,
        name: str | None = None,
        *,
        cls: type[typer.core.TyperCommand] | None = None,
        context_settings: dict[Any, Any] | None = None,
        help: str | None = None,  # noqa: A002
        epilog: str | None = None,
        short_help: str | None = None,
        options_metavar: str = '[OPTIONS]',
        add_help_option: bool = True,
        no_args_is_help: bool = False,
        hidden: bool = False,
        deprecated: bool = False,
        rich_help_panel: str | None = typer.models.Default(None),
        args: dict[str, TyperArg] | None = None,
    ) -> Callable[[CommandFunctionType], CommandFunctionType]:
        args = self.args if args is None else {**self.args, **args}

        def wrapper(
            func: CommandFunctionType,
            name: str | None,
            command: CommandFunctionType,
        ) -> CommandFunctionType:
            name = name or func.__name__
            func = make_cmd_func(func, name, args, self.conf)

            decorator = command(
                name=name,
                cls=cls,
                context_settings=context_settings,
                help=help,
                epilog=epilog,
                short_help=short_help,
                options_metavar=options_metavar,
                add_help_option=add_help_option,
                no_args_is_help=no_args_is_help,
                hidden=hidden,
                deprecated=deprecated,
                rich_help_panel=rich_help_panel,
            )
            decorator(func)

            return func

        return cast(
            Callable[[CommandFunctionType], CommandFunctionType],
            partial(
                wrapper,
                name=name,
                command=cast(
                    Callable[[CommandFunctionType], CommandFunctionType],
                    super().command,
                ),
            ),
        )
