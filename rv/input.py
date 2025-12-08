# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
# Original solution by Bharel: https://stackoverflow.com/a/70664652
#

from asyncio import CancelledError, sleep
from collections.abc import Callable
from contextlib import contextmanager, nullcontext
from platform import system

__all__ = ('wait_for_key',)

if system() == 'Windows':
    import msvcrt

    set_terminal_raw = nullcontext
    input_ready = msvcrt.kbhit
    next_input = msvcrt.getwch
else:
    import functools
    import sys
    from select import select
    from termios import TCSADRAIN, tcgetattr, tcsetattr
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

    next_input = functools.partial(sys.stdin.read, 1)


async def wait_for_key(key: str, count: int, callback: Callable[[], None]) -> None:
    try:
        stroke_sequence: list[str] = []
        with set_terminal_raw():
            while stroke_sequence != [key] * count:
                await sleep(1.0)
                if not input_ready():
                    stroke_sequence.clear()
                    continue
                while input_ready():
                    ch = next_input()
                    if ch == key:
                        stroke_sequence.append(ch)
                    else:
                        stroke_sequence.clear()
                        while input_ready():
                            next_input()
            callback()
    except CancelledError:
        pass

#
#
#########################################
