# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import os
from argparse import ZERO_OR_MORE, ArgumentParser, Namespace
from collections.abc import Sequence

from .config import Config
from .defs import (
    ACTION_APPEND,
    ACTION_EXTEND,
    ACTION_STORE_TRUE,
    CONNECT_RETRIES_BASE,
    DEFAULT_QUALITY,
    DOWNLOAD_MODE_DEFAULT,
    DOWNLOAD_MODES,
    DOWNLOAD_POLICY_DEFAULT,
    HELP_ARG_ALL_PAGES,
    HELP_ARG_BEGIN_STOP_ID,
    HELP_ARG_BLACKLIST,
    HELP_ARG_CHECK_TITLEDESC,
    HELP_ARG_CHECK_UPLOADER,
    HELP_ARG_CMDFILE,
    HELP_ARG_CONTINUE,
    HELP_ARG_COOKIE,
    HELP_ARG_DMMODE,
    HELP_ARG_DUMP_INFO,
    HELP_ARG_DUMP_SCREENSHOTS,
    HELP_ARG_DURATION,
    HELP_ARG_DWN_SCENARIO,
    HELP_ARG_EXTRA_TAGS,
    HELP_ARG_FAVORITES,
    HELP_ARG_FSDEPTH,
    HELP_ARG_FSLEVELUP,
    HELP_ARG_GET_MAXID,
    HELP_ARG_HEADER,
    HELP_ARG_ID_COUNT,
    HELP_ARG_ID_END,
    HELP_ARG_ID_START,
    HELP_ARG_IDSEQUENCE,
    HELP_ARG_LINKSEQUENCE,
    HELP_ARG_LOGGING,
    HELP_ARG_LOOKAHEAD,
    HELP_ARG_MERGE_LISTS,
    HELP_ARG_MINRATING,
    HELP_ARG_MINSCORE,
    HELP_ARG_MODEL,
    HELP_ARG_NAMING,
    HELP_ARG_NOCOLORS,
    HELP_ARG_NOMOVE,
    HELP_ARG_PAGE_COUNT,
    HELP_ARG_PAGE_END,
    HELP_ARG_PAGE_START,
    HELP_ARG_PATH,
    HELP_ARG_PLAYLIST,
    HELP_ARG_PREDICT_ID_GAPS,
    HELP_ARG_PROXY,
    HELP_ARG_PROXYNODOWN,
    HELP_ARG_PROXYNOHTML,
    HELP_ARG_QUALITY,
    HELP_ARG_REPORT_DUPLICATES,
    HELP_ARG_RETRIES,
    HELP_ARG_SEARCH_ACT,
    HELP_ARG_SEARCH_RULE,
    HELP_ARG_SEARCH_STR,
    HELP_ARG_SESSION_ID,
    HELP_ARG_SKIP_EMPTY_LISTS,
    HELP_ARG_SOLVE_TAG_CONFLICTS,
    HELP_ARG_STORE_CONTINUE_CMDFILE,
    HELP_ARG_THROTTLE,
    HELP_ARG_THROTTLE_AUTO,
    HELP_ARG_TIMEOUT,
    HELP_ARG_UNFINISH,
    HELP_ARG_UPLOADER,
    HELP_ARG_UTPOLICY,
    HELP_ARG_VERSION,
    IDGAP_PREDICTION_DEFAULT,
    IDGAP_PREDICTION_MODES,
    LOGGING_FLAGS_DEFAULT,
    MAX_DEST_SCAN_SUB_DEPTH_DEFAULT,
    MAX_DEST_SCAN_UPLEVELS_DEFAULT,
    NAMING_FLAGS_DEFAULT,
    QUALITIES,
    SEARCH_RULE_DEFAULT,
    SEARCH_RULES,
    UNTAGGED_POLICIES,
    UTF8,
)
from .logger import Log
from .scenario import DownloadScenario
from .tagger import (
    valid_artists,
    valid_blacklist,
    valid_categories,
    valid_extra_tag,
    valid_playlist_id,
    valid_playlist_name,
    valid_tags,
)
from .validators import (
    log_level,
    naming_flags,
    positive_int,
    positive_nonzero_int,
    valid_duration,
    valid_filepath_abs,
    valid_int,
    valid_kwarg,
    valid_lookahead,
    valid_path,
    valid_proxy,
    valid_rating,
    valid_search_string,
    valid_session_id,
    valid_timeout,
)
from .version import APP_NAME, APP_VERSION

__all__ = ('HelpPrintExitException', 'parse_logging_args', 'prepare_arglist')

MODULE = APP_NAME.replace('-', '_')
INDENT = ' ' * 7

UTP_DEFAULT = DOWNLOAD_POLICY_DEFAULT
"""'nofilters'"""
DM_DEFAULT = DOWNLOAD_MODE_DEFAULT
"""'full'"""
NAMING_DEFAULT = NAMING_FLAGS_DEFAULT
'''0x1F'''
LOGGING_DEFAULT = LOGGING_FLAGS_DEFAULT
'''0x004'''
FSDEPTH_DEFAULT = MAX_DEST_SCAN_SUB_DEPTH_DEFAULT
'''1'''
FSUP_DEFAULT = MAX_DEST_SCAN_UPLEVELS_DEFAULT
'''0'''

PARSER_TITLE_NONE = ''
PARSER_TITLE_IDS = 'ids'
PARSER_TITLE_PAGES = 'pages'
PARSER_TITLE_FILE = 'ifile'

PARSER_TITLE_NAMES_REMAP: dict[str, str] = {
    PARSER_TITLE_FILE: 'file',
}

PARSER_PARAM_PARSER_TYPE = 'zzzparser_type'
PARSER_PARAM_PARSER_TITLE = 'zzzparser_title'

IDGP_DEFAULT = IDGAP_PREDICTION_DEFAULT
"""'0'"""

PARSED_ARGS_NO_CONSUME = {
    PARSER_PARAM_PARSER_TYPE,
    PARSER_PARAM_PARSER_TITLE,
    'pages',
    'count',
}


class HelpPrintExitException(Exception):
    pass


def parse_logging_args(args: Sequence[str]) -> None:
    parser = ArgumentParser(add_help=False)
    add_logging_args(parser)
    parsed = parser.parse_known_args(args)
    Config.logging_flags = parsed[0].log_level
    Config.disable_log_colors = parsed[0].disable_log_colors


def read_cmdfile(cmdfile_path: str) -> list[str]:
    """Read cmd args from a text file"""
    with open(cmdfile_path, 'rt', encoding=UTF8) as cmdfile:
        return [_.strip(' \n\ufeff') for _ in cmdfile]


def is_parsed_cmdfile(parsed_result: Namespace) -> bool:
    return getattr(parsed_result, PARSER_PARAM_PARSER_TITLE) == PARSER_TITLE_FILE


def validate_parsed(parser: ArgumentParser, args: Sequence[str]) -> Namespace:
    errors_to_print: list[str] = []
    parsed, unks = parser.parse_known_args(args)
    if not is_parsed_cmdfile(parsed):
        taglist: Sequence[str]
        for i, taglist in enumerate((parsed.extra_tags, unks)):
            for tag in taglist:
                try:
                    valid_tag = valid_extra_tag(tag, False)
                    if i > 0:
                        parsed.extra_tags.append(valid_tag)
                except (AssertionError, ValueError):
                    errors_to_print.append(f'Invalid extra tag: \'{tag}\'')
        if errors_to_print:
            Log.fatal('\n'.join(errors_to_print))
            raise ValueError
    return parsed


def execute_parser(parser: ArgumentParser, args: Sequence[str]) -> Namespace:
    if not args:
        parser.print_help()
        raise HelpPrintExitException

    try:
        assert args
        parsed = validate_parsed(parser, args)
        if not is_parsed_cmdfile(parsed):
            if getattr(parsed, PARSER_PARAM_PARSER_TITLE) == PARSER_TITLE_PAGES:
                parsed.is_pages = True
                parsed.playlist_id, parsed.playlist_name = parsed.playlist_id if parsed.playlist_id[0] else parsed.playlist_name
                if not parsed.get_maxid:
                    if parsed.end < parsed.start + parsed.pages - 1:
                        parsed.end = parsed.start + parsed.pages - 1
            else:
                if parsed.use_id_sequence or parsed.use_link_sequence:
                    parsed.start = parsed.end = None
                else:
                    parsed.end = max(parsed.end, parsed.start + parsed.count - 1)
        while is_parsed_cmdfile(parsed):
            parsed = parse_arglist(read_cmdfile(parsed.path))
        return parsed
    except SystemExit:
        raise HelpPrintExitException
    except Exception:
        from traceback import format_exc
        Log.fatal(format_exc())
        raise HelpPrintExitException


def create_parsers() -> dict[str, ArgumentParser]:
    def create_parser(sub, name: str, description: str) -> ArgumentParser:
        if sub:
            parser: ArgumentParser = sub.add_parser(PARSER_TITLE_NAMES_REMAP.get(name, name), description=description, add_help=False)
            parser.set_defaults(**{PARSER_PARAM_PARSER_TITLE: name})
        else:
            parser = ArgumentParser(add_help=False, prog=MODULE)
        parser.set_defaults(**{PARSER_PARAM_PARSER_TYPE: parser})
        assert name not in parsers
        parsers[name] = parser
        return parser

    def create_subparser(parser: ArgumentParser, title: str, dest: str):
        return parser.add_subparsers(required=True, title=title, dest=dest, prog=MODULE)

    parsers: dict[str, ArgumentParser] = {}

    parser_main = create_parser(None, PARSER_TITLE_NONE, '')
    subs_main = create_subparser(parser_main, 'subcommands', 'subcommand_1')

    _parser_ids = create_parser(subs_main, PARSER_TITLE_IDS, 'Scan posts by id')
    _parser_pages = create_parser(subs_main, PARSER_TITLE_PAGES, 'Scan post pages')
    _parser_file = create_parser(subs_main, PARSER_TITLE_FILE, 'Read cmdline from file')
    return parsers


def add_common_args(par: ArgumentParser) -> None:
    co = par.add_argument_group(title='connection options')
    co.add_argument('-proxy', metavar='#type://[u:p@]a.d.d.r:port', default=None, help=HELP_ARG_PROXY, type=valid_proxy)
    co.add_argument('-proxynodown', '--download-without-proxy', action=ACTION_STORE_TRUE, help=HELP_ARG_PROXYNODOWN)
    co.add_argument('-proxynohtml', '--html-without-proxy', action=ACTION_STORE_TRUE, help=HELP_ARG_PROXYNOHTML)
    co.add_argument('-timeout', metavar='#seconds', default=valid_timeout(''), help=HELP_ARG_TIMEOUT, type=valid_timeout)
    co.add_argument('-retries', metavar='#number', default=CONNECT_RETRIES_BASE, help=HELP_ARG_RETRIES, type=positive_int)
    co.add_argument('-throttle', metavar='#rate', default=0, help=HELP_ARG_THROTTLE, type=positive_nonzero_int)
    co.add_argument('-athrottle', '--throttle-auto', action=ACTION_STORE_TRUE, help=HELP_ARG_THROTTLE_AUTO)
    co.add_argument('-header', metavar='#name=value', action=ACTION_APPEND, help=HELP_ARG_HEADER, type=valid_kwarg)
    co.add_argument('-cookie', metavar='#name=value', action=ACTION_APPEND, help=HELP_ARG_COOKIE, type=valid_kwarg)
    co.add_argument('-session_id', default=None, help=HELP_ARG_SESSION_ID, type=valid_session_id)
    do = par.add_argument_group(title='download options')
    do.add_argument('-path', default=valid_path(os.path.abspath(os.path.curdir)), help=HELP_ARG_PATH, type=valid_path)
    do.add_argument('-quality', default=DEFAULT_QUALITY, help=HELP_ARG_QUALITY, choices=QUALITIES)
    do.add_argument('-fsdepth', metavar='#number', default=FSDEPTH_DEFAULT, help=HELP_ARG_FSDEPTH, type=positive_int)
    do.add_argument('-fslevelup', metavar='#number', default=FSUP_DEFAULT, help=HELP_ARG_FSLEVELUP, type=positive_nonzero_int)
    do.add_argument('-continue', '--continue-mode', action=ACTION_STORE_TRUE, help=HELP_ARG_CONTINUE)
    do.add_argument('-unfinish', '--keep-unfinished', action=ACTION_STORE_TRUE, help=HELP_ARG_UNFINISH)
    do.add_argument('--store-continue-cmdfile', action=ACTION_STORE_TRUE, help=HELP_ARG_STORE_CONTINUE_CMDFILE)
    do.add_argument('-nomove', '--no-rename-move', action=ACTION_STORE_TRUE, help=HELP_ARG_NOMOVE)
    do.add_argument('-naming', default=NAMING_DEFAULT, help=HELP_ARG_NAMING, type=naming_flags)
    do.add_argument('-dmode', '--download-mode', default=DM_DEFAULT, help=HELP_ARG_DMMODE, choices=DOWNLOAD_MODES)
    do.add_argument('-script', '--download-scenario', default=None, help=HELP_ARG_DWN_SCENARIO, type=DownloadScenario)
    doex = par.add_argument_group(title='extra download options')
    doex.add_argument('-tdump', '--dump-tags', action=ACTION_STORE_TRUE, help='')
    doex.add_argument('-ddump', '--dump-descriptions', action=ACTION_STORE_TRUE, help='')
    doex.add_argument('-cdump', '--dump-comments', action=ACTION_STORE_TRUE, help=HELP_ARG_DUMP_INFO)
    doex.add_argument('-dmerge', '--merge-lists', action=ACTION_STORE_TRUE, help=HELP_ARG_MERGE_LISTS)
    doex.add_argument('-dnoempty', '--skip-empty-lists', action=ACTION_STORE_TRUE, help=HELP_ARG_SKIP_EMPTY_LISTS)
    doex.add_argument('-sdump', '--dump-screenshots', action=ACTION_STORE_TRUE, help=HELP_ARG_DUMP_SCREENSHOTS)
    dofi = par.add_argument_group(title='filtering options')
    dofi.add_argument(dest='extra_tags', nargs=ZERO_OR_MORE, action=ACTION_EXTEND, help=HELP_ARG_EXTRA_TAGS)
    dofi.add_argument('-duration', metavar='#min-max', default=valid_duration(''), help=HELP_ARG_DURATION, type=valid_duration)
    dofi.add_argument('-minrating', '--minimum-rating', metavar='#rating', default=0, help=HELP_ARG_MINRATING, type=valid_rating)
    dofi.add_argument('-minscore', '--minimum-score', metavar='#score', default=None, help=HELP_ARG_MINSCORE, type=valid_int)
    dofi.add_argument('-utp', '--untagged-policy', default=UTP_DEFAULT, help=HELP_ARG_UTPOLICY, choices=UNTAGGED_POLICIES)
    dofi.add_argument('--solve-tag-conflicts', action=ACTION_STORE_TRUE, help=HELP_ARG_SOLVE_TAG_CONFLICTS)
    dofi.add_argument('--report-duplicates', action=ACTION_STORE_TRUE, help=HELP_ARG_REPORT_DUPLICATES)
    dofi.add_argument('--check-uploader', action=ACTION_STORE_TRUE, help=HELP_ARG_CHECK_UPLOADER)
    dofi.add_argument('--check-title-pos', action=ACTION_STORE_TRUE, help='')
    dofi.add_argument('--check-title-neg', action=ACTION_STORE_TRUE, help='')
    dofi.add_argument('--check-description-pos', action=ACTION_STORE_TRUE, help='')
    dofi.add_argument('--check-description-neg', action=ACTION_STORE_TRUE, help=HELP_ARG_CHECK_TITLEDESC)


def add_logging_args(par: ArgumentParser) -> None:
    lo = par.add_argument_group(title='logging options')
    lo.add_argument('-log', '--log-level', default=log_level(LOGGING_DEFAULT.name.lower()), help=HELP_ARG_LOGGING, type=log_level)
    lo.add_argument('-nocolors', '--disable-log-colors', action=ACTION_STORE_TRUE, help=HELP_ARG_NOCOLORS)


def add_help(par: ArgumentParser, is_root: bool):
    mi = par.add_argument_group(title='misc')
    mi.add_argument('--help', action='help', help='Print this message')
    if is_root:
        mi.add_argument('--version', action='version', help=HELP_ARG_VERSION, version=f'{APP_NAME} {APP_VERSION}')


def parse_arglist(args: Sequence[str]) -> Namespace:
    parsers = create_parsers()

    # Root
    parser_root = parsers[PARSER_TITLE_NONE]
    parser_root.usage = (
        f'\n{INDENT}{MODULE} {PARSER_TITLE_IDS} ...'
        f'\n{INDENT}{MODULE} {PARSER_TITLE_PAGES} ...'
    )

    # Ids
    pci = parsers[PARSER_TITLE_IDS]
    pci.usage = (
        f'\n{INDENT}{MODULE} {PARSER_TITLE_IDS}'
        f' -start #number -end|-count #number [options...] [extra tags...]'
        f'\n{INDENT}{MODULE} {PARSER_TITLE_IDS}'
        f' --use-id-sequence|--use-link-sequence [options...] [extra tags...]'
    )
    pcig1 = pci.add_argument_group(title='options')
    pcigm1 = pcig1.add_mutually_exclusive_group(required=True)
    pcigm2 = pcig1.add_mutually_exclusive_group()
    pcigm1.add_argument('-start', metavar='#number', help=HELP_ARG_ID_START, type=positive_nonzero_int)
    pcigm2.add_argument('-count', metavar='#number', default=1, help=HELP_ARG_ID_COUNT, type=positive_nonzero_int)
    pcigm2.add_argument('-end', metavar='#number', default=1, help=HELP_ARG_ID_END, type=positive_nonzero_int)
    pcig1.add_argument('-lookahead', metavar='#number', default=0, help=HELP_ARG_LOOKAHEAD, type=valid_lookahead)
    pcig1.add_argument('-gpred', '--predict-id-gaps', default=IDGP_DEFAULT, help=HELP_ARG_PREDICT_ID_GAPS, choices=IDGAP_PREDICTION_MODES)
    pcigm1.add_argument('-seq', '--use-id-sequence', action=ACTION_STORE_TRUE, help=HELP_ARG_IDSEQUENCE)
    pcigm1.add_argument('-links', '--use-link-sequence', action=ACTION_STORE_TRUE, help=HELP_ARG_LINKSEQUENCE)

    # Pages
    pcp = parsers[PARSER_TITLE_PAGES]
    pcp.usage = (
        f'\n{INDENT}{MODULE} {PARSER_TITLE_PAGES}'
        f' -start #number -end|-pages #number #[options...] #[extra tags...]'
        f'\n{INDENT}{MODULE} {PARSER_TITLE_PAGES}'
        f' -get_maxid'
    )
    pcpg1 = pcp.add_argument_group(title='options')
    pcpgm1 = pcpg1.add_mutually_exclusive_group(required=True)
    pcpgm1.add_argument('-get_maxid', action=ACTION_STORE_TRUE, help=HELP_ARG_GET_MAXID)
    pcpg1.add_argument('-start', metavar='#number', default=1, help=HELP_ARG_PAGE_START, type=positive_nonzero_int)
    pcpgm1.add_argument('-pages', metavar='#number', help=HELP_ARG_PAGE_COUNT, type=positive_nonzero_int)
    pcpgm1.add_argument('-end', metavar='#number', default=1, help=HELP_ARG_PAGE_END, type=positive_nonzero_int)
    pcpg1.add_argument('-stop_id', metavar='#number', default=1, help='', type=positive_nonzero_int)
    pcpg1.add_argument('-begin_id', metavar='#number', default=10**9, help=HELP_ARG_BEGIN_STOP_ID, type=positive_nonzero_int)
    pcpg1.add_argument('-pall', '--scan-all-pages', action=ACTION_STORE_TRUE, help=HELP_ARG_ALL_PAGES)
    pcpgm2 = pcpg1.add_mutually_exclusive_group()
    pcpgm2.add_argument('-playlist_id', metavar='#number', default=(0, ''), help='', type=valid_playlist_id)
    pcpgm2.add_argument('-playlist_name', metavar='#name', default=(0, ''), help=HELP_ARG_PLAYLIST, type=valid_playlist_name)
    pcpgm2.add_argument('-favourites', metavar='#user_id', default=0, help=HELP_ARG_FAVORITES, type=positive_nonzero_int)
    pcpgm2.add_argument('-uploader', metavar='#user_id', default=0, help=HELP_ARG_UPLOADER, type=positive_nonzero_int)
    pcpgm2.add_argument('-model', metavar='#name', default='', help=HELP_ARG_MODEL)
    pcpg1.add_argument('-search', metavar='#string', default='', help=HELP_ARG_SEARCH_STR, type=valid_search_string)
    pcpg1.add_argument('-search_tag', metavar='#tag[,tag...]', default='', help='', type=valid_tags)
    pcpg1.add_argument('-search_art', metavar='#artist[,artist...]', default='', help='', type=valid_artists)
    pcpg1.add_argument('-search_cat', metavar='#category[,category...]', default='', help=HELP_ARG_SEARCH_ACT, type=valid_categories)
    pcpg1.add_argument('-search_rule_tag', default=SEARCH_RULE_DEFAULT, help='', choices=SEARCH_RULES)
    pcpg1.add_argument('-search_rule_art', default=SEARCH_RULE_DEFAULT, help='', choices=SEARCH_RULES)
    pcpg1.add_argument('-search_rule_cat', default=SEARCH_RULE_DEFAULT, help=HELP_ARG_SEARCH_RULE, choices=SEARCH_RULES)
    pcpg1.add_argument('-blacklist', metavar='#[(a|c|t):]name[,...]', default='', help=HELP_ARG_BLACKLIST, type=valid_blacklist)

    # File
    pcf = parsers[PARSER_TITLE_FILE]
    pcf.usage = (
        f'\n{INDENT}{MODULE} {PARSER_TITLE_NAMES_REMAP[PARSER_TITLE_FILE]}'
        f' -path #path_to_file'
    )
    pcfg1 = pcf.add_argument_group(title='options')
    pcfg1.add_argument('-path', metavar='#filepath', required=True, help=HELP_ARG_CMDFILE, type=valid_filepath_abs)

    [add_common_args(_) for _ in (parser_root, pci, pcp)]
    [add_logging_args(_) for _ in parsers.values()]
    [add_help(_, _ == parser_root) for _ in parsers.values()]
    return execute_parser(parser_root, args)


def prepare_arglist(args: Sequence[str]) -> None:
    parsed = parse_arglist(args)
    for pp in vars(parsed):
        param = Config.NAMESPACE_VARS_REMAP.get(pp, pp)
        parsed_value = getattr(parsed, pp)
        parser_default = getattr(parsed, PARSER_PARAM_PARSER_TYPE).get_default(pp)
        if param in vars(Config):
            cvalue = getattr(Config, param)
            if not cvalue or (parsed_value and parsed_value != parser_default):
                svalue = parsed_value if cvalue is None else (parsed_value or cvalue)
                setattr(Config, param, svalue)
        elif param not in PARSED_ARGS_NO_CONSUME:
            Log.error(f'Argument list param {param} was not consumed!')

#
#
#########################################
