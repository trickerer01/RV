# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations

from argparse import Namespace
from base64 import b64decode
from datetime import datetime
from enum import IntEnum
from locale import getpreferredencoding
from re import compile as re_compile
from typing import Optional, List, Union
from urllib.parse import urlparse

from colorama import init as colorama_init, Fore

colorama_init()


class BaseConfig(object):
    """Parameters container for params used in both **pages** and **ids** modes"""
    def __init__(self) -> None:
        self.dest_base = None  # type: Optional[str]
        self.proxy = None  # type: Optional[str]
        self.min_rating = None  # type: Optional[int]
        self.min_score = None  # type: Optional[int]
        self.quality = None  # type: Optional[str]
        self.un_video_policy = None  # type: Optional[str]
        self.download_mode = None  # type: Optional[str]
        self.save_tags = None  # type: Optional[bool]
        self.extra_tags = None  # type: Optional[List[str]]
        self.scenario = None  # type: Optional['DownloadScenario'] # noqa F821
        self.naming_flags = 0
        self.logging_flags = 0

    def read_params(self, params: Namespace) -> None:
        self.dest_base = params.path
        self.proxy = params.proxy
        self.min_rating = params.minimum_rating
        self.min_score = params.minimum_score
        self.quality = params.quality
        self.un_video_policy = params.untag_video_policy
        self.download_mode = params.download_mode
        self.save_tags = params.dump_tags
        self.extra_tags = params.extra_tags
        self.scenario = params.download_scenario
        self.naming_flags = params.naming
        self.logging_flags = params.log_level

    @property
    def uvp(self) -> Optional[str]:
        return self.un_video_policy

    @uvp.setter
    def uvp(self, value: str) -> None:
        self.un_video_policy = value

    @property
    def dm(self) -> Optional[str]:
        return self.download_mode


ExtraConfig = BaseConfig()

SITE = b64decode('aHR0cHM6Ly9ydWxlMzR2aWRlby5wYXJ0eS8=').decode()
SITE_AJAX_REQUEST_PAGE = b64decode(
    'aHR0cHM6Ly9ydWxlMzR2aWRlby5wYXJ0eS9zZWFyY2gvP21vZGU9YXN5bmMmZnVuY3Rpb249Z2V0X2Jsb2NrJmJsb2NrX2lkPWN1c3RvbV9saXN0X3ZpZGVvc192aWRlb3NfbG'
    'lzdF9zZWFyY2gmc29ydF9ieT1wb3N0X2RhdGUmdGFnX2lkcz0lcyZtb2RlbF9pZHM9JXMmY2F0ZWdvcnlfaWRzPSVzJnE9JXMmZnJvbV92aWRlb3M9JWQ=').decode()
"""Params required: **tags**, **artists**, **categories**, **search**, **page** - **str**, **str**, **str**, **str**, **int**.\n
Ex. SITE_AJAX_REQUEST_PAGE % ('1,2', '3,4,5', '6', 'sfw', 1)"""
SITE_AJAX_REQUEST_VIDEO = b64decode('aHR0cHM6Ly9ydWxlMzR2aWRlby5wYXJ0eS9wb3B1cC12aWRlby8lZC8=').decode()
"""Params required: int. Ex. SITE_AJAX_REQUEST_VIDEO % (1071113)"""

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Goanna/6.2 Firefox/102.0 PaleMoon/32.2.0'
HOST = urlparse(SITE).netloc
DEFAULT_HEADERS = {'User-Agent': USER_AGENT}

# language=PythonRegExp
REPLACE_SYMBOLS = r'[^0-9a-zA-Z.,_+%\-()\[\] ]+'
# language=PythonRegExp
NON_SEARCH_SYMBOLS = r'[^\da-zA-Z._+\-\[\]]'

QUALITIES = ('2160p', '1080p', '720p', '480p', '360p', 'preview')

DEFAULT_QUALITY = QUALITIES[4]
"""360p"""

# untagged videos download policy
DOWNLOAD_POLICY_NOFILTERS = 'nofilters'
DOWNLOAD_POLICY_ALWAYS = 'always'
UVIDEO_POLICIES = (DOWNLOAD_POLICY_NOFILTERS, DOWNLOAD_POLICY_ALWAYS)
"""['nofilters','always']"""
DOWNLOAD_POLICY_DEFAULT = DOWNLOAD_POLICY_NOFILTERS
"""'nofilters'"""

# download (file creation) mode
DOWNLOAD_MODE_FULL = 'full'
DOWNLOAD_MODE_TOUCH = 'touch'
DOWNLOAD_MODES = (DOWNLOAD_MODE_FULL, DOWNLOAD_MODE_TOUCH)
"""['full','touch']"""
DOWNLOAD_MODE_DEFAULT = DOWNLOAD_MODE_FULL
"""'full'"""

# search args combination logic rules
SEARCH_RULE_ALL = 'all'
SEARCH_RULE_ANY = 'any'
SEARCH_RULES = (SEARCH_RULE_ALL, SEARCH_RULE_ANY)
"""['all','any']"""
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
\n\n'full': '0x1F',\n\n}
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
LOGGING_FLAGS_DEFAULT = LoggingFlags.LOGGING_INFO
"""0x004"""

ACTION_STORE_TRUE = 'store_true'
ACTION_STORE_FALSE = 'store_false'

HELP_PAGES = 'Pages count to process. Required'
HELP_STOP_ID = 'If you want to download only videos above or equal to this id'
HELP_BEGIN_ID = 'If you want to download only videos below or equal to this id'
HELP_ARG_IDSEQUENCE = (
    'Use video id sequence instead of range. This disables start / count / end id parametes and expects an id sequesnce instead of'
    ' extra tags. Sequence structure: (id=<id1>~id=<id2>~id=<id3>~...~id=<idN>)'
)
HELP_PATH = 'Download destination. Default is current folder'
HELP_SEARCH_RULE = (
    f'Multiple search args of the same type combine logic: {str(SEARCH_RULES)}. Default is \'{SEARCH_RULE_DEFAULT}\'.'
    f' Example: while searching for tags \'sfw,side_view\','
    f' \'{SEARCH_RULE_ANY}\' will search for any of those tags, \'{SEARCH_RULE_ALL}\' will only return results matching both'
)
HELP_SEARCH_ACT = (
    'Native search by tag(s) / artist(s) / category(ies). Spaces must be replced with \'_\', concatenate with \',\'.'
    ' Example: \'-search_tag 1girl,side_view -search_art artist_name -search_cat category_name\''
)
HELP_SEARCH_STR = 'Native search using string query (matching any word). Spaces must be replced with \'-\'. Ex. \'after-hours\''
HELP_QUALITY = f'Video quality. Default is \'{DEFAULT_QUALITY}\'. If not found, best quality found is used (up to 4K)'
HELP_ARG_PROXY = 'Proxy to use. Example: http://127.0.0.1:222'
HELP_ARG_UVPOLICY = (
    'Untagged videos download policy. By default these videos are ignored if you use extra \'tags\' / \'-tags\'. Use'
    f' \'{DOWNLOAD_POLICY_ALWAYS}\' to override'
)
HELP_ARG_DMMODE = 'Download (file creation) mode'
HELP_ARG_EXTRA_TAGS = (
    'All remaining \'args\' and \'-args\' count as tags to require or exclude. All spaces must be replaced with \'_\'.'
    ' Videos containing any of \'-tags\', or not containing all of \'tags\' will be skipped.'
    ' Supports wildcards, \'or\' groups and \'negative\' groups (check README for more info).'
    ' Only existing tags are allowed unless wildcards are used'
)
HELP_ARG_DWN_SCENARIO = (
    'Download scenario. This allows to scan for tags and sort videos accordingly in a single pass.'
    ' Useful when you have several queries you need to process for same id range.'
    ' Format:'
    ' "{SUBDIR1}: tag1 tag2; {SUBDIR2}: tag3 tag4 -tag1 -tag2".'
    ' You can also use following arguments in each subquery: -quality, -minscore, -uvp, -seq.'
    ' Example:'
    ' \'python ids.py -path ... -start ... -end ... --download-scenario'
    ' "1g: 1girl -1monster -quality 480p; 2g: 2girls -1girl -1monster -quality 720p -minscore 150 -uvp always"\''
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
    'Full path to file containing cmdline arguments. One word per line. Useful when cmdline length exceeds maximum for your OS.'
    ' Windows: ~32000, MinGW: ~4000 to ~32000, Linux: ~127000+'
)
HELP_ARG_NAMING = (
    f'File naming flags: {str(NAMING_FLAGS)}.'
    f' You can combine them via names \'prefix|score|title\', otherwise it has to be an int or a hex number.'
    f' Default is \'full\''
)
HELP_ARG_LOGGING = (
    f'Logging level: {str(list(LOGGING_FLAGS.keys()))}. All messages equal or above this level will be logged. Default is \'info\''
)

CONNECT_RETRIES_PAGE = 50
CONNECT_RETRIES_ITEM = 50
CONNECT_REQUEST_DELAY = 1.0

MAX_DEST_SCAN_SUB_DEPTH = 1
MAX_VIDEOS_QUEUE_SIZE = 8
DOWNLOAD_STATUS_CHECK_TIMER = 120.0

SLASH = '/'
UTF8 = 'utf-8'
TAGS_CONCAT_CHAR = ','
START_TIME = datetime.now()

re_media_filename = re_compile(fr'^(?:rv_)?(\d+).*?(?:_({"|".join(QUALITIES)}))?(?:_py(?:dw|pv))?\..{{3,4}}$')
re_replace_symbols = re_compile(REPLACE_SYMBOLS)
re_ext = re_compile(r'(\.[^&]{3,5})&')
# re_private_video = re_compile(r'^This is a private video\..*?$')


class Log:
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
        # if flags & LoggingFlags.LOGGING_FATAL == 0 and ExtraConfig.logging_flags & flags != flags:
        if flags < ExtraConfig.logging_flags:
            return

        for f in reversed(Log.COLORS.keys()):
            if f & flags:
                text = f'{Log.COLORS[f]}{text}{Fore.RESET}'
                break

        try:
            print(text)
        except UnicodeError:
            # print(f'message was: {bytearray(map(ord, text))}')
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
    return not not (ExtraConfig.naming_flags & flag)


def calc_sleep_time(base_time: float) -> float:
    """Returns either base_time for full download or shortened time otherwise"""
    return base_time if ExtraConfig.download_mode == DOWNLOAD_MODE_FULL else max(1.0, base_time / 3.0)


class DownloadResult(IntEnum):
    DOWNLOAD_SUCCESS = 0
    DOWNLOAD_FAIL_NOT_FOUND = 1
    DOWNLOAD_FAIL_RETRIES = 2
    DOWNLOAD_FAIL_ALREADY_EXISTS = 3
    DOWNLOAD_FAIL_SKIPPED = 4

    def __str__(self) -> str:
        return f'{self._name_} ({self.value:03X})'


class HelpPrintExitException(Exception):
    pass


class VideoInfo:
    class VIState(IntEnum):
        NONE = 0
        QUEUED = 1
        ACTIVE = 2
        DOWNLOADING = 3
        WRITING = 4
        DONE = 5
        FAILED = 6

    def __init__(self, m_id: int, m_title='', m_link='', m_subfolder='', m_filename='', m_rating='') -> None:
        self.my_id = m_id or 0
        self.my_title = m_title or ''
        self.my_link = m_link or ''
        self.my_subfolder = m_subfolder or ''
        self.my_filename = m_filename or ''
        self.my_rating = m_rating or ''

        self.my_quality = ExtraConfig.quality or DEFAULT_QUALITY
        self._state = VideoInfo.VIState.NONE

    def set_state(self, state: VideoInfo.VIState) -> None:
        self._state = state

    def __eq__(self, other: Union[VideoInfo, int]) -> bool:
        return self.my_id == other.my_id if isinstance(other, type(self)) else self.my_id == other if isinstance(other, int) else False

    def __repr__(self) -> str:
        return (
            f'[{self.state_str}] \'{prefixp()}{self.my_id}_{self.my_title}.mp4\' ({self.my_quality})'
            f'\nDest: \'{self.my_fullpath}\'\nLink: \'{self.my_link}\''
        )

    @property
    def my_folder(self) -> str:
        return normalize_path(f'{ExtraConfig.dest_base}{self.my_subfolder}')

    @property
    def my_fullpath(self) -> str:
        return normalize_filename(self.my_filename, self.my_folder)

    @property
    def state_str(self) -> str:
        return self._state.name

#
#
#########################################
