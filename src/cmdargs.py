# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import ArgumentParser, Namespace, ArgumentError, ZERO_OR_MORE
from os import path
from re import sub as re_sub
from typing import Optional, List

from defs import (
    Log, HELP_PATH, HELP_PAGES, HELP_STOP_ID, HELP_SEARCH_STR, QUALITIES, DEFAULT_QUALITY, HELP_QUALITY, HELP_ARG_PROXY, HELP_BEGIN_ID,
    HELP_ARG_EXTRA_TAGS, HELP_ARG_UVPOLICY, UVIDEO_POLICIES, DOWNLOAD_POLICY_DEFAULT, DOWNLOAD_MODES, DOWNLOAD_MODE_DEFAULT,
    NAMING_FLAGS_DEFAULT, LOGGING_FLAGS_DEFAULT, HELP_ARG_DMMODE, HELP_ARG_DWN_SCENARIO, HELP_ARG_MINSCORE, HELP_ARG_CMDFILE,
    HELP_ARG_NAMING, HELP_ARG_LOGGING, HELP_ARG_IDSEQUENCE, ACTION_STORE_TRUE, UTF8, HelpPrintExitException,
    HELP_SEARCH_TAGS, HELP_SEARCH_ARTISTS, HELP_SEARCH_CATEGORIES, HELP_SEARCH_RULE, SEARCH_RULES, SEARCH_RULE_DEFAULT,
)
from scenario import DownloadScenario
from tagger import valid_extra_tag, valid_tags, valid_artists, valid_categories
from validators import (
    valid_int, valid_positive_nonzero_int, valid_path, valid_filepath_abs, valid_search_string, valid_proxy, naming_flags, log_level,
)

__all__ = ('prepare_arglist_pages', 'prepare_arglist_ids', 'read_cmdfile', 'is_parsed_cmdfile')

UVP_DEFAULT = DOWNLOAD_POLICY_DEFAULT
"""'nofilters'"""
DM_DEFAULT = DOWNLOAD_MODE_DEFAULT
"""'full'"""
NAMING_DEFAULT = NAMING_FLAGS_DEFAULT
"""0x0F"""
LOGGING_DEFAULT = LOGGING_FLAGS_DEFAULT
"""0x004"""

PARSER_TITLE_FILE = 'file'
PARSER_TITLE_CMD = 'cmd'
EXISTING_PARSERS = {PARSER_TITLE_CMD, PARSER_TITLE_FILE}

parser = None  # type: Optional[ArgumentParser]


def read_cmdfile(cmdfile_path: str) -> List[str]:
    """
    Read cmd args from a text file
    """
    with open(cmdfile_path, 'rt', encoding=UTF8) as cmdfile:
        args = []  # type: List[str]
        for line in cmdfile.readlines():
            rline = re_sub(r'^ *(.+)$', r'\1', line.strip(' \n\ufeff'))
            if rline != '':
                args.append(rline)
        return args


def is_parsed_cmdfile(parse_result: Namespace) -> bool:
    """Determines if parsed cmdline points to a text file"""
    return hasattr(parse_result, 'path') and not hasattr(parse_result, 'extra_tags')


def validate_parsed(args: List[str], default_sub: ArgumentParser) -> Namespace:
    global parser

    error_to_print = ''
    try:
        parsed, unks = (
            parser.parse_known_args(args) if args[0] in EXISTING_PARSERS else default_sub.parse_known_args(args))
        if not is_parsed_cmdfile(parsed):
            for tag in unks:
                try:
                    assert valid_extra_tag(tag)
                except Exception:
                    error_to_print = f'\nInvalid extra tag: \'{tag}\'\n'
                    raise
            parsed.extra_tags += [tag.lower().replace(' ', '_') for tag in unks]
    except (ArgumentError, TypeError, Exception):
        # print('\n', e)
        parser.print_help()
        if error_to_print != '':
            Log.error(error_to_print)
        raise

    return parsed


def add_common_args(parser_or_group: ArgumentParser) -> None:
    parser_or_group.add_argument('-path', default=path.abspath(path.curdir), help=HELP_PATH, type=valid_path)
    parser_or_group.add_argument('-quality', default=DEFAULT_QUALITY, help=HELP_QUALITY, choices=QUALITIES)
    parser_or_group.add_argument('-naming', metavar='#MASK', default=NAMING_DEFAULT, help=HELP_ARG_NAMING, type=naming_flags)
    parser_or_group.add_argument('-log', '--log-level', default=LOGGING_DEFAULT, help=HELP_ARG_LOGGING, type=log_level)
    parser_or_group.add_argument('-minscore', '--minimum-score', metavar='#score', default=-999999, help=HELP_ARG_MINSCORE, type=valid_int)
    parser_or_group.add_argument('-proxy', metavar='#type://a.d.d.r:port', default=None, help=HELP_ARG_PROXY, type=valid_proxy)
    parser_or_group.add_argument('-uvp', '--untag-video-policy', default=UVP_DEFAULT, help=HELP_ARG_UVPOLICY, choices=UVIDEO_POLICIES)
    parser_or_group.add_argument('-dmode', '--download-mode', default=DM_DEFAULT, help=HELP_ARG_DMMODE, choices=DOWNLOAD_MODES)
    parser_or_group.add_argument('-tdump', '--dump-tags', action=ACTION_STORE_TRUE, help='Save tags to text file')
    parser_or_group.add_argument('-script', '--download-scenario', default=None, help=HELP_ARG_DWN_SCENARIO, type=DownloadScenario)
    parser_or_group.add_argument(dest='extra_tags', nargs=ZERO_OR_MORE, help=HELP_ARG_EXTRA_TAGS, type=valid_extra_tag)


def prepare_arglist_ids(args: List[str]) -> Namespace:
    global parser

    parser = ArgumentParser(add_help=False)

    subs = parser.add_subparsers()
    par_file = subs.add_parser(PARSER_TITLE_FILE, description='Run using text file containing cmdline', add_help=False)
    par_cmd = subs.add_parser(PARSER_TITLE_CMD, description='Run using normal cmdline', add_help=False)

    par_file.add_argument('-path', metavar='#filepath', required=True, help=HELP_ARG_CMDFILE, type=valid_filepath_abs)
    arggr_start_or_seq = par_cmd.add_mutually_exclusive_group(required=True)
    arggr_start_or_seq.add_argument('-seq', '--use-id-sequence', action=ACTION_STORE_TRUE, help=HELP_ARG_IDSEQUENCE)
    arggr_start_or_seq.add_argument('-start', metavar='#number', help='Start video id. Required', type=valid_positive_nonzero_int)
    arggr_ids = par_cmd.add_mutually_exclusive_group()
    arggr_ids.add_argument('-count', metavar='#number', default=1, help='Ids count to process', type=valid_positive_nonzero_int)
    arggr_ids.add_argument('-end', metavar='#number', default=1, help='End video id', type=valid_positive_nonzero_int)

    add_common_args(par_cmd)

    [p.add_argument('--help', action='help', help='Print this message') for p in [par_file, par_cmd]]

    def finalize_ex_groups(parsed: Namespace) -> Namespace:
        if parsed.use_id_sequence:
            parsed.start = parsed.end = None
        elif parsed.end < parsed.start + parsed.count - 1:
            parsed.end = parsed.start + parsed.count - 1
        parsed.count = None
        return parsed

    try:
        pparsed = validate_parsed(args, par_cmd)
        if not is_parsed_cmdfile(pparsed):
            pparsed = finalize_ex_groups(pparsed)
        return pparsed
    except SystemExit:
        raise HelpPrintExitException
    except (ArgumentError, TypeError, Exception):
        raise


def prepare_arglist_pages(args: List[str]) -> Namespace:
    global parser

    parser = ArgumentParser(add_help=False)

    subs = parser.add_subparsers()
    par_file = subs.add_parser(PARSER_TITLE_FILE, description='Run using text file containing cmdline', add_help=False)
    par_cmd = subs.add_parser(PARSER_TITLE_CMD, description='Run using normal cmdline', add_help=False)

    par_file.add_argument('-path', metavar='#filepath', required=True, help=HELP_ARG_CMDFILE, type=valid_filepath_abs)
    par_cmd.add_argument('-start', metavar='#number', default=1, help="Start page number. Default is '1'", type=valid_positive_nonzero_int)
    par_cmd.add_argument('-pages', metavar='#number', required=True, help=HELP_PAGES, type=valid_positive_nonzero_int)
    par_cmd.add_argument('-stop_id', metavar='#number', default=1, help=HELP_STOP_ID, type=valid_positive_nonzero_int)
    par_cmd.add_argument('-begin_id', metavar='#number', default=1000000000, help=HELP_BEGIN_ID, type=valid_positive_nonzero_int)
    par_cmd.add_argument('-search', metavar='#string', default='', help=HELP_SEARCH_STR, type=valid_search_string)
    par_cmd.add_argument('-search_tag', metavar='#tags...', default='', help=HELP_SEARCH_TAGS, type=valid_tags)
    par_cmd.add_argument('-search_art', metavar='#artists...', default='', help=HELP_SEARCH_ARTISTS, type=valid_artists)
    par_cmd.add_argument('-search_cat', metavar='#catergories...', default='', help=HELP_SEARCH_CATEGORIES, type=valid_categories)
    par_cmd.add_argument('-search_rule_tag', default=SEARCH_RULE_DEFAULT, help=HELP_SEARCH_RULE, choices=SEARCH_RULES)
    par_cmd.add_argument('-search_rule_art', default=SEARCH_RULE_DEFAULT, help=HELP_SEARCH_RULE, choices=SEARCH_RULES)
    par_cmd.add_argument('-search_rule_cat', default=SEARCH_RULE_DEFAULT, help=HELP_SEARCH_RULE, choices=SEARCH_RULES)
    par_cmd.epilog = 'Note that search obeys \'AND\' rule: \'(ANY/ALL tag(s)) AND (ANY/ALL artist(s)) AND (ANY/ALL category(ies))\''

    add_common_args(par_cmd)

    [p.add_argument('--help', action='help', help='Print this message') for p in [par_file, par_cmd]]

    try:
        pparsed = validate_parsed(args, par_cmd)
        return pparsed
    except SystemExit:
        raise HelpPrintExitException
    except (ArgumentError, TypeError, Exception):
        raise

#
#
#########################################
