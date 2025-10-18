# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import base64
import datetime
import os
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import TypeVar

MIN_PYTHON_VERSION = (3, 10)
MIN_PYTHON_VERSION_STR = f'{MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}'

CONNECT_RETRIES_BASE = 50
CONNECT_TIMEOUT_BASE = 10
CONNECT_REQUEST_DELAY = 0.7
CONNECT_RETRY_DELAY = (4.0, 8.0)

MAX_DEST_SCAN_SUB_DEPTH_DEFAULT = 1
MAX_DEST_SCAN_UPLEVELS_DEFAULT = 0
MAX_VIDEOS_QUEUE_SIZE = 8
MAX_SCAN_QUEUE_SIZE = 1
DOWNLOAD_STATUS_CHECK_TIMER = 60
DOWNLOAD_QUEUE_STALL_CHECK_TIMER = 30
DOWNLOAD_CONTINUE_FILE_CHECK_TIMER = 30
SCAN_CANCEL_KEYSTROKE = 'q'
SCAN_CANCEL_KEYCOUNT = 2
LOOKAHEAD_WATCH_RESCAN_DELAY_MIN = 300
LOOKAHEAD_WATCH_RESCAN_DELAY_MAX = 1800
RESCAN_DELAY_EMPTY = 1

SCREENSHOTS_COUNT = 10
FULLPATH_MAX_BASE_LEN = 240

PREFIX = 'rv_'
SLASH = '/'
UTF8 = 'utf-8'
TAGS_CONCAT_CHAR = ','
DEFAULT_EXT = 'mp4'
EXTENSIONS_V = (DEFAULT_EXT, 'webm')
HTTPS_PREFIX = 'https://'
START_TIME = datetime.datetime.now()

SITE = base64.b64decode('aHR0cHM6Ly9ydWxlMzR2aWRlby5jb20=').decode()
SITE_AJAX_REQUEST_SEARCH_PAGE = base64.b64decode(
    'aHR0cHM6Ly9ydWxlMzR2aWRlby5jb20vc2VhcmNoLz9tb2RlPWFzeW5jJmZ1bmN0aW9uPWdldF9ibG9jayZibG9ja19pZD1jdXN0b21fbGlzdF92aWRlb3NfdmlkZW9zX2xpc3'
    'Rfc2VhcmNoJnNvcnRfYnk9cG9zdF9kYXRlJnRhZ19pZHM9JXMmbW9kZWxfaWRzPSVzJmNhdGVnb3J5X2lkcz0lcyZxPSVzJnRlbXBfc2tpcF9pdGVtcz0lcyZmcm9tX3ZpZGVv'
    'cz0lZA==').decode()
'''Params required: **tags**, **artists**, **categories**, **search**, **blacklist**, **page** -
**str**, **str**, **str**, **str**, **str**, **int**\n
Ex. SITE_AJAX_REQUEST_SEARCH_PAGE % ('1,2', '3,4,5', '6', 'sfw', 'tag:1,tag:2,cat:3,model:4', 1)'''
SITE_AJAX_REQUEST_VIDEO = base64.b64decode('aHR0cHM6Ly9ydWxlMzR2aWRlby5jb20vcG9wdXAtdmlkZW8vJWQv').decode()
'''Params required: **video_id** - **int**\n
Ex. SITE_AJAX_REQUEST_VIDEO % (1071113)'''
SITE_AJAX_REQUEST_PLAYLIST_PAGE = base64.b64decode(
    'aHR0cHM6Ly9ydWxlMzR2aWRlby5jb20vcGxheWxpc3RzLyVkLyVzLz9tb2RlPWFzeW5jJmZ1bmN0aW9uPWdldF9ibG9jayZibG9ja19pZD1wbGF5bGlzdF92aWV3X3BsYXlsaX'
    'N0X3ZpZXcmc29ydF9ieT1hZGRlZDJmYXZfZGF0ZSZmcm9tPSVk').decode()
'''Params required: **playlist_id**, **playlist_name**, **page** - **int**, **str**, **int**\n
Ex. SITE_AJAX_REQUEST_PLAYLIST_PAGE % (999, 'stuff', 1)'''
SITE_AJAX_REQUEST_FAVOURITES_PAGE = base64.b64decode(
    'aHR0cHM6Ly9ydWxlMzR2aWRlby5jb20vbWVtYmVycy8lZC9mYXZvdXJpdGVzL3ZpZGVvcy8/bW9kZT1hc3luYyZmdW5jdGlvbj1nZXRfYmxvY2smYmxvY2tfaWQ9bGlzdF92aW'
    'Rlb3NfZmF2b3VyaXRlX3ZpZGVvcyZzb3J0X2J5PSZmcm9tX2Zhdl92aWRlb3M9JWQ=').decode()
'''Params required: **user_id**, **page** - **int**, **int**\n
Ex. SITE_AJAX_REQUEST_FAVOURITES_PAGE % (2083334, 1)'''
SITE_AJAX_REQUEST_UPLOADER_PAGE = base64.b64decode(
    'aHR0cHM6Ly9ydWxlMzR2aWRlby5jb20vbWVtYmVycy8lZC92aWRlb3MvP21vZGU9YXN5bmMmZnVuY3Rpb249Z2V0X2Jsb2NrJmJsb2NrX2lkPWxpc3RfdmlkZW9zX3VwbG9hZG'
    'VkX3ZpZGVvcyZzb3J0X2J5PSZmcm9tX3ZpZGVvcz0lZA==').decode()
'''Params required: **user_id**, **page** - **int**, **int**\n
Ex. SITE_AJAX_REQUEST_UPLOADER_PAGE % (158018, 1)'''
SITE_AJAX_REQUEST_MODEL_PAGE = base64.b64decode(
    'aHR0cHM6Ly9ydWxlMzR2aWRlby5jb20vbW9kZWxzLyVzLz9tb2RlPWFzeW5jJmZ1bmN0aW9uPWdldF9ibG9jayZibG9ja19pZD1jdXN0b21fbGlzdF92aWRlb3NfY29tbW9uX3'
    'ZpZGVvcyZzb3J0X2J5PSZmcm9tPSVk').decode()
'''Params required: **artist_name**, **page** - **str**, **int**\n
Ex. SITE_AJAX_REQUEST_MODEL_PAGE % ('gray', 1)'''

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Goanna/6.7 Firefox/102.0 PaleMoon/33.3.1'
DEFAULT_HEADERS = {'User-Agent': USER_AGENT}

# untagged videos download policy
DOWNLOAD_POLICY_NOFILTERS = 'nofilters'
DOWNLOAD_POLICY_ALWAYS = 'always'
UNTAGGED_POLICIES = (DOWNLOAD_POLICY_NOFILTERS, DOWNLOAD_POLICY_ALWAYS)
'''('nofilters','always')'''
DOWNLOAD_POLICY_DEFAULT = DOWNLOAD_POLICY_NOFILTERS
"""'nofilters'"""

# download (file creation) mode
DOWNLOAD_MODE_FULL = 'full'
DOWNLOAD_MODE_TOUCH = 'touch'
DOWNLOAD_MODE_SKIP = 'skip'
DOWNLOAD_MODES = (DOWNLOAD_MODE_FULL, DOWNLOAD_MODE_TOUCH, DOWNLOAD_MODE_SKIP)
'''('full','touch','skip')'''
DOWNLOAD_MODE_DEFAULT = DOWNLOAD_MODE_FULL
"""'full'"""

# search args combination logic rules
SEARCH_RULE_ALL = 'all'
SEARCH_RULE_ANY = 'any'
SEARCH_RULES = (SEARCH_RULE_ALL, SEARCH_RULE_ANY)
'''('all','any')'''
SEARCH_RULE_DEFAULT = SEARCH_RULE_ALL
"""'all'"""


class Quality(str):
    def __lt__(self, other: str) -> bool:
        return QUALITIES.index(self) > QUALITIES.index(other)

    def __gt__(self, other: str) -> bool:
        return QUALITIES.index(self) < QUALITIES.index(other)

    def __le__(self, other: str) -> bool:
        return QUALITIES.index(self) >= QUALITIES.index(other)

    def __ge__(self, other: str) -> bool:
        return QUALITIES.index(self) <= QUALITIES.index(other)


QUALITY_2160P = Quality('2160p')
QUALITY_1080P = Quality('1080p')
QUALITY_720P = Quality('720p')
QUALITY_480P = Quality('480p')
QUALITY_360P = Quality('360p')
QUALITY_PREVIEW = Quality('preview')

QUALITIES = (QUALITY_2160P, QUALITY_1080P, QUALITY_720P, QUALITY_480P, QUALITY_360P, QUALITY_PREVIEW)
# QUALITY_STARTS = ('h264/', 'h264/', 'hd/', 'h264/', 'h264/', 'h264/', 'iphone/')
# QUALITY_ENDS = ('_1080p', '_720p', '', '_480p', '_360p', '_SD', '')

DEFAULT_QUALITY = QUALITY_360P


class NamingFlags:
    NONE = 0x00
    PREFIX = 0x01
    SCORE = 0x02
    TITLE = 0x04
    TAGS = 0x08
    QUALITY = 0x10
    # extra
    USE_URL_TITLE = 0x20
    ALL_DEFAULT = PREFIX | SCORE | TITLE | TAGS | QUALITY
    '''0x1F'''
    ALL_EXTRA = USE_URL_TITLE
    '''0x20'''
    ALL = ALL_DEFAULT | ALL_EXTRA
    '''0x3F'''


NAMING_FLAGS = {
    'none': f'0x{NamingFlags.NONE:02X}',
    'prefix': f'0x{NamingFlags.PREFIX:02X}',
    'score': f'0x{NamingFlags.SCORE:02X}',
    'title': f'0x{NamingFlags.TITLE:02X}',
    'tags': f'0x{NamingFlags.TAGS:02X}',
    'quality': f'0x{NamingFlags.QUALITY:02X}',
    'full': f'0x{NamingFlags.ALL_DEFAULT:02X}',
    'urltitle': f'0x{NamingFlags.USE_URL_TITLE:02X}',
}
'''
{\n\n'none': '0x00',\n\n'prefix': '0x01',\n\n'score': '0x02',\n\n'title': '0x04',\n\n'tags': '0x08',\n\n'quality': '0x10',
\n\n'full': '0x1F'\n\n'urltitle': '0x20'\n\n}
'''
NAMING_FLAGS_DEFAULT = NamingFlags.ALL_DEFAULT
'''0x1F'''


class LoggingFlags(IntEnum):
    NONE = 0x000
    TRACE = 0x001
    DEBUG = 0x002
    INFO = 0x004
    WARN = 0x008
    ERROR = 0x010
    FATAL = 0x800
    # unused
    ALL = FATAL | ERROR | WARN | INFO | DEBUG | TRACE
    '''0x81F'''

    def __str__(self) -> str:
        return f'{self.name} (0x{self.value:03X})'


LOGGING_FLAGS = {
    'error': f'0x{LoggingFlags.ERROR.value:03X}',
    'warn': f'0x{LoggingFlags.WARN.value:03X}',
    'info': f'0x{LoggingFlags.INFO.value:03X}',
    'debug': f'0x{LoggingFlags.DEBUG.value:03X}',
    'trace': f'0x{LoggingFlags.TRACE.value:03X}',
}
'''{\n\n'error': '0x010',\n\n'warn': '0x008',\n\n'info': '0x004',\n\n'debug': '0x002',\n\n'trace': '0x001'\n\n}'''
LOGGING_FLAGS_DEFAULT = LoggingFlags.INFO
'''0x004'''

ACTION_STORE_TRUE = 'store_true'

SRC_PATH = os.path.abspath(os.path.dirname(__file__)).replace('\\', SLASH)
FILE_LOC_TAGS = f'{SRC_PATH}/../2tags/rv_tags.json'
FILE_LOC_CATS = f'{SRC_PATH}/../3categories/rv_cats.json'
FILE_LOC_ARTS = f'{SRC_PATH}/../4artists/rv_arts.json'
FILE_LOC_PLAS = f'{SRC_PATH}/../5playlists/rv_playlists.json'
FILE_LOC_TAG_ALIASES = f'{SRC_PATH}/../2tags/tag_aliases.json'
FILE_LOC_TAG_CONFLICTS = f'{SRC_PATH}/../2tags/tag_conflicts.json'

HELP_ARG_VERSION = 'Show program\'s version number and exit'
HELP_ARG_GET_MAXID = 'Print maximum id and exit'
HELP_ARG_ID_END = 'End video id'
HELP_ARG_ID_COUNT = 'Ids count to process'
HELP_ARG_ID_START = 'Start video id. Required'
HELP_ARG_PAGE_END = 'End page number'
HELP_ARG_PAGE_COUNT = 'Pages count to process'
HELP_ARG_PAGE_START = 'Start page number. Default is \'1\''
HELP_ARG_BEGIN_STOP_ID = 'Video id lower / upper bounds filter to only download videos where \'begin_id >= video_id >= stop_id\''
HELP_ARG_LOOKAHEAD = (
    f'-200..-1, 1..200. Continue scanning indefinitely after reaching end id until number of non-existing videos encountered in a row'
    f' reaches this number.'
    f' Furthermore, negative value enables watcher mode, periodically re-scanning trailing non-existing videos, this process never finishes'
    f' on its own but can be interrupted safely by pressing \'{SCAN_CANCEL_KEYSTROKE}\' twice'
)
HELP_ARG_PREDICT_ID_GAPS = (
    'Enable ids known to be non-existent prediction. When video is uploaded to the website post id usually gets incremented more than once.'
    ' This options allows to skip gaps within id ranges known to contain them, this may cut scan time by up to -75%%.\n'
    ' Automatically disables itself if encounters a contradicting post validity sequence.'
    ' WARNING: unsafe - may skip valid posts (not trying to request post info), use at your own risk'
)
HELP_ARG_IDSEQUENCE = (
    'Use video id sequence instead of id range. This disables start / count / end id parametes and expects an id sequence among extra tags.'
    ' Sequence structure: (id=<id1>~id=<id2>~id=<id3>~...~id=<idN>)'
)
HELP_ARG_LINKSEQUENCE = (
    'Use links instead of id range. This disables start / count / end id parametes and expects at least one link among extra tags'
)
HELP_ARG_PATH = 'Download destination. Default is current folder'
HELP_ARG_FSDEPTH = (
    f'Number of subfolder levels to walk from base destination folder scanning for existing downloads.'
    f' Default is \'{MAX_DEST_SCAN_SUB_DEPTH_DEFAULT:d}\''
)
HELP_ARG_FSLEVELUP = (
    'Folder levels to go up before scanning for existing files, increases scan depth. Destination folder is always checked'
)
HELP_ARG_SESSION_ID = (
    '\'PHPSESSID\' cookie. Some tags are hidden and cannot be searched for without logging in.'
    ' Using this cookie from logged in account resolves that problem (tag/artist/category blacklists still apply)'
)
HELP_ARG_SEARCH_RULE = (
    f'Multiple search args of the same type combine logic. Default is \'{SEARCH_RULE_DEFAULT}\'.'
    f' Example: while searching for tags \'sfw,side_view\','
    f' \'{SEARCH_RULE_ANY}\' will search for any of those tags, \'{SEARCH_RULE_ALL}\' will only return results matching both'
)
HELP_ARG_SEARCH_ACT = (
    'Native search by tag(s) / artist(s) / category(ies). Spaces must be replced with \'_\', concatenate using \',\'.'
    ' Example: \'-search_tag 1girl,side_view -search_art artist_name -search_cat category_name\'.'
    ' Note that search obeys \'AND\' rule: search string AND ANY_OF/ALL the tags AND ANY_OF/ALL the artists AND ANY_OF/ALL the categories'
)
HELP_ARG_PLAYLIST = 'Playlist to download (filters still apply)'
HELP_ARG_SEARCH_STR = (
    'Native search using string query (matching all words with alias expansion, check README for more info).'
    ' Spaces must be replced with \'-\'. Ex. \'after-hours\''
)
HELP_ARG_BLACKLIST = (
    'Native search temporary blacklist filter. Separate values by comma, all values must be valid tag, category or artist names.'
    ' Prefix indicates filter type: [a]rtist, [c]ategory or [t]ag. Unprefixed values match all types (if more than one exists).'
    ' Supports wildcards.'
    ' Example: \'-blacklist c:2d,a:wiz220,t:1boy*\' will exclude all results having either category \'2d\', artist \'wiz220\''
    ' or a tag starting with \'1boy\''
)
HELP_ARG_QUALITY = f'Video quality. Default is \'{DEFAULT_QUALITY}\'. If not found, best quality found is used (up to 4K)'
HELP_ARG_DURATION = 'Video duration filter (in seconds). Example: \'5-180\' will only allow videos from 5 seconds to 3 minutes'
HELP_ARG_PROXY = 'Proxy to use, supports basic auth. Example: http://user:pass@127.0.0.1:222'
HELP_ARG_PROXYNODOWN = 'Don\'t use proxy to connect to file servers if they differ from the main host'
HELP_ARG_UTPOLICY = (
    f'Untagged videos download policy. By default these videos are ignored if you use extra \'tags\' / \'-tags\'. Use'
    f' \'{DOWNLOAD_POLICY_ALWAYS}\' to override'
)
HELP_ARG_DMMODE = '[Debug] Download (file creation) mode'
HELP_ARG_ALL_PAGES = 'Do not interrupt pages scan if encountered a page having all post ids filtered out'
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
    ' You can also use following arguments in each subquery: -quality, -duration, -minscore, -minrating, -utp, -seq.'
    ' Example:'
    ' \'python ids.py -path ... -start ... -end ... --download-scenario'
    ' "1g: 1girl -quality 480p; 2g: 2girls -quality 720p -minscore 150 -utp always"\''
)
HELP_ARG_STORE_CONTINUE_CMDFILE = (
    'Store and automatically update cmd file which allows to later continue with unfinished download queue'
    ' (using ids module, file mode, check README for more info)'
)
HELP_ARG_SOLVE_TAG_CONFLICTS = (
    'Detect and remove simple tags that are contradictory to one or more other - more descriptive - tags (if no similar tags were found).'
    ' Mainly to prevent posts being accidently filtered out by extra \'tags\' / \'-tags\'.'
    ' Example: a post tagged with \'solo\' tag, \'1boy1girl\' or \'2girls\' and neither \'solo_male\' nor \'solo_female\''
    ' will have its \'solo\' tag removed as it is less descriptive and probably a mistake'
)
HELP_ARG_REPORT_DUPLICATES = (
    f'Report duplicate downloaded posts (regardless of quality) after initial destination folder scan.'
    f' Simplified - only names starting with \'{PREFIX}\''
)
HELP_ARG_CHECK_UPLOADER = (
    'Apply extra \'tag\' / \'-tag\' filters to uploader name.'
    ' By default only tags, categories and artists are checked by extra tags'
    ' and uploader can only be checked using its own syntax: positive \'u:{name}\' or negative \'-u:{name}\''
)
HELP_ARG_CHECK_TITLEDESC = (
    'Apply extra \'tag\' / \'-tag\' filters to title / description.'
    ' All exta \'tag\'s will be converted to wildcard tags and will have underscores replaced with spaces during this match.'
    ' Post is considered matching extra tags if either its tags or its title / description matches all extra \'tag\'s (positive filtering)'
    ' and neither its tags nor its title / description matches extra \'-tags\' (negative filtering)'
)
HELP_ARG_MINRATING = (
    'Rating percentage filter, 0-100.'
    ' Videos having rating below this value will be skipped, unless rating extraction fails - in that case video always gets a pass'
)
HELP_ARG_MINSCORE = (
    'Score filter (likes minus dislikes).'
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
HELP_ARG_NOCOLORS = 'Disable logging level dependent colors in log'
HELP_ARG_DUMP_SCREENSHOTS = 'Save timeline screenshots (webp, very slow, ignores download mode)'
HELP_ARG_DUMP_INFO = 'Save tags / descriptions / comments to text file (separately)'
HELP_ARG_SKIP_EMPTY_LISTS = 'Do not store tags / descriptions / comments list if it contains no useful data'
HELP_ARG_MERGE_LISTS = 'Merge exising tags / descriptions / comments list(s) with saved info (only if saving is enabled)'
HELP_ARG_CONTINUE = 'Try to continue unfinished files, may be slower if most files already exist'
HELP_ARG_UNFINISH = 'Do not clean up unfinished files on interrupt'
HELP_ARG_NOMOVE = 'In continue mode instead of moving already existing file to destination folder download to its original location'
HELP_ARG_TIMEOUT = f'Connection timeout (in seconds). Default is \'{CONNECT_TIMEOUT_BASE:d}\''
HELP_ARG_RETRIES = f'Connection retries count. Default is \'{CONNECT_RETRIES_BASE:d}\''
HELP_ARG_THROTTLE = 'Download speed threshold (in KB/s) to assume throttling, drop connection and retry'
HELP_ARG_THROTTLE_AUTO = 'Enable automatic throttle threshold adjustment when crossed too many times in a row'
HELP_ARG_FAVORITES = 'User id (integer, filters still apply)'
HELP_ARG_UPLOADER = 'Uploader user id (integer, filters still apply)'
HELP_ARG_MODEL = 'Artist name (scan artist\'s page(s) instead of using search, filters still apply)'
# HELP_ARG_ALLOW_DUPLICATE_NAMES = (
#     'Disable search results deduplication (by name).'
#     ' By default exact matches will be dropped except the latest one (highest album id)'
# )


class DownloadResult(IntEnum):
    SUCCESS = 0
    FAIL_NOT_FOUND = 1
    FAIL_RETRIES = 2
    FAIL_ALREADY_EXISTS = 3
    FAIL_SKIPPED = 4
    FAIL_DELETED = 5
    FAIL_FILTERED_OUTER = 6
    FAIL_EMPTY_HTML = 7

    def __str__(self) -> str:
        return f'{self.name} (0x{self.value:02X})'


class Mem:
    KB = 1024
    MB = KB * 1024
    GB = MB * 1024


class Pair(ABC):
    PT = TypeVar('PT')

    @abstractmethod
    def __init__(self, vals: tuple[PT, PT]) -> None:
        self._first, self._second = vals
        self._fmt = {int: 'd', bool: 'd', float: '.2f'}.get(type(self._first), '')

    @property
    def first(self) -> PT:
        return self._first

    @property
    def second(self) -> PT:
        return self._second

    def __bool__(self) -> bool:
        return bool(self._first) or bool(self._second)

    def __eq__(self, other) -> bool:
        return (self._first, self._second) == ((other.first, other.second) if isinstance(other, Duration) else other)

    def __str__(self) -> str:
        return f'first: {self._first:{self._fmt}}, second: {self._second:{self._fmt}}'

    __repr__ = __str__


class IntPair(Pair):
    def __init__(self, vals: tuple[int, int]) -> None:
        super().__init__(vals)


class StrPair(Pair):
    def __init__(self, vals: tuple[str, str]) -> None:
        super().__init__(vals)


class Duration(IntPair):
    def __str__(self) -> str:
        return f'{self._first:{self._fmt}}-{self._second:{self._fmt}}'

#
#
#########################################
