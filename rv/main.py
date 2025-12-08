# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import sys
from asyncio import get_running_loop, run, sleep
from collections.abc import Callable, Coroutine, Sequence

from .cmdargs import HelpPrintExitException, parse_logging_args, prepare_arglist
from .config import Config
from .defs import MIN_PYTHON_VERSION, MIN_PYTHON_VERSION_STR
from .download import at_interrupt
from .ids import process_ids
from .logger import Log
from .pages import process_pages
from .version import APP_NAME, APP_VERSION

__all__ = ('main_async', 'main_sync')


class ErrorCodes:
    SUCCESS = 0
    INTERRUPTED = -1
    UNKNOWN_ERROR = -255


def at_startup(args: Sequence[str]) -> None:
    """Inits logger. Reports python version and run options"""
    argv_set = set(args or ())
    parse_logging_args(args)
    Log.init()
    if argv_set.intersection({'--version', '--help'}):
        return
    Log.debug(f'Python {sys.version}\n{APP_NAME} ver {APP_VERSION}\nCommand-line args: {" ".join(sys.argv)}\n')


async def main(args: Sequence[str]) -> int:
    try:
        prepare_arglist(args)
    except HelpPrintExitException:
        return 0

    actions: dict[str, Callable[[], Coroutine[int]]] = {
        'ids': process_ids,
        'pages': process_pages,
    }

    action_name = Config.get_action_string()
    assert action_name in actions, f'Unknown action \'{action_name}\'!'
    proc = actions[action_name]
    return await proc()


async def run_main(args: Sequence[str]) -> int:
    res = await main(args)
    await sleep(0.5)
    return res


async def main_async(args: Sequence[str]) -> int:
    assert sys.version_info >= MIN_PYTHON_VERSION, f'Minimum python version required is {MIN_PYTHON_VERSION_STR}!'
    try:
        return await run_main(args)
    except (KeyboardInterrupt, SystemExit):
        Log.warn('Warning: catched KeyboardInterrupt/SystemExit...')
        return ErrorCodes.INTERRUPTED
    finally:
        at_interrupt()


def main_sync(args: Sequence[str]) -> int:
    at_startup(args)
    try:
        loop = get_running_loop()
    except RuntimeError:  # no current event loop
        loop = None
    run_func = loop.run_until_complete if loop else run
    return run_func(main_async(args))


if __name__ == '__main__':
    exit(main_sync(sys.argv[1:]))

#
#
#########################################
