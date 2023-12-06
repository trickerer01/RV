# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import sys
from datetime import datetime

from config import Config
from defs import START_TIME, SLASH, DOWNLOAD_MODE_FULL
from logger import Log
from rex import re_replace_symbols, re_ext


def format_time(seconds: int) -> str:
    """Formats time from seconds to format: **hh:mm:ss**"""
    mm, ss = divmod(seconds, 60)
    hh, mm = divmod(mm, 60)
    return f'{hh:02d}:{mm:02d}:{ss:02d}'


def get_elapsed_time_i() -> int:
    """Returns time since launch in **seconds**"""
    return (datetime.now() - START_TIME).seconds


def get_elapsed_time_s() -> str:
    """Returns time since launch in format: **hh:mm:ss**"""
    return format_time(get_elapsed_time_i())


def normalize_path(basepath: str, append_slash=True) -> str:
    """Converts path string to universal slash-concatenated string, enclosing slash is optional"""
    normalized_path = basepath.replace('\\', SLASH)
    if append_slash and len(normalized_path) != 0 and normalized_path[-1] != SLASH:
        normalized_path += SLASH
    return normalized_path


def normalize_filename(filename: str, base_path: str) -> str:
    """Returns full path to a file, normalizing base path and removing disallowed symbols from file name"""
    return normalize_path(base_path) + re_replace_symbols.sub('_', filename)


def extract_ext(href: str) -> str:
    ext_match = re_ext.search(href)
    return ext_match.group(1) if ext_match else '.mp4'


def has_naming_flag(flag: int) -> bool:
    return not not (Config.naming_flags & flag)


def calc_sleep_time(base_time: float) -> float:
    """Returns either base_time for full download or shortened time otherwise"""
    return base_time if Config.download_mode == DOWNLOAD_MODE_FULL else max(1.0, base_time / 3.0)


def at_startup() -> None:
    """Inits logger. Reports python version and run options"""
    Log.init()
    Log.debug(f'Python {sys.version}\nCommand-line args: {" ".join(sys.argv)}')

#
#
#########################################
