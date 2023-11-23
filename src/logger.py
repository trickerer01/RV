# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from locale import getpreferredencoding

from colorama import Fore, init as colorama_init

from defs import LoggingFlags, UTF8
from config import Config


class Log:
    """
    Basic logger supporting different log levels, colors and extra logging flags\n
    **Static**
    """
    _disabled = False

    COLORS = {
        LoggingFlags.LOGGING_TRACE: Fore.WHITE,
        LoggingFlags.LOGGING_DEBUG: Fore.LIGHTWHITE_EX,
        LoggingFlags.LOGGING_INFO: Fore.LIGHTCYAN_EX,
        LoggingFlags.LOGGING_WARN: Fore.LIGHTYELLOW_EX,
        LoggingFlags.LOGGING_ERROR: Fore.LIGHTYELLOW_EX,
        LoggingFlags.LOGGING_FATAL: Fore.LIGHTRED_EX
    }

    @staticmethod
    def init() -> None:
        colorama_init()

    @staticmethod
    def should_log(flags: LoggingFlags) -> bool:
        return flags >= Config.logging_flags and not Log._disabled

    @staticmethod
    def log(text: str, flags: LoggingFlags) -> None:
        # if flags & LoggingFlags.LOGGING_FATAL == 0 and Config.logging_flags & flags != flags:
        if not Log.should_log(flags):
            return

        for f in reversed(Log.COLORS.keys()):
            if f & flags:
                text = f'{Log.COLORS[f]}{text}{Fore.RESET}'
                break

        try:
            print(text)
        except UnicodeError:
            try:
                print(text.encode(UTF8).decode())
            except Exception:
                try:
                    print(text.encode(UTF8).decode(getpreferredencoding()))
                except Exception:
                    print('<Message was not logged due to UnicodeError>')
            finally:
                print('Previous message caused UnicodeError...')

    @staticmethod
    def fatal(text: str) -> None:
        return Log.log(text, LoggingFlags.LOGGING_FATAL)

    @staticmethod
    def error(text: str, extra_flags=LoggingFlags.LOGGING_NONE) -> None:
        return Log.log(text, LoggingFlags.LOGGING_ERROR | extra_flags)

    @staticmethod
    def warn(text: str, extra_flags=LoggingFlags.LOGGING_NONE) -> None:
        return Log.log(text, LoggingFlags.LOGGING_WARN | extra_flags)

    @staticmethod
    def info(text: str, extra_flags=LoggingFlags.LOGGING_NONE) -> None:
        return Log.log(text, LoggingFlags.LOGGING_INFO | extra_flags)

    @staticmethod
    def debug(text: str, extra_flags=LoggingFlags.LOGGING_NONE) -> None:
        return Log.log(text, LoggingFlags.LOGGING_DEBUG | extra_flags)

    @staticmethod
    def trace(text: str, extra_flags=LoggingFlags.LOGGING_NONE) -> None:
        return Log.log(text, LoggingFlags.LOGGING_TRACE | extra_flags)

#
#
#########################################
