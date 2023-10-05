# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from argparse import Namespace
from base64 import b64decode
from datetime import datetime
from enum import IntEnum
from locale import getpreferredencoding
from re import compile as re_compile
from typing import Optional, List
from urllib.parse import urlparse

from colorama import init as colorama_init, Fore

colorama_init()


class BaseConfig(object):
    """Parameters container for params used in both **pages** and **ids** modes"""
    def __init__(self) -> None:
        self.dest_base = None  # type: Optional[str]
        self.proxy = None  # type: Optional[str]
        self.session_id = None  # type: Optional[str]
        self.min_rating = None  # type: Optional[int]
        self.min_score = None  # type: Optional[int]
        self.quality = None  # type: Optional[str]
        self.un_video_policy = None  # type: Optional[str]
        self.download_mode = None  # type: Optional[str]
        self.continue_mode = None  # type: Optional[bool]
        self.keep_unfinished = None  # type: Optional[bool]
        self.save_tags = None  # type: Optional[bool]
        self.save_descriptions = None  # type: Optional[bool]
        self.save_comments = None  # type: Optional[bool]
        self.save_screenshots = None  # type: Optional[bool]
        self.extra_tags = None  # type: Optional[List[str]]
        self.scenario = None  # type: Optional['DownloadScenario'] # noqa F821
        self.naming_flags = self.logging_flags = 0
        self.start = self.end = self.start_id = self.end_id = 0
        self.get_maxid = None  # type: Optional[bool]
        # extras (can't be set through cmdline arguments)
        self.nodelay = False

    def read(self, params: Namespace, pages: bool) -> None:
        self.dest_base = params.path
        self.proxy = params.proxy
        self.session_id = params.session_id
        self.min_rating = params.minimum_rating
        self.min_score = params.minimum_score
        self.quality = params.quality
        self.un_video_policy = params.untag_video_policy
        self.download_mode = params.download_mode
        self.continue_mode = params.continue_mode
        self.keep_unfinished = params.keep_unfinished
        self.save_tags = params.dump_tags
        self.save_descriptions = params.dump_descriptions
        self.save_comments = params.dump_comments
        self.save_screenshots = params.dump_screenshots
        self.extra_tags = params.extra_tags
        self.scenario = params.download_scenario
        self.naming_flags = params.naming
        self.logging_flags = params.log_level
        self.start = params.start
        self.end = params.end
        self.start_id = params.stop_id if pages else self.start
        self.end_id = params.begin_id if pages else self.end
        self.get_maxid = getattr(params, 'get_maxid') if hasattr(params, 'get_maxid') else self.get_maxid

    @property
    def uvp(self) -> Optional[str]:
        return self.un_video_policy

    @uvp.setter
    def uvp(self, value: str) -> None:
        self.un_video_policy = value

    @property
    def dm(self) -> Optional[str]:
        return self.download_mode


Config = BaseConfig()

APP_NAME = 'RV'
APP_VERSION = '1.6.249'

SITE = b64decode('aHR0cHM6Ly9ydWxlMzR2aWRlby5wYXJ0eQ==').decode()
SITE_AJAX_REQUEST_PAGE = b64decode(
    'aHR0cHM6Ly9ydWxlMzR2aWRlby5wYXJ0eS9zZWFyY2gvP21vZGU9YXN5bmMmZnVuY3Rpb249Z2V0X2Jsb2NrJmJsb2NrX2lkPWN1c3RvbV9saXN0X3ZpZGVvc192aWRlb3NfbG'
    'lzdF9zZWFyY2gmc29ydF9ieT1wb3N0X2RhdGUmdGFnX2lkcz0lcyZtb2RlbF9pZHM9JXMmY2F0ZWdvcnlfaWRzPSVzJnE9JXMmZnJvbV92aWRlb3M9JWQ=').decode()
"""Params required: **tags**, **artists**, **categories**, **search**, **page** - **str**, **str**, **str**, **str**, **int**\n
Ex. SITE_AJAX_REQUEST_PAGE % ('1,2', '3,4,5', '6', 'sfw', 1)"""
SITE_AJAX_REQUEST_VIDEO = b64decode('aHR0cHM6Ly9ydWxlMzR2aWRlby5wYXJ0eS9wb3B1cC12aWRlby8lZC8=').decode()
"""Params required: **video_id** - **int**\n
Ex. SITE_AJAX_REQUEST_VIDEO % (1071113)"""
SITE_AJAX_REQUEST_PLAYLIST_PAGE = b64decode(
    'aHR0cHM6Ly9ydWxlMzR2aWRlby5wYXJ0eS9wbGF5bGlzdHMvJWQvJXMvP21vZGU9YXN5bmMmZnVuY3Rpb249Z2V0X2Jsb2NrJmJsb2NrX2lkPXBsYXlsaXN0X3ZpZXdfcGxheW'
    'xpc3RfdmlldyZzb3J0X2J5PWFkZGVkMmZhdl9kYXRlJmZyb209JWQ=').decode()
"""Params required: **playlist_id**, **playlist_name**, **page** - **int**, **str**, **int**\n
Ex. SITE_AJAX_REQUEST_PLAYLIST_PAGE % (999, 'stuff', 1)"""

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Goanna/6.3 Firefox/102.0 PaleMoon/32.4.0.1'
HOST = urlparse(SITE).netloc
DEFAULT_HEADERS = {'User-Agent': USER_AGENT}

# language=PythonRegExp
REPLACE_SYMBOLS = r'[^0-9a-zA-Z.,_+%\-()\[\] ]+'
# language=PythonRegExp
NON_SEARCH_SYMBOLS = r'[^\da-zA-Z._+\-\[\]]'

QUALITIES = ('2160p', '1080p', '720p', '480p', '360p', 'preview')

DEFAULT_QUALITY = QUALITIES[4]
"""'360p'"""

# untagged videos download policy
DOWNLOAD_POLICY_NOFILTERS = 'nofilters'
DOWNLOAD_POLICY_ALWAYS = 'always'
UVIDEO_POLICIES = (DOWNLOAD_POLICY_NOFILTERS, DOWNLOAD_POLICY_ALWAYS)
"""('nofilters','always')"""
DOWNLOAD_POLICY_DEFAULT = DOWNLOAD_POLICY_NOFILTERS
"""'nofilters'"""

# download (file creation) mode
DOWNLOAD_MODE_FULL = 'full'
DOWNLOAD_MODE_TOUCH = 'touch'
DOWNLOAD_MODE_SKIP = 'skip'
DOWNLOAD_MODES = (DOWNLOAD_MODE_FULL, DOWNLOAD_MODE_TOUCH, DOWNLOAD_MODE_SKIP)
"""('full','touch','skip')"""
DOWNLOAD_MODE_DEFAULT = DOWNLOAD_MODE_FULL
"""'full'"""

# search args combination logic rules
SEARCH_RULE_ALL = 'all'
SEARCH_RULE_ANY = 'any'
SEARCH_RULES = (SEARCH_RULE_ALL, SEARCH_RULE_ANY)
"""('all','any')"""
SEARCH_RULE_DEFAULT = SEARCH_RULE_ALL
"""'all'"""


class NamingFlags:
    NAMING_FLAG_NONE = 0x00
    NAMING_FLAG_PREFIX = 0x01
    NAMING_FLAG_SCORE = 0x02
    NAMING_FLAG_TITLE = 0x04
    NAMING_FLAG_TAGS = 0x08
    NAMING_FLAG_QUALITY = 0x10
    NAMING_FLAGS_ALL = NAMING_FLAG_PREFIX | NAMING_FLAG_SCORE | NAMING_FLAG_TITLE | NAMING_FLAG_TAGS | NAMING_FLAG_QUALITY
    """0x1F"""


NAMING_FLAGS = {
    'none': f'0x{NamingFlags.NAMING_FLAG_NONE:02X}',
    'prefix': f'0x{NamingFlags.NAMING_FLAG_PREFIX:02X}',
    'score': f'0x{NamingFlags.NAMING_FLAG_SCORE:02X}',
    'title': f'0x{NamingFlags.NAMING_FLAG_TITLE:02X}',
    'tags': f'0x{NamingFlags.NAMING_FLAG_TAGS:02X}',
    'quality': f'0x{NamingFlags.NAMING_FLAG_QUALITY:02X}',
    'full': f'0x{NamingFlags.NAMING_FLAGS_ALL:02X}'
}
"""
{\n\n'none': '0x00',\n\n'prefix': '0x01',\n\n'score': '0x02',\n\n'title': '0x04',\n\n'tags': '0x08',\n\n'quality': '0x10',
\n\n'full': '0x1F'\n\n}
"""
NAMING_FLAGS_DEFAULT = NamingFlags.NAMING_FLAGS_ALL
"""0x1F"""


class LoggingFlags(IntEnum):
    LOGGING_NONE = 0x000
    LOGGING_TRACE = 0x001
    LOGGING_DEBUG = 0x002
    LOGGING_INFO = 0x004
    LOGGING_WARN = 0x008
    LOGGING_ERROR = 0x010
    LOGGING_FATAL = 0x800
    # some extra logging flags are merged into normal flags for now
    LOGGING_EX_MISSING_TAGS = LOGGING_TRACE
    """0x001"""
    LOGGING_EX_EXCLUDED_TAGS = LOGGING_INFO
    """0x004"""
    LOGGING_EX_LOW_SCORE = LOGGING_INFO
    """0x004"""
    LOGGING_ALL = LOGGING_FATAL | LOGGING_ERROR | LOGGING_WARN | LOGGING_INFO | LOGGING_DEBUG | LOGGING_TRACE
    """0x81F"""

    def __str__(self) -> str:
        return f'{self._name_} (0x{self.value:03X})'


LOGGING_FLAGS = {
    'error': f'0x{LoggingFlags.LOGGING_ERROR.value:03X}',
    'warn': f'0x{LoggingFlags.LOGGING_WARN.value:03X}',
    'info': f'0x{LoggingFlags.LOGGING_INFO.value:03X}',
    'debug': f'0x{LoggingFlags.LOGGING_DEBUG.value:03X}',
    'trace': f'0x{LoggingFlags.LOGGING_TRACE.value:03X}',
}
"""{\n\n'error': '0x010',\n\n'warn': '0x008',\n\n'info': '0x004',\n\n'debug': '0x002',\n\n'trace': '0x001'\n\n}"""
LOGGING_FLAGS_DEFAULT = LoggingFlags.LOGGING_INFO
"""0x004"""

ACTION_STORE_TRUE = 'store_true'

HELP_ARG_VERSION = 'Show program\'s version number and exit'
HELP_ARG_GET_MAXID = 'Print maximum id and exit'
HELP_ARG_BEGIN_STOP_ID = 'Video id lower / upper bounds filter to only download videos where \'begin_id >= video_id >= stop_id\''
HELP_ARG_IDSEQUENCE = (
    'Use video id sequence instead of range. This disables start / count / end id parametes and expects an id sequence instead of'
    ' extra tags. Sequence structure: (id=<id1>~id=<id2>~id=<id3>~...~id=<idN>)'
)
HELP_ARG_PATH = 'Download destination. Default is current folder'
HELP_ARG_SESSION_ID = (
    '\'PHPSESSID\' cookie. Comments as well as some tags to search for are hidden behind login wall.'
    ' Using this cookie from logged in account resolves that problem'
)
HELP_ARG_SEARCH_RULE = (
    f'Multiple search args of the same type combine logic. Default is \'{SEARCH_RULE_DEFAULT}\'.'
    f' Example: while searching for tags \'sfw,side_view\','
    f' \'{SEARCH_RULE_ANY}\' will search for any of those tags, \'{SEARCH_RULE_ALL}\' will only return results matching both'
)
HELP_ARG_SEARCH_ACT = (
    'Native search by tag(s) / artist(s) / category(ies). Spaces must be replced with \'_\', concatenate with \',\'.'
    ' Example: \'-search_tag 1girl,side_view -search_art artist_name -search_cat category_name\''
)
HELP_ARG_PLAYLIST = 'Playlist to download (filters still apply)'
HELP_ARG_SEARCH_STR = 'Native search using string query (matching any word). Spaces must be replced with \'-\'. Ex. \'after-hours\''
HELP_ARG_QUALITY = f'Video quality. Default is \'{DEFAULT_QUALITY}\'. If not found, best quality found is used (up to 4K)'
HELP_ARG_PROXY = 'Proxy to use. Example: http://127.0.0.1:222'
HELP_ARG_UVPOLICY = (
    f'Untagged videos download policy. By default these videos are ignored if you use extra \'tags\' / \'-tags\'. Use'
    f' \'{DOWNLOAD_POLICY_ALWAYS}\' to override'
)
HELP_ARG_DMMODE = 'Download (file creation) mode'
HELP_ARG_EXTRA_TAGS = (
    'All remaining \'args\' and \'-args\' count as tags to require or exclude. All spaces must be replaced with \'_\'.'
    ' Videos containing any of \'-tags\', or not containing all \'tags\' will be skipped.'
    ' Supports wildcards, \'or\' groups and \'negative\' groups (check README for more info).'
    ' Only existing tags are allowed unless wildcards are used'
)
HELP_ARG_DWN_SCENARIO = (
    'Download scenario. This allows to scan for tags and sort videos accordingly in a single pass.'
    ' Useful when you have several queries you need to process for same id range.'
    ' Format:'
    ' "{SUBDIR1}: tag1 tag2; {SUBDIR2}: tag3 tag4".'
    ' You can also use following arguments in each subquery: -quality, -minscore, -minrating, -uvp, -seq.'
    ' Example:'
    ' \'python ids.py -path ... -start ... -end ... --download-scenario'
    ' "1g: 1girl -quality 480p; 2g: 2girls -quality 720p -minscore 150 -uvp always"\''
)
HELP_ARG_MINRATING = (
    '[DEPRECATED, DO NOT USE] Rating percentage filter for videos, 0-100.'
    ' Videos having rating below this value will be skipped, unless rating extraction fails - in that case video always gets a pass'
)
HELP_ARG_MINSCORE = (
    'Score filter for videos (likes minus dislikes).'
    ' Videos having score below this value will be skipped, unless score extraction fails - in that case video always gets a pass'
)
HELP_ARG_CMDFILE = (
    'Full path to file containing cmdline arguments. Useful when cmdline length exceeds maximum for your OS.'
    ' Windows: ~32000, MinGW: ~4000 to ~32000, Linux: ~127000+. Check README for more info'
)
HELP_ARG_NAMING = (
    f'File naming flags: {str(NAMING_FLAGS).replace(" ", "").replace(":", "=")}.'
    f' You can combine them via names \'prefix|score|title\', otherwise it has to be an int or a hex number.'
    f' Default is \'full\''
)
HELP_ARG_LOGGING = (
    f'Logging level: {{{str(list(LOGGING_FLAGS.keys())).replace(" ", "")[1:-1]}}}.'
    f' All messages equal or above this level will be logged. Default is \'info\''
)
HELP_ARG_DUMP_INFO = 'Save tags / descriptions / comments to text file (separately)'
HELP_ARG_CONTINUE = 'Try to continue unfinished files, may be slower if most files already exist'
HELP_ARG_UNFINISH = 'Do not clean up unfinished files on interrupt'

CONNECT_RETRIES_PAGE = 50
CONNECT_RETRIES_ITEM = 50
CONNECT_REQUEST_DELAY = 1.0

MAX_DEST_SCAN_SUB_DEPTH = 1
MAX_VIDEOS_QUEUE_SIZE = 8
DOWNLOAD_STATUS_CHECK_TIMER = 120.0

SCREENSHOTS_COUNT = 10

SLASH = '/'
UTF8 = 'utf-8'
TAGS_CONCAT_CHAR = ','
EXTENSIONS_V = ('mp4', 'webm')
START_TIME = datetime.now()

re_media_filename = re_compile(fr'^(?:rv_)?(\d+).*?(?:_({"|".join(QUALITIES)}))?(?:_py(?:dw|pv))?\.(?:{"|".join(EXTENSIONS_V)})$')
re_replace_symbols = re_compile(REPLACE_SYMBOLS)
re_ext = re_compile(r'(\.[^&]{3,5})&')
# re_private_video = re_compile(r'^This is a private video\..*?$')


class Log:
    """
    Basic logger supporting different log levels, colors and extra logging flags\n
    **Static**
    """
    COLORS = {
        LoggingFlags.LOGGING_TRACE: Fore.WHITE,
        LoggingFlags.LOGGING_DEBUG: Fore.LIGHTWHITE_EX,
        LoggingFlags.LOGGING_INFO: Fore.LIGHTCYAN_EX,
        LoggingFlags.LOGGING_WARN: Fore.LIGHTYELLOW_EX,
        LoggingFlags.LOGGING_ERROR: Fore.LIGHTYELLOW_EX,
        LoggingFlags.LOGGING_FATAL: Fore.LIGHTRED_EX
    }

    @staticmethod
    def log(text: str, flags: LoggingFlags) -> None:
        # if flags & LoggingFlags.LOGGING_FATAL == 0 and Config.logging_flags & flags != flags:
        if flags < Config.logging_flags:
            return

        for f in reversed(Log.COLORS.keys()):
            if f & flags:
                text = f'{Log.COLORS[f]}{text}{Fore.RESET}'
                break

        try:
            print(text)
        except UnicodeError:
            try:
                print(text.encode(UTF8).decode())
            except Exception:
                try:
                    print(text.encode(UTF8).decode(getpreferredencoding()))
                except Exception:
                    print('<Message was not logged due to UnicodeError>')
            finally:
                print('Previous message caused UnicodeError...')

    @staticmethod
    def fatal(text: str) -> None:
        return Log.log(text, LoggingFlags.LOGGING_FATAL)

    @staticmethod
    def error(text: str, extra_flags=LoggingFlags.LOGGING_NONE) -> None:
        return Log.log(text, LoggingFlags.LOGGING_ERROR | extra_flags)

    @staticmethod
    def warn(text: str, extra_flags=LoggingFlags.LOGGING_NONE) -> None:
        return Log.log(text, LoggingFlags.LOGGING_WARN | extra_flags)

    @staticmethod
    def info(text: str, extra_flags=LoggingFlags.LOGGING_NONE) -> None:
        return Log.log(text, LoggingFlags.LOGGING_INFO | extra_flags)

    @staticmethod
    def debug(text: str, extra_flags=LoggingFlags.LOGGING_NONE) -> None:
        return Log.log(text, LoggingFlags.LOGGING_DEBUG | extra_flags)

    @staticmethod
    def trace(text: str, extra_flags=LoggingFlags.LOGGING_NONE) -> None:
        return Log.log(text, LoggingFlags.LOGGING_TRACE | extra_flags)


def prefixp() -> str:
    return 'rv_'


def get_elapsed_time_i() -> int:
    """Returns time since launch in **seconds**"""
    return (datetime.now() - START_TIME).seconds


def get_elapsed_time_s() -> str:
    """Returns time since launch in format: **hh:mm:ss**"""
    mm, ss = divmod((datetime.now() - START_TIME).seconds, 60)
    hh, mm = divmod(mm, 60)
    return f'{hh:02d}:{mm:02d}:{ss:02d}'


def unquote(string: str) -> str:
    """Removes all leading/trailing single/double quotes. Non-matching quotes are removed too"""
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
    try:
        return re_ext.search(href).group(1)
    except Exception:
        return '.mp4'


def has_naming_flag(flag: int) -> bool:
    return not not (Config.naming_flags & flag)


def calc_sleep_time(base_time: float) -> float:
    """Returns either base_time for full download or shortened time otherwise"""
    return base_time if Config.download_mode == DOWNLOAD_MODE_FULL else max(1.0, base_time / 3.0)


class DownloadResult(IntEnum):
    DOWNLOAD_SUCCESS = 0
    DOWNLOAD_FAIL_NOT_FOUND = 1
    DOWNLOAD_FAIL_RETRIES = 2
    DOWNLOAD_FAIL_ALREADY_EXISTS = 3
    DOWNLOAD_FAIL_SKIPPED = 4

    def __str__(self) -> str:
        return f'{self._name_} (0x{self.value:d})'


class HelpPrintExitException(Exception):
    pass

#
#
#########################################
