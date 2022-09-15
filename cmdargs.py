# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import os.path as path
from argparse import ArgumentParser, Namespace, ArgumentError
from re import match as re_match, sub as re_sub
from typing import Optional, List

from defs import SLASH, Log, NON_SEARCH_SYMBOLS, QUALITIES, MODE_PREVIEW, MODE_BEST, MODE_LOWQ, HELP_PATH, HELP_QUALITY, HELP_PAGES, \
    HELP_STOP_ID, HELP_MODE, HELP_SEARCH, HELP_ARG_PROXY, HELP_BEGIN_ID

MODES = (MODE_PREVIEW, MODE_BEST, MODE_LOWQ)

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
        newpath = path.abspath(unquote(pathstr)).replace('\\', SLASH)
        if not path.exists(newpath[:(newpath.find(SLASH) + 1)]):
            raise ValueError
        if newpath[-1] != SLASH:
            newpath += SLASH
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
    try:
        parsed, unk = parser.parse_known_args(args)
        if len(unk) > 0:
            Log(f'\ninvalid arguments found:{str(unk)}\n')
            raise ArgumentError
        # Log('parsed:', parsed)
    except (ArgumentError, TypeError, Exception):
        # Log('\n', e)
        parser.print_help()
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


def add_common_args(parser_or_group: ArgumentParser) -> None:
    parser_or_group.add_argument('-path', default=path.abspath(path.curdir), help=HELP_PATH, type=valid_path)
    parser_or_group.add_argument('-proxy', metavar='#type://a.d.d.r:port', help=HELP_ARG_PROXY, type=valid_proxy)


def prepare_arglist_ids(args: List[str]) -> Namespace:
    global parser

    parser = ArgumentParser()

    parser.add_argument('-start', metavar='#number', required=True, help='Start video id. Required', type=valid_positive_nonzero_int)
    arggr_ids = parser.add_mutually_exclusive_group()
    arggr_ids.add_argument('-count', metavar='#number', default=1, help='Ids count to process', type=valid_positive_nonzero_int)
    arggr_ids.add_argument('-end', metavar='#number', default=1, help='End video id', type=valid_positive_nonzero_int)
    parser.add_argument('-quality', default=QUALITIES[0], help=HELP_QUALITY, choices=QUALITIES)
    add_common_args(parser)

    def finalize_ex_groups(parsed: Namespace) -> Namespace:
        if parsed.end < parsed.start + parsed.count - 1:
            parsed.end = parsed.start + parsed.count - 1
        parsed.count = None

        return parsed

    try:
        return finalize_ex_groups(validate_parsed(args))
    except (ArgumentError, TypeError, Exception):
        raise


def prepare_arglist_pages(args: List[str]) -> Namespace:
    global parser

    parser = ArgumentParser()

    parser.add_argument('-start', metavar='#number', default=1, help='Start page number. Default is \'1\'', type=valid_positive_nonzero_int)
    parser.add_argument('-pages', metavar='#number', required=True, help=HELP_PAGES, type=valid_positive_nonzero_int)
    parser.add_argument('-stop_id', metavar='#number', default=1, help=HELP_STOP_ID, type=valid_positive_nonzero_int)
    parser.add_argument('-begin_id', metavar='#number', default=1000000000, help=HELP_BEGIN_ID, type=valid_positive_nonzero_int)
    parser.add_argument('-mode', default=MODE_BEST, help=HELP_MODE, choices=MODES)
    parser.add_argument('-search', metavar='#string', default='', help=HELP_SEARCH, type=valid_search_string)
    add_common_args(parser)

    try:
        return validate_parsed(args)
    except (ArgumentError, TypeError, Exception):
        raise

#
#
#########################################
