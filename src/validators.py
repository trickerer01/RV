# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import os
from argparse import ArgumentError
from ipaddress import IPv4Address

from aiohttp import ClientTimeout

from config import Config
from defs import (
    CONNECT_TIMEOUT_BASE,
    CONNECT_TIMEOUT_SOCKET_READ,
    DEFAULT_QUALITY,
    DOWNLOAD_POLICY_DEFAULT,
    DURATION_MAX,
    IDGAP_PREDICTION_OFF,
    LOGGING_FLAGS,
    NAMING_FLAGS,
    SEARCH_RULE_ALL,
    SLASH,
    Duration,
    LoggingFlags,
    NamingFlags,
)
from logger import Log
from rex import re_non_search_symbols, re_session_id
from util import has_naming_flag, normalize_path


def find_and_resolve_config_conflicts(full_download=True) -> bool:
    if Config.playlist_name and (Config.search or Config.search_tags or Config.search_arts or Config.search_cats):
        Log.fatal('\nError: cannot use search within playlist! Please use one or the other, or filter using extra tags')
        raise ValueError
    if Config.uploader and (Config.search or Config.search_tags or Config.search_arts or Config.search_cats):
        Log.fatal('\nError: cannot use search within uploader\'s videos! Please use one or the other, or filter using extra tags')
        raise ValueError
    if Config.model and (Config.search or Config.search_tags or Config.search_arts or Config.search_cats):
        Log.fatal('\nError: cannot use search within artist\'s videos! Please use one or the other, or filter using extra tags')
        raise ValueError
    if Config.proxy and Config.download_without_proxy and Config.html_without_proxy:
        Log.fatal('\nError: proxy exists but is disabled for both html and download requests!')
        raise ValueError
    if all(_ in (False, None) for _ in (Config.use_id_sequence, Config.use_link_sequence)):
        if Config.start_id > Config.end_id or Config.start > Config.end:
            Log.fatal(f'\nError: invalid id bounds: start ({Config.start:d}|{Config.start_id}) > end ({Config.end:d}|{Config.end_id})')
            raise ValueError
    if Config.lookahead:
        if Config.use_id_sequence:
            Log.fatal('\nError: lookahead argument cannot be used together with id sequence!')
            raise ValueError
        if Config.store_continue_cmdfile:
            Log.fatal('\nError: lookahead argument prevents saving continue cmdfile, unexpected behavior possible!')
            raise ValueError
    if Config.use_link_sequence:
        if Config.use_id_sequence:
            Log.fatal('\nError: link sequence argument cannot be used together with id sequence!')
            raise ValueError
        if Config.lookahead:
            Log.fatal('\nError: link sequence argument cannot be used together with lookahead!')
            raise ValueError

    if Config.get_maxid:
        Config.logging_flags = LoggingFlags.FATAL
        Config.start = Config.end = Config.start_id = Config.end_id = 1
        return False

    if Config.search_tags and ',' in Config.search_tags and Config.search_rule_tag == SEARCH_RULE_ALL:
        Config.search_tags = f'{SEARCH_RULE_ALL},{Config.search_tags}'
    if Config.search_arts and ',' in Config.search_arts and Config.search_rule_art == SEARCH_RULE_ALL:
        Config.search_arts = f'{SEARCH_RULE_ALL},{Config.search_arts}'
    if Config.search_cats and ',' in Config.search_cats and Config.search_rule_cat == SEARCH_RULE_ALL:
        Config.search_cats = f'{SEARCH_RULE_ALL},{Config.search_cats}'

    delay_for_message = False

    if Config.watcher_mode:
        Log.info('Info: watcher mode enabled, disabling id gaps detection')
        Config.detect_id_gaps = False
        delay_for_message = True
    if Config.detect_id_gaps:
        if Config.predict_id_gaps != IDGAP_PREDICTION_OFF:
            Log.info('Info: id gaps detection is enabled, disabling id gaps prediction')
            Config.predict_id_gaps = IDGAP_PREDICTION_OFF
            delay_for_message = True

    if Config.scan_all_pages and Config.start_id <= 1:
        Log.info('Info: \'--scan-all-pages\' flag was set but post id lower bound was not provided, ignored')
        delay_for_message = True

    if Config.scenario is not None:
        if Config.utp != DOWNLOAD_POLICY_DEFAULT:
            Log.info('Info: running download script, outer untagged policy will be ignored')
            Config.utp = DOWNLOAD_POLICY_DEFAULT
            delay_for_message = True
        if len(Config.extra_tags) > 0:
            Log.info(f'Info: running download script: outer extra tags: {Config.extra_tags!s}')
            delay_for_message = True
        if Config.min_score is not None:
            Log.info(f'Info: running download script: outer minimum score: {Config.min_score:d}')
            delay_for_message = True
        if Config.min_rating > 0:
            Log.info(f'Info: running download script: outer minimum rating: {Config.min_rating:d}')
            delay_for_message = True
        if Config.quality != DEFAULT_QUALITY:
            Log.info(f'Info: running download script, outer quality: {Config.quality}')
            delay_for_message = True
    if full_download is False:
        if Config.scenario is not None:
            Log.info('Info: scenarios are ignored for previews!')
            delay_for_message = True
        if len(Config.extra_tags) > 0:
            Log.info('Info: extra tags are ignored for previews!')
            delay_for_message = True
        if Config.utp != DOWNLOAD_POLICY_DEFAULT:
            Log.info('Info: untagged videos download policy is ignored for previews!')
            delay_for_message = True
        if Config.save_tags is True:
            Log.info('Info: tags are not saved for previews!')
            delay_for_message = True
        if Config.min_score:
            Log.info('Info: score is not extracted from previews!')
            delay_for_message = True
        if Config.min_rating:
            Log.info('Info: rating is not extracted from previews!')
            delay_for_message = True
        if (Config.naming_flags & NamingFlags.ALL_DEFAULT) != NamingFlags.ALL_DEFAULT:
            if has_naming_flag(NamingFlags.ALL_DEFAULT & ~(NamingFlags.PREFIX | NamingFlags.TITLE)):
                Log.info('Info: can only use prefix and title naming flags for previews, other flags will be ignored!')
                delay_for_message = True
    return delay_for_message


def valid_int(val: str, *, lb: int | None = None, ub: int | None = None, nonzero=False) -> int:
    try:
        val = int(val)
        assert lb is None or val >= lb
        assert ub is None or val <= ub
        assert nonzero is False or val != 0
        return val
    except Exception:
        raise ArgumentError


def positive_int(val: str) -> int:
    return valid_int(val, lb=0)


def nonzero_int(val: str) -> int:
    return valid_int(val, nonzero=True)


def positive_nonzero_int(val: str) -> int:
    return valid_int(val, lb=1)


def valid_rating(val: str) -> int:
    return valid_int(val, lb=0, ub=100)


def valid_lookahead(val: str) -> int:
    return valid_int(val, lb=-200, ub=200, nonzero=True)


def valid_path(pathstr: str) -> str:
    try:
        newpath = normalize_path(os.path.expanduser(pathstr.strip('\'"')))
        assert os.path.isdir(newpath[:(newpath.find(SLASH) + 1)])
        return newpath
    except Exception:
        raise ArgumentError


def valid_filepath_abs(pathstr: str) -> str:
    try:
        newpath = normalize_path(os.path.expanduser(pathstr.strip('\'"')), False)
        assert os.path.isfile(newpath) and os.path.isabs(newpath)
        return newpath
    except Exception:
        raise ArgumentError


def valid_search_string(search_str: str) -> str:
    try:
        assert len(search_str) == 0 or re_non_search_symbols.search(search_str) is None
        return search_str
    except Exception:
        raise ArgumentError


def valid_proxy(prox: str) -> str:
    from ctypes import c_uint16, sizeof
    try:
        if not prox:
            return prox
        try:
            pt, pv = tuple(prox.split('://', 1))
        except ValueError:
            Log.error('Failed to split proxy type and value/port!')
            raise
        if pt not in {'http', 'socks4', 'socks5', 'socks5h'}:
            Log.error(f'Invalid proxy type: \'{pt}\'!')
            raise ValueError
        try:
            pv, pp = tuple(pv.rsplit(':', 1))
        except ValueError:
            Log.error('Failed to split proxy address and port!')
            raise
        try:
            pup, pvv = tuple(pv.rsplit('@', 1)) if ('@' in pv) else ('', pv)
            if pup:
                pup = f'{pup}@'
        except ValueError:
            Log.error('Failed to split proxy address and port!')
            raise
        try:
            pva = IPv4Address(pvv)
        except ValueError:
            Log.error(f'Invalid proxy ip address value \'{pv}\'!')
            raise
        try:
            ppi = int(pp)
            assert 20 < ppi < 2 ** (8 * sizeof(c_uint16))
        except (ValueError, AssertionError):
            Log.error(f'Invalid proxy port value \'{pp}\'!')
            raise
        return f'{pt}://{pup}{pva!s}:{ppi:d}'
    except Exception:
        raise ArgumentError


def naming_flags(flags: str) -> int:
    try:
        if flags[0].isnumeric():
            intflags = int(flags, base=16 if flags.startswith('0x') else 10)
            assert intflags & ~NamingFlags.ALL == 0
        else:
            intflags = sum(int(NAMING_FLAGS[fname], base=16) for fname in flags.split('|'))
        return intflags
    except Exception:
        raise ArgumentError


def log_level(level: str) -> int:
    try:
        return int(LOGGING_FLAGS[level], 16)
    except Exception:
        raise ArgumentError


def valid_session_id(sessionid: str) -> str:
    try:
        assert (not sessionid) or re_session_id.fullmatch(sessionid)
        return sessionid
    except Exception:
        raise ArgumentError


def valid_duration(duration: str) -> Duration:
    try:
        duration = duration or f'0-{DURATION_MAX:d}'
        parts = duration.split('-', maxsplit=2)
        assert len(parts) == 2
        dur_min = valid_int(parts[0], lb=0, ub=DURATION_MAX)
        dur_max = valid_int(parts[1], lb=dur_min, ub=DURATION_MAX)
        return Duration(dur_min, dur_max)
    except Exception:
        raise ArgumentError


def valid_timeout(timeout: str) -> ClientTimeout:
    try:
        timeout_int = positive_nonzero_int(timeout) if timeout else CONNECT_TIMEOUT_BASE
        return ClientTimeout(total=None, connect=timeout_int, sock_connect=timeout_int, sock_read=float(CONNECT_TIMEOUT_SOCKET_READ))
    except Exception:
        raise ArgumentError

#
#
#########################################
