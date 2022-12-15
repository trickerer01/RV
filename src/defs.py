# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from base64 import b64decode
from datetime import datetime
from typing import Optional


__RV_DEBUG__ = False


class BaseConfig(object):
    def __init__(self):
        self.verbose = False
        self.min_score = None  # type: Optional[int]
        self.naming_flags = 0
        self.validate_tags = True


ExtraConfig = BaseConfig()

# SITE = b64decode('aHR0cHM6Ly9ydWxlMzR2aWRlby5jb20v').decode()
# Params required: str, int. Ex. SITE_AJAX_REQUEST_BASE % ('sfw', 1)
SITE_AJAX_REQUEST_BASE = b64decode(
    'aHR0cHM6Ly9ydWxlMzR2aWRlby5jb20vc2VhcmNoLz9tb2RlPWFzeW5jJmZ1bmN0aW9uPWdldF9ibG9jayZibG9ja19pZD1jdXN0b21fbGlzdF92aWRlb3NfdmlkZW9zX2xpc3'
    'Rfc2VhcmNoJnE9JXMmc29ydF9ieT1wb3N0X2RhdGUmZnJvbV92aWRlb3M9JWQ=').decode()
# Params required: int. Ex. SITE_AJAX_REQUEST_VIDEO % (1071113)
SITE_AJAX_REQUEST_VIDEO = b64decode(
    'aHR0cHM6Ly9ydWxlMzR2aWRlby5jb20vcG9wdXAtdmlkZW8vJWQv').decode()

USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:68.9) Gecko/20100101 Goanna/4.8 Firefox/68.9'
DEFAULT_HEADERS = {'User-Agent': USER_AGENT}

REPLACE_SYMBOLS = r'[^\da-zA-Z.,_+%\-()\[\] ]+?'
NON_SEARCH_SYMBOLS = r'[^\da-zA-Z._+\-\[\]]'

SLASH = '/'
UTF8 = 'utf-8'

QUALITIES = ['2160p', '1080p', '720p', '480p', '360p', 'preview']

DEFAULT_QUALITY = QUALITIES[4]

# untagged videos download policy
DOWNLOAD_POLICY_NOFILTERS = 'nofilters'
DOWNLOAD_POLICY_ALWAYS = 'always'
UVIDEO_POLICIES = [DOWNLOAD_POLICY_NOFILTERS, DOWNLOAD_POLICY_ALWAYS]
DOWNLOAD_POLICY_DEFAULT = DOWNLOAD_POLICY_NOFILTERS

# download (file creation) mode
DOWNLOAD_MODE_FULL = 'full'
DOWNLOAD_MODE_TOUCH = 'touch'
DOWNLOAD_MODES = [DOWNLOAD_MODE_FULL, DOWNLOAD_MODE_TOUCH]
DOWNLOAD_MODE_DEFAULT = DOWNLOAD_MODE_FULL

NAMING_FLAG_PREFIX = 0x01
NAMING_FLAG_SCORE = 0x02
NAMING_FLAG_TITLE = 0x04
NAMING_FLAG_TAGS = 0x08
NAMING_FLAGS_FULL = NAMING_FLAG_PREFIX | NAMING_FLAG_SCORE | NAMING_FLAG_TITLE | NAMING_FLAG_TAGS
NAMING_FLAGS = {
    'prefix': f'0x{NAMING_FLAG_PREFIX:02X}',
    'score': f'0x{NAMING_FLAG_SCORE:02X}',
    'title': f'0x{NAMING_FLAG_TITLE:02X}',
    'tags': f'0x{NAMING_FLAG_TAGS:02X}',
    'full': f'0x{NAMING_FLAGS_FULL:02X}'
}
NAMING_FLAGS_DEFAULT = NAMING_FLAGS_FULL

ACTION_STORE_TRUE = 'store_true'
ACTION_STORE_FALSE = 'store_false'

HELP_PAGES = 'Pages count to process. Required'
HELP_STOP_ID = 'If you want to download only videos above or equal to this id'
HELP_BEGIN_ID = 'If you want to download only videos above or equal to this id'
HELP_PATH = 'Download destination. Default is current folder'
HELP_SEARCH = 'If you want to only traverse pages matching some search query'
HELP_QUALITY = f'Video quality. Default is \'{DEFAULT_QUALITY}\'. If not found, best quality found is used (up to 4K)'
HELP_ARG_PROXY = 'Proxy to use. Example: http://127.0.0.1:222'
HELP_ARG_UVPOLICY = (
    'Untagged videos download policy. By default these videos are ignored if you use extra \'tags\' / \'-tags\'. Use'
    f' \'{DOWNLOAD_POLICY_ALWAYS}\' to override'
)
HELP_ARG_DMMODE = 'Download (file creation) mode'
HELP_ARG_EXTRA_TAGS = (
    'All remaining \'args\' and \'-args\' count as tags to exclude / require.'
    ' Videos containing any of \'-tags\', or not containing all of \'tags\' will be skipped.'
    ' Only existing tags are allowed. Use can skip validity checks with \'--no-validation\' option'
)
HELP_ARG_DWN_SCENARIO = (
    'Download scenario. This allows to scan for tags and sort videos accordingly in a single pass.'
    ' Useful when you have several queries you need to process for same id range.'
    ' Format:'
    ' "{SUBDIR1}: tag1 tag2; {SUBDIR2}: tag3 tag4 -tag1 -tag2"'
    ' You can also use following arguments in each subquery: -quality, -minscore, -uvp.'
    ' Example:'
    ' \'python ids.py -path ... -start ... -end ... --download-scenario'
    ' "1g: 1girl -1monster -quality 480p; 2g: 2girls -1girl -1monster -quality 720p -minscore 150 -uvp always"\''
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
HELP_ARG_NO_VALIDATION = 'Skip extra tags validation. Useful when you want to filter by author or category'

CONNECT_RETRIES_PAGE = 5
CONNECT_RETRIES_ITEM = 50

MAX_VIDEOS_QUEUE_SIZE = 8

Log = print

TAGS_CONCAT_CHAR = ','
start_time = datetime.now()


def prefixp() -> str:
    return 'rv_'


def get_elapsed_time_s() -> str:
    mm, ss = divmod((datetime.now() - start_time).seconds, 60)
    hh, mm = divmod(mm, 60)
    return f'{hh:02d}:{mm:02d}:{ss:02d}'


def normalize_path(basepath: str, append_slash: bool = True) -> str:
    normalized_path = basepath.replace('\\', SLASH)
    if append_slash and len(normalized_path) != 0 and normalized_path[-1] != SLASH:
        normalized_path += SLASH
    return normalized_path


def has_naming_flag(flag: int) -> bool:
    return not not ExtraConfig.naming_flags & flag


class DownloadResult:
    DOWNLOAD_SUCCESS = 0
    DOWNLOAD_FAIL_NOT_FOUND = 1
    DOWNLOAD_FAIL_RETRIES = 2
    DOWNLOAD_FAIL_ALREADY_EXISTS = 3

#
#
#########################################
