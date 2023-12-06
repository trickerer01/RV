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

from config import Config
from defs import NamingFlags, LoggingFlags, SLASH, NAMING_FLAGS, LOGGING_FLAGS, DOWNLOAD_POLICY_DEFAULT, DEFAULT_QUALITY, SEARCH_RULE_ALL
from logger import Log
from rex import re_non_search_symbols, re_session_id
from util import normalize_path, has_naming_flag


def find_and_resolve_config_conflicts(full_download=True) -> bool:
    if Config.playlist_name and (Config.search or Config.search_tags or Config.search_arts or Config.search_cats):
        Log.fatal('\nError: cannot use search within playlist! Please use one or the other')
        raise ValueError
    if Config.uploader and (Config.search or Config.search_tags or Config.search_arts or Config.search_cats):
        Log.fatal('\nError: cannot use search within uploader\'s videos! Please use one or the other')
        raise ValueError
    if Config.use_id_sequence in (False, None) and Config.start_id > Config.end_id:
        Log.fatal(f'\nError: invalid video id bounds: start ({Config.start_id:d}) > end ({Config.end_id:d})')
        raise ValueError

    if Config.get_maxid:
        Config.logging_flags = LoggingFlags.LOGGING_FATAL
        Config.start = Config.end = Config.start_id = Config.end_id = 1

    if Config.search_tags.find(',') != -1 and Config.search_rule_tag == SEARCH_RULE_ALL:
        Config.search_tags = f'{SEARCH_RULE_ALL},{Config.search_tags}'
    if Config.search_arts.find(',') != -1 and Config.search_rule_art == SEARCH_RULE_ALL:
        Config.search_arts = f'{SEARCH_RULE_ALL},{Config.search_arts}'
    if Config.search_cats.find(',') != -1 and Config.search_rule_cat == SEARCH_RULE_ALL:
        Config.search_cats = f'{SEARCH_RULE_ALL},{Config.search_cats}'

    delay_for_message = False
    if Config.save_comments is True and Config.session_id is None:
        Log.info('Info: Comments cannot be accessed without `-session_id`, saving comments is impossible. Disabled!')
        Config.save_comments = False
        delay_for_message = True
    if Config.scenario is not None:
        if Config.uvp != DOWNLOAD_POLICY_DEFAULT:
            Log.info('Info: running download script, outer untagged policy will be ignored')
            Config.uvp = DOWNLOAD_POLICY_DEFAULT
            delay_for_message = True
        if len(Config.extra_tags) > 0:
            Log.info(f'Info: running download script: outer extra tags: {str(Config.extra_tags)}')
            delay_for_message = True
        if Config.min_score is not None:
            Log.info(f'Info: running download script: outer minimum score: {Config.min_score:d}')
            delay_for_message = True
        if Config.min_rating > 0:
            Log.info(f'Info: running download script: outer minimum rating: {Config.min_rating:d}')
            delay_for_message = True
        if Config.quality != DEFAULT_QUALITY:
            Log.info('Info: running download script, outer quality setting will be ignored')
            delay_for_message = True
    if full_download is False:
        if Config.scenario is not None:
            Log.info('Info: scenarios are ignored for previews!')
            delay_for_message = True
        if len(Config.extra_tags) > 0:
            Log.info('Info: extra tags are ignored for previews!')
            delay_for_message = True
        if Config.uvp != DOWNLOAD_POLICY_DEFAULT:
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
        if Config.naming_flags != NamingFlags.NAMING_FLAGS_ALL:
            if has_naming_flag(NamingFlags.NAMING_FLAGS_ALL & ~(NamingFlags.NAMING_FLAG_PREFIX | NamingFlags.NAMING_FLAG_TITLE)):
                Log.info('Info: can only use prefix and title naming flags for previews, other flags will be ignored!')
                delay_for_message = True
    return delay_for_message


def valid_int(val: str) -> int:
    try:
        return int(val)
    except Exception:
        raise ArgumentError


def positive_nonzero_int(val: str) -> int:
    try:
        val = int(val)
        assert val > 0
        return val
    except Exception:
        raise ArgumentError


def valid_rating(val: str) -> int:
    try:
        val = int(val)
        assert 100 >= val >= 0
        return val
    except Exception:
        raise ArgumentError


def valid_path(pathstr: str) -> str:
    try:
        newpath = normalize_path(path.expanduser(pathstr.strip('\'"')))
        assert path.isdir(newpath[:(newpath.find(SLASH) + 1)])
        return newpath
    except Exception:
        raise ArgumentError


def valid_filepath_abs(pathstr: str) -> str:
    try:
        newpath = normalize_path(path.expanduser(pathstr.strip('\'"')), False)
        assert path.isfile(newpath) and path.isabs(newpath)
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
    try:
        try:
            pt, pv = tuple(prox.split('://', 1))
        except ValueError:
            Log.error('Failed to split proxy type and value/port!')
            raise
        if pt not in {'http', 'https', 'socks5', 'socks5h'}:
            Log.error(f'Invalid proxy type: \'{pt}\'!')
            raise ValueError
        try:
            pv, pp = tuple(pv.split(':', 1))
        except ValueError:
            Log.error('Failed to split proxy address and port!')
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
        return f'{pt}://{str(pva)}:{ppi:d}'
    except Exception:
        raise ArgumentError


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


def valid_session_id(sessionid: str) -> str:
    try:
        assert (not sessionid) or re_session_id.fullmatch(sessionid)
        return sessionid
    except Exception:
        raise ArgumentError

#
#
#########################################
