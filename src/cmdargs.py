# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import ArgumentParser, Namespace, ArgumentError, ZERO_OR_MORE
from os import path
from re import match as re_match, sub as re_sub
from typing import Optional, List

from defs import (
    SLASH, Log, NON_SEARCH_SYMBOLS, QUALITIES, DEFAULT_QUALITY, HELP_PATH, HELP_QUALITY, HELP_PAGES,
    HELP_STOP_ID, HELP_SEARCH, HELP_ARG_PROXY, HELP_BEGIN_ID,
    HELP_ARG_EXTRA_TAGS, HELP_ARG_UVPOLICY, UVIDEO_POLICIES, DOWNLOAD_POLICY_DEFAULT, DOWNLOAD_MODES, DOWNLOAD_MODE_DEFAULT,
    HELP_ARG_DMMODE, HELP_ARG_DWN_SCENARIO, HELP_ARG_NO_VALIDATION, ACTION_STORE_TRUE, normalize_path,
)
from scenario import DownloadScenario
from tagger import extra_tag

UVP_DEFAULT = DOWNLOAD_POLICY_DEFAULT
DM_DEFAULT = DOWNLOAD_MODE_DEFAULT

parser = None  # type: Optional[ArgumentParser]


def unquote(string: str) -> str:
    try:
        while True:
            found = False
            if len(string) > 1 and string[0] in ['\'', '"']:
                string = string[1:]
                found = True
            if len(string) > 1 and string[-1] in ['\'', '"']:
                string = string[:-1]
                found = True
            if not found:
                break
        return string
    except Exception:
        raise ValueError


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
        if not path.exists(newpath[:(newpath.find(SLASH) + 1)]):
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


def validate_parsed(args) -> Namespace:
    global parser

    error_to_print = ''
    try:
        parsed, unks = parser.parse_known_args(args)
        parsed.extra_tags += [tag.lower().replace(' ', '_') for tag in unks]
        # Log('parsed:', parsed)
    except (ArgumentError, TypeError, Exception):
        # Log('\n', e)
        parser.print_help()
        if error_to_print != '':
            Log(error_to_print)
        raise

    return parsed


def valid_proxy(prox: str) -> str:
    try:
        # replace front trailing zeros: 01.0144.022.055:002022 -> 1.144.22.55:2022
        newval = str(re_sub(r'([^\d]|^)0+([1-9](?:[0-9]+)?)', r'\1\2', prox))
        # validate IP with port
        adr_valid = (newval == '') or re_match(r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,5})', newval) is not None
        if adr_valid and len(newval) > 0:
            #  port
            ps = str(newval).split(':')
            ips = ps[0].split('.') if (ps and len(ps) > 0) else []
            if len(ps) != 2 or len(ips) != 4:
                adr_valid = False
            if adr_valid:
                try:
                    if ps[1][0] == '0':
                        raise Exception
                    port = int(ps[1])
                    if port < 20 or port > 65535:
                        raise Exception
                except Exception:
                    adr_valid = False
            #  ip
            if adr_valid:
                try:
                    for ip in ips:
                        if len(ip) == 0 or (len(ip) > 1 and ip[0] == '0'):
                            raise Exception
                        iip = int(ip)
                        if iip < 0 or iip > 255:
                            raise Exception
                except Exception as e:
                    raise e
    except Exception:
        raise ArgumentError

    return newval


def download_scenario_format(fmt_str: str) -> DownloadScenario:
    try:
        return DownloadScenario.from_string(fmt_str)
    except Exception:
        raise ArgumentError


def add_common_args(parser_or_group: ArgumentParser) -> None:
    parser_or_group.add_argument('-path', default=path.abspath(path.curdir), help=HELP_PATH, type=valid_path)
    parser_or_group.add_argument('-quality', default=DEFAULT_QUALITY, help=HELP_QUALITY, choices=QUALITIES)
    parser_or_group.add_argument('-proxy', metavar='#type://a.d.d.r:port', help=HELP_ARG_PROXY, type=valid_proxy)
    parser_or_group.add_argument('-uvp', '--untag-video-policy', default=UVP_DEFAULT, help=HELP_ARG_UVPOLICY, choices=UVIDEO_POLICIES)
    parser_or_group.add_argument('-dmode', '--download-mode', default=DM_DEFAULT, help=HELP_ARG_DMMODE, choices=DOWNLOAD_MODES)
    parser_or_group.add_argument('-tdump', '--dump-tags', action=ACTION_STORE_TRUE, help='Save tags (full download only)')
    parser_or_group.add_argument('--verbose', action=ACTION_STORE_TRUE, help='Use verbose mode for output')
    parser_or_group.add_argument('-script', '--download-scenario', default=None, help=HELP_ARG_DWN_SCENARIO, type=download_scenario_format)
    parser_or_group.add_argument('--no-validation', action=ACTION_STORE_TRUE, help=HELP_ARG_NO_VALIDATION)
    parser_or_group.add_argument(dest='extra_tags', nargs=ZERO_OR_MORE, help=HELP_ARG_EXTRA_TAGS, type=extra_tag)


def prepare_arglist_ids(args: List[str]) -> Namespace:
    global parser

    parser = ArgumentParser(add_help=False)
    parser.add_argument('--help', action='help')

    arggr_start_or_seq = parser.add_mutually_exclusive_group(required=True)
    arggr_start_or_seq.add_argument('-start', metavar='#number', help='Start video id. Required', type=valid_positive_nonzero_int)
    arggr_start_or_seq.add_argument('-seq', '--use-id-sequence', action=ACTION_STORE_TRUE, help='Use id sequence instead (in tags)')
    arggr_ids = parser.add_mutually_exclusive_group()
    arggr_ids.add_argument('-count', metavar='#number', default=1, help='Ids count to process', type=valid_positive_nonzero_int)
    arggr_ids.add_argument('-end', metavar='#number', default=1, help='End video id', type=valid_positive_nonzero_int)
    add_common_args(parser)

    def finalize_ex_groups(parsed: Namespace) -> Namespace:
        if parsed.use_id_sequence:
            parsed.start = parsed.end = None
        elif parsed.end < parsed.start + parsed.count - 1:
            parsed.end = parsed.start + parsed.count - 1
        parsed.count = None

        return parsed

    try:
        return finalize_ex_groups(validate_parsed(args))
    except (ArgumentError, TypeError, Exception):
        raise


def prepare_arglist_pages(args: List[str]) -> Namespace:
    global parser

    parser = ArgumentParser(add_help=False)
    parser.add_argument('--help', action='help')

    parser.add_argument('-start', metavar='#number', default=1, help='Start page number. Default is \'1\'', type=valid_positive_nonzero_int)
    parser.add_argument('-pages', metavar='#number', required=True, help=HELP_PAGES, type=valid_positive_nonzero_int)
    parser.add_argument('-stop_id', metavar='#number', default=1, help=HELP_STOP_ID, type=valid_positive_nonzero_int)
    parser.add_argument('-begin_id', metavar='#number', default=1000000000, help=HELP_BEGIN_ID, type=valid_positive_nonzero_int)
    parser.add_argument('-search', metavar='#string', default='', help=HELP_SEARCH, type=valid_search_string)
    add_common_args(parser)

    try:
        return validate_parsed(args)
    except (ArgumentError, TypeError, Exception):
        raise

#
#
#########################################
