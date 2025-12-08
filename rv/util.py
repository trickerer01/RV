# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import datetime
import time
from collections.abc import Iterable, Sequence

from .config import Config
from .defs import CONNECT_REQUEST_DELAY, DEFAULT_EXT, DOWNLOAD_MODE_FULL, SLASH, START_TIME
from .rex import re_ext


def assert_nonempty(container: Iterable, message='') -> Iterable:
    assert container, message
    return container


def get_time_seconds(timespan: str) -> int:
    """Converts time from **[hh:][mm:]ss** format to **seconds**"""
    return sum(int(part) * pow(60, idx) for idx, part in enumerate(reversed(timespan.split(':'))))


def format_time(seconds: int) -> str:
    """Formats time from seconds to: **hh:mm:ss**"""
    mm, ss = divmod(seconds, 60)
    hh, mm = divmod(mm, 60)
    return f'{hh:02d}:{mm:02d}:{ss:02d}'


def get_elapsed_time_i() -> int:
    """Returns time since launch in **seconds**"""
    return (datetime.datetime.now() - START_TIME).seconds


def get_elapsed_time_s() -> str:
    """Returns time since launch in format: **hh:mm:ss**"""
    return format_time(get_elapsed_time_i())


def get_local_time_i() -> int:
    """Returns **local** time since epoch in **seconds**"""
    return int(datetime.datetime.now().timestamp()) + time.localtime().tm_gmtoff


def get_local_time_s(*, offset=0) -> str:
    """Returns **local** time **[+offset]** in 24hr format: **hh:mm:ss**"""
    return format_time((get_local_time_i() + offset) % 86400)


def normalize_path(basepath: str, append_slash=True) -> str:
    """Converts path string to universal slash-concatenated string, enclosing slash is optional"""
    normalized_path = basepath.replace('\\', SLASH)
    if append_slash and normalized_path and not normalized_path.endswith(SLASH):
        normalized_path += SLASH
    return normalized_path


def sanitize_filename(filename_base: str) -> str:
    def char_replace(char: str) -> str:
        if char in '\n\r\t"*:<>?|/\\':
            return {'/': '\u29f8', '\\': '\u29f9', '\n': '', '\r': '', '\t': ''}.get(char, chr(ord(char) + 0xfee0))
        elif ord(char) < 32 or ord(char) == 127:
            char = ''
        return char

    filename = ''.join(map(char_replace, filename_base)).replace('\0', '_')
    while '__' in filename:
        filename = filename.replace('__', '_')
    return filename.strip('_')


def normalize_filename(filename: str, base_path: str) -> str:
    """Returns full path to a file, normalizing base path and removing disallowed symbols from file name"""
    return f'{normalize_path(base_path)}{sanitize_filename(filename)}'


def extract_ext(href: str) -> str:
    ext_match = re_ext.search(href)
    return ext_match.group(1) if ext_match else f'.{DEFAULT_EXT}'


def has_naming_flag(flag: int) -> bool:
    return bool(Config.naming_flags & flag)


def calc_sleep_time(base_time: float) -> float:
    """Returns either base_time for full download or shortened time otherwise"""
    return base_time if Config.download_mode == DOWNLOAD_MODE_FULL else max(1.0, base_time / 3.0)


def calculate_eta(container: Sequence) -> int:
    return int(2.0 + (CONNECT_REQUEST_DELAY + 0.2 + 0.02) * len(container))

#
#
#########################################
