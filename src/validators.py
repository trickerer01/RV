# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import ArgumentError
from ipaddress import IPv4Address
from os import path
from re import match as re_match

from defs import normalize_path, unquote, Log, NamingFlags, LoggingFlags, SLASH, NON_SEARCH_SYMBOLS, NAMING_FLAGS, LOGGING_FLAGS


def valid_int(val: str) -> int:
    try:
        return int(val)
    except Exception:
        raise ArgumentError


def valid_positive_nonzero_int(val: str) -> int:
    try:
        val = int(val)
        assert(val > 0)
    except Exception:
        raise ArgumentError

    return val


def valid_path(pathstr: str) -> str:
    try:
        newpath = normalize_path(unquote(pathstr))
        if not path.isdir(newpath[:(newpath.find(SLASH) + 1)]):
            raise ValueError
    except Exception:
        raise ArgumentError

    return newpath


def valid_filepath_abs(pathstr: str) -> str:
    try:
        newpath = normalize_path(unquote(pathstr), False)
        if not path.isfile(newpath):
            raise ValueError
        if not path.isabs(newpath):
            raise ValueError
    except Exception:
        raise ArgumentError

    return newpath


def valid_search_string(search_str: str) -> str:
    try:
        if len(search_str) > 0 and re_match(fr'^.*{NON_SEARCH_SYMBOLS}.*$', search_str):
            raise ValueError
    except Exception:
        raise ArgumentError

    return search_str


def valid_proxy(prox: str) -> str:
    try:
        try:
            pt, pv = tuple(prox.split('://', 1))
        except ValueError:
            Log.error('Failed to split proxy type and value/port!')
            raise
        if pt not in ['http', 'https', 'socks5']:
            Log.error(f'Invalid proxy type: \'{pt}\'!')
            raise ValueError
        try:
            pv, pp = tuple(pv.split(':', 1))
        except ValueError:
            Log.error('Failed to split proxy value and port!')
            raise
        try:
            pva = IPv4Address(pv)
        except ValueError:
            Log.error(f'Invalid proxy ip address value \'{pv}\'!')
            raise
        try:
            ppi = int(pp)
            assert 20 < ppi < 65535
        except (ValueError, AssertionError,):
            Log.error(f'Invalid proxy ip port value \'{pp}\'!')
            raise
    except Exception:
        raise ArgumentError

    return f'{pt}://{str(pva)}:{ppi:d}'


def naming_flags(flags: str) -> int:
    try:
        if flags[0].isnumeric():
            intflags = int(flags, base=16 if flags.startswith('0x') else 10)
            assert intflags & ~NamingFlags.NAMING_FLAGS_ALL == 0
        else:
            intflags = 0
            for fname in flags.split('|'):
                intflags |= int(NAMING_FLAGS[fname], base=16)
        return intflags
    except Exception:
        raise ArgumentError


def log_level(level: str) -> LoggingFlags:
    try:
        return LoggingFlags(int(LOGGING_FLAGS[level], 16))
    except Exception:
        raise ArgumentError

#
#
#########################################
