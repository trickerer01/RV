# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
# Original solution by Bharel: https://stackoverflow.com/a/70664652
#

from asyncio import CancelledError, sleep
from collections.abc import Callable
from contextlib import nullcontext, contextmanager
from platform import system

__all__ = ('wait_for_key',)

if system() == 'Windows':
    # noinspection PyCompatibility
    from msvcrt import getwch, kbhit

    set_terminal_raw = nullcontext
    input_ready = kbhit
    next_input = getwch
else:
    # TODO: test on Linux
    import sys
    from functools import partial
    from select import select
    from termios import tcgetattr, tcsetattr, TCSADRAIN
    from tty import setraw

    @contextmanager
    def set_terminal_raw() -> None:
        fd = sys.stdin.fileno()
        old_settings = tcgetattr(fd)
        try:
            setraw(sys.stdin.fileno())
            yield
        finally:
            tcsetattr(fd, TCSADRAIN, old_settings)

    def input_ready() -> bool:
        return select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

    next_input = partial(sys.stdin.read, 1)


async def wait_for_key(key: str, callback: Callable[[], None], *, secondary=False) -> None:
    try:
        with set_terminal_raw():
            ch = ''
            while ch != key:
                await sleep(1.0)
                while input_ready():
                    ch = next_input()
            if secondary:
                while input_ready():
                    next_input()
                callback()
            else:
                await wait_for_key(key, callback, secondary=True)
    except CancelledError:
        pass

#
#
#########################################
