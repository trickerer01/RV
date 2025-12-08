# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from locale import getpreferredencoding

from colorama import Fore
from colorama import init as colorama_init

from .config import Config
from .defs import UTF8, LoggingFlags


class Log:
    """
    Basic logger supporting different log levels, colors and extra logging flags\n
    **Static**
    """
    _disabled = False

    COLORS = {
        LoggingFlags.TRACE: Fore.WHITE,
        LoggingFlags.DEBUG: Fore.LIGHTWHITE_EX,
        LoggingFlags.INFO: Fore.LIGHTCYAN_EX,
        LoggingFlags.WARN: Fore.LIGHTYELLOW_EX,
        LoggingFlags.ERROR: Fore.LIGHTYELLOW_EX,
        LoggingFlags.FATAL: Fore.LIGHTRED_EX,
    }

    ERR_POLICY = 'backslashreplace'

    @staticmethod
    def init() -> None:
        if not Config.nocolors:
            colorama_init()

    @staticmethod
    def should_log(flags: LoggingFlags) -> bool:
        return flags >= Config.logging_flags and not Log._disabled

    @staticmethod
    def log(text: str, flags: LoggingFlags) -> None:
        # if flags & LoggingFlags.FATAL == 0 and Config.logging_flags & flags != flags:
        if not Log.should_log(flags):
            return

        if not Config.nocolors:
            for f in reversed(Log.COLORS.keys()):
                if f & flags:
                    text = f'{Log.COLORS[f]}{text}{Fore.RESET}'
                    break

        try:
            print(text)
        except UnicodeError:
            try:
                print(text.encode(UTF8, errors=Log.ERR_POLICY).decode(getpreferredencoding(), errors=Log.ERR_POLICY))
            except Exception:
                print('<Message was not logged due to UnicodeError>')

    @staticmethod
    def fatal(text: str) -> None:
        return Log.log(text, LoggingFlags.FATAL)

    @staticmethod
    def error(text: str, extra_flags=LoggingFlags.NONE) -> None:
        return Log.log(text, LoggingFlags.ERROR | extra_flags)

    @staticmethod
    def warn(text: str, extra_flags=LoggingFlags.NONE) -> None:
        return Log.log(text, LoggingFlags.WARN | extra_flags)

    @staticmethod
    def info(text: str, extra_flags=LoggingFlags.NONE) -> None:
        return Log.log(text, LoggingFlags.INFO | extra_flags)

    @staticmethod
    def debug(text: str, extra_flags=LoggingFlags.NONE) -> None:
        return Log.log(text, LoggingFlags.DEBUG | extra_flags)

    @staticmethod
    def trace(text: str, extra_flags=LoggingFlags.NONE) -> None:
        return Log.log(text, LoggingFlags.TRACE | extra_flags)

#
#
#########################################
