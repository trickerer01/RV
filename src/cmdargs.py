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

from config import Config
from defs import (
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
from logger import Log
from scenario import DownloadScenario
from tagger import valid_artists, valid_blacklist, valid_categories, valid_extra_tag, valid_playlist_id, valid_playlist_name, valid_tags
from validators import (
    log_level,
    naming_flags,
    positive_int,
    positive_nonzero_int,
    valid_duration,
    valid_filepath_abs,
    valid_int,
    valid_lookahead,
    valid_path,
    valid_proxy,
    valid_rating,
    valid_search_string,
    valid_session_id,
    valid_timeout,
)
from version import APP_NAME, APP_VERSION

__all__ = ('HelpPrintExitException', 'prepare_arglist')

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

PARSER_TYPE_PARAM = 'zzzparser_type'
PARSER_TITLE_FILE = 'file'
PARSER_TITLE_CMD = 'cmd'
EXISTING_PARSERS = {PARSER_TITLE_CMD, PARSER_TITLE_FILE}
"""'file','cmd'"""

IDGP_DEFAULT = IDGAP_PREDICTION_DEFAULT
"""'0'"""


class HelpPrintExitException(Exception):
    pass


def read_cmdfile(cmdfile_path: str) -> list[str]:
    """Read cmd args from a text file"""
    with open(cmdfile_path, 'rt', encoding=UTF8) as cmdfile:
        args = []
        for line in cmdfile.readlines():
            line = line.strip(' \n\ufeff')
            if line:
                args.append(line)
        return args


def is_parsed_file(parsed_result: Namespace) -> bool:
    return getattr(parsed_result, PARSER_TYPE_PARAM) == PARSER_TITLE_FILE


def is_parsed_cmdfile(parsed_result: Namespace) -> bool:
    return is_parsed_file(parsed_result)


def validate_parsed(parser: ArgumentParser, args: Sequence[str], default_sub: ArgumentParser) -> Namespace:
    errors_to_print: list[str] = []
    parsed, unks = parser.parse_known_args(args) if args[0] in EXISTING_PARSERS else default_sub.parse_known_args(args)
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


def execute_parser(parser: ArgumentParser, default_sub: ArgumentParser, args: Sequence[str], pages: bool) -> Namespace:
    try:
        assert args
        parsed = validate_parsed(parser, args, default_sub)
        if not is_parsed_cmdfile(parsed):
            if pages:
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
            parsed = prepare_arglist_type(read_cmdfile(parsed.path), pages)
        return parsed
    except SystemExit:
        raise HelpPrintExitException
    except Exception:
        from traceback import format_exc
        default_sub.print_help()
        Log.fatal(format_exc())
        raise HelpPrintExitException


def create_parsers() -> tuple[ArgumentParser, ArgumentParser, ArgumentParser]:
    parser = ArgumentParser(add_help=False)
    subs = parser.add_subparsers()
    par_file = subs.add_parser(PARSER_TITLE_FILE, description='Run using text file containing cmdline', add_help=False)
    par_cmd = subs.add_parser(PARSER_TITLE_CMD, description='Run using normal cmdline', add_help=False)
    [p.add_argument('--help', action='help', help='Print this message') for p in (par_file, par_cmd)]
    [p.add_argument('--version', action='version', help=HELP_ARG_VERSION, version=f'{APP_NAME} {APP_VERSION}') for p in (par_file, par_cmd)]
    [p.set_defaults(**{PARSER_TYPE_PARAM: t}) for p, t in zip((par_file, par_cmd), (PARSER_TITLE_FILE, PARSER_TITLE_CMD), strict=True)]
    return parser, par_file, par_cmd


def add_common_args(parser_or_group: ArgumentParser) -> None:
    parser_or_group.add_argument('-path', default=valid_path(os.path.abspath(os.path.curdir)), help=HELP_ARG_PATH, type=valid_path)
    parser_or_group.add_argument('-quality', default=DEFAULT_QUALITY, help=HELP_ARG_QUALITY, choices=QUALITIES)
    parser_or_group.add_argument('-duration', metavar='#min-max', default=valid_duration(''), help=HELP_ARG_DURATION, type=valid_duration)
    parser_or_group.add_argument('-minrating', '--minimum-rating', metavar='#rating', default=0, help=HELP_ARG_MINRATING, type=valid_rating)
    parser_or_group.add_argument('-minscore', '--minimum-score', metavar='#score', default=None, help=HELP_ARG_MINSCORE, type=valid_int)
    parser_or_group.add_argument('-utp', '--untagged-policy', default=UTP_DEFAULT, help=HELP_ARG_UTPOLICY, choices=UNTAGGED_POLICIES)
    parser_or_group.add_argument('-fsdepth', metavar='#number', default=FSDEPTH_DEFAULT, help=HELP_ARG_FSDEPTH, type=positive_int)
    parser_or_group.add_argument('-fslevelup', metavar='#number', default=FSUP_DEFAULT, help=HELP_ARG_FSLEVELUP, type=positive_nonzero_int)
    parser_or_group.add_argument('-proxy', metavar='#type://[u:p@]a.d.d.r:port', default=None, help=HELP_ARG_PROXY, type=valid_proxy)
    parser_or_group.add_argument('-proxynodown', '--download-without-proxy', action=ACTION_STORE_TRUE, help=HELP_ARG_PROXYNODOWN)
    parser_or_group.add_argument('-proxynohtml', '--html-without-proxy', action=ACTION_STORE_TRUE, help=HELP_ARG_PROXYNOHTML)
    parser_or_group.add_argument('-timeout', metavar='#seconds', default=valid_timeout(''), help=HELP_ARG_TIMEOUT, type=valid_timeout)
    parser_or_group.add_argument('-retries', metavar='#number', default=CONNECT_RETRIES_BASE, help=HELP_ARG_RETRIES, type=positive_int)
    parser_or_group.add_argument('-throttle', metavar='#rate', default=0, help=HELP_ARG_THROTTLE, type=positive_nonzero_int)
    parser_or_group.add_argument('-athrottle', '--throttle-auto', action=ACTION_STORE_TRUE, help=HELP_ARG_THROTTLE_AUTO)
    parser_or_group.add_argument('-continue', '--continue-mode', action=ACTION_STORE_TRUE, help=HELP_ARG_CONTINUE)
    parser_or_group.add_argument('-unfinish', '--keep-unfinished', action=ACTION_STORE_TRUE, help=HELP_ARG_UNFINISH)
    parser_or_group.add_argument('-nomove', '--no-rename-move', action=ACTION_STORE_TRUE, help=HELP_ARG_NOMOVE)
    parser_or_group.add_argument('-naming', default=NAMING_DEFAULT, help=HELP_ARG_NAMING, type=naming_flags)
    parser_or_group.add_argument('-log', '--log-level', default=LOGGING_DEFAULT, help=HELP_ARG_LOGGING, type=log_level)
    parser_or_group.add_argument('-nocolors', '--disable-log-colors', action=ACTION_STORE_TRUE, help=HELP_ARG_NOCOLORS)
    parser_or_group.add_argument('-tdump', '--dump-tags', action=ACTION_STORE_TRUE, help='')
    parser_or_group.add_argument('-ddump', '--dump-descriptions', action=ACTION_STORE_TRUE, help='')
    parser_or_group.add_argument('-cdump', '--dump-comments', action=ACTION_STORE_TRUE, help=HELP_ARG_DUMP_INFO)
    parser_or_group.add_argument('-dmerge', '--merge-lists', action=ACTION_STORE_TRUE, help=HELP_ARG_MERGE_LISTS)
    parser_or_group.add_argument('-dnoempty', '--skip-empty-lists', action=ACTION_STORE_TRUE, help=HELP_ARG_SKIP_EMPTY_LISTS)
    parser_or_group.add_argument('-sdump', '--dump-screenshots', action=ACTION_STORE_TRUE, help=HELP_ARG_DUMP_SCREENSHOTS)
    parser_or_group.add_argument('-dmode', '--download-mode', default=DM_DEFAULT, help=HELP_ARG_DMMODE, choices=DOWNLOAD_MODES)
    parser_or_group.add_argument('-session_id', default=None, help=HELP_ARG_SESSION_ID, type=valid_session_id)
    parser_or_group.add_argument('-script', '--download-scenario', default=None, help=HELP_ARG_DWN_SCENARIO, type=DownloadScenario)
    parser_or_group.add_argument('--store-continue-cmdfile', action=ACTION_STORE_TRUE, help=HELP_ARG_STORE_CONTINUE_CMDFILE)
    parser_or_group.add_argument('--solve-tag-conflicts', action=ACTION_STORE_TRUE, help=HELP_ARG_SOLVE_TAG_CONFLICTS)
    parser_or_group.add_argument('--report-duplicates', action=ACTION_STORE_TRUE, help=HELP_ARG_REPORT_DUPLICATES)
    parser_or_group.add_argument('--check-uploader', action=ACTION_STORE_TRUE, help=HELP_ARG_CHECK_UPLOADER)
    parser_or_group.add_argument('--check-title-pos', action=ACTION_STORE_TRUE, help='')
    parser_or_group.add_argument('--check-title-neg', action=ACTION_STORE_TRUE, help='')
    parser_or_group.add_argument('--check-description-pos', action=ACTION_STORE_TRUE, help='')
    parser_or_group.add_argument('--check-description-neg', action=ACTION_STORE_TRUE, help=HELP_ARG_CHECK_TITLEDESC)
    parser_or_group.add_argument(dest='extra_tags', nargs=ZERO_OR_MORE, help=HELP_ARG_EXTRA_TAGS)


def prepare_arglist_ids(args: Sequence[str]) -> Namespace:
    parser, par_file, par_cmd = create_parsers()
    par_cmd.usage = (
        '\n       ids.py [cmd] -start #number -end|-count #number [options...] [extra tags...]'
        '\n       ids.py [cmd] --use-id-sequence|--use-link-sequence [options...] [extra tags...]'
        '\n       ids.py file -path #path_to_file'
    )

    par_file.add_argument('-path', metavar='#filepath', required=True, help=HELP_ARG_CMDFILE, type=valid_filepath_abs)
    arggr_start_or_seq = par_cmd.add_mutually_exclusive_group(required=True)
    arggr_count_or_end = par_cmd.add_mutually_exclusive_group()
    arggr_start_or_seq.add_argument('-start', metavar='#number', help=HELP_ARG_ID_START, type=positive_nonzero_int)
    arggr_count_or_end.add_argument('-count', metavar='#number', default=1, help=HELP_ARG_ID_COUNT, type=positive_nonzero_int)
    arggr_count_or_end.add_argument('-end', metavar='#number', default=1, help=HELP_ARG_ID_END, type=positive_nonzero_int)
    par_cmd.add_argument('-lookahead', metavar='#number', default=0, help=HELP_ARG_LOOKAHEAD, type=valid_lookahead)
    par_cmd.add_argument('-gpred', '--predict-id-gaps', default=IDGP_DEFAULT, help=HELP_ARG_PREDICT_ID_GAPS, choices=IDGAP_PREDICTION_MODES)
    arggr_start_or_seq.add_argument('-seq', '--use-id-sequence', action=ACTION_STORE_TRUE, help=HELP_ARG_IDSEQUENCE)
    arggr_start_or_seq.add_argument('-links', '--use-link-sequence', action=ACTION_STORE_TRUE, help=HELP_ARG_LINKSEQUENCE)

    add_common_args(par_cmd)
    return execute_parser(parser, par_cmd, args, False)


def prepare_arglist_pages(args: Sequence[str]) -> Namespace:
    parser, par_file, par_cmd = create_parsers()
    par_cmd.usage = (
        '\n       pages.py [cmd] -start #number -end|-pages #number [options...] [extra tags...]'
        '\n       pages.py [cmd] -get_maxid'
        '\n       pages.py file -path #path_to_file'
    )

    par_file.add_argument('-path', metavar='#filepath', required=True, help=HELP_ARG_CMDFILE, type=valid_filepath_abs)
    par_cmd.add_argument('-start', metavar='#number', default=1, help=HELP_ARG_PAGE_START, type=positive_nonzero_int)
    arggr_count_or_end = par_cmd.add_mutually_exclusive_group(required=True)
    arggr_count_or_end.add_argument('-get_maxid', action=ACTION_STORE_TRUE, help=HELP_ARG_GET_MAXID)
    arggr_count_or_end.add_argument('-pages', metavar='#number', help=HELP_ARG_PAGE_COUNT, type=positive_nonzero_int)
    arggr_count_or_end.add_argument('-end', metavar='#number', default=1, help=HELP_ARG_PAGE_END, type=positive_nonzero_int)
    par_cmd.add_argument('-stop_id', metavar='#number', default=1, help='', type=positive_nonzero_int)
    par_cmd.add_argument('-begin_id', metavar='#number', default=10**9, help=HELP_ARG_BEGIN_STOP_ID, type=positive_nonzero_int)
    par_cmd.add_argument('-pall', '--scan-all-pages', action=ACTION_STORE_TRUE, help=HELP_ARG_ALL_PAGES)
    arggr_pl_upl = par_cmd.add_mutually_exclusive_group()
    arggr_pl_upl.add_argument('-playlist_id', metavar='#number', default=(0, ''), help='', type=valid_playlist_id)
    arggr_pl_upl.add_argument('-playlist_name', metavar='#name', default=(0, ''), help=HELP_ARG_PLAYLIST, type=valid_playlist_name)
    arggr_pl_upl.add_argument('-favourites', metavar='#user_id', default=0, help=HELP_ARG_FAVORITES, type=positive_nonzero_int)
    arggr_pl_upl.add_argument('-uploader', metavar='#user_id', default=0, help=HELP_ARG_UPLOADER, type=positive_nonzero_int)
    arggr_pl_upl.add_argument('-model', metavar='#name', default='', help=HELP_ARG_MODEL)
    par_cmd.add_argument('-search', metavar='#string', default='', help=HELP_ARG_SEARCH_STR, type=valid_search_string)
    par_cmd.add_argument('-search_tag', metavar='#tag[,tag...]', default='', help='', type=valid_tags)
    par_cmd.add_argument('-search_art', metavar='#artist[,artist...]', default='', help='', type=valid_artists)
    par_cmd.add_argument('-search_cat', metavar='#category[,category...]', default='', help=HELP_ARG_SEARCH_ACT, type=valid_categories)
    par_cmd.add_argument('-search_rule_tag', default=SEARCH_RULE_DEFAULT, help='', choices=SEARCH_RULES)
    par_cmd.add_argument('-search_rule_art', default=SEARCH_RULE_DEFAULT, help='', choices=SEARCH_RULES)
    par_cmd.add_argument('-search_rule_cat', default=SEARCH_RULE_DEFAULT, help=HELP_ARG_SEARCH_RULE, choices=SEARCH_RULES)
    par_cmd.add_argument('-blacklist', metavar='#[(a|c|t):]name[,...]', default='', help=HELP_ARG_BLACKLIST, type=valid_blacklist)

    add_common_args(par_cmd)
    return execute_parser(parser, par_cmd, args, True)


def prepare_arglist_type(args: Sequence[str], pages: bool) -> Namespace:
    parsed = prepare_arglist_pages(args) if pages else prepare_arglist_ids(args)
    return parsed


def prepare_arglist(args: Sequence[str], pages: bool) -> None:
    parsed = prepare_arglist_type(args, pages)
    for pp in vars(parsed):
        param = Config.NAMESPACE_VARS_REMAP.get(pp, pp)
        if param in vars(Config):
            setattr(Config, param, getattr(parsed, pp, getattr(Config, param)))
        else:
            Log.debug(f'Argument list param {param} was not consumed...')

#
#
#########################################
