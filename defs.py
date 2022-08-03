# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from base64 import b64decode


__RV_DEBUG__ = False


# SITE = b64decode('aHR0cHM6Ly9ydWxlMzR2aWRlby5jb20v').decode()
# Params required: str, int. Ex. SITE_AJAX_REQUEST_BASE % ('sfw', 1)
SITE_AJAX_REQUEST_BASE = b64decode(
    'aHR0cHM6Ly9ydWxlMzR2aWRlby5jb20vc2VhcmNoLz9tb2RlPWFzeW5jJmZ1bmN0aW9uPWdldF9ibG9jayZibG9ja19pZD1jdXN0b21fbGlzdF92aWRlb3NfdmlkZW9zX2xpc3'
    'Rfc2VhcmNoJnE9JXMmc29ydF9ieT1wb3N0X2RhdGUmZnJvbV92aWRlb3M9JWQ=').decode()

USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:68.9) Gecko/20100101 Goanna/4.8 Firefox/68.9'
DEFAULT_HEADERS = {'User-Agent': USER_AGENT}

REPLACE_SYMBOLS = r'[^\da-zA-Z._\-\[\] ]'
NON_SEARCH_SYMBOLS = r'[^\da-zA-Z._\-\[\]]'
SLASH_CHAR = '/'

QUALITIES = ['1080p', '720p', '480p', '360p']

ACTION_STORE_TRUE = 'store_true'
ACTION_STORE_FALSE = 'store_false'

# pages
HELP_MODE = 'Video size and quality. You can download just previews, full videos with highest quality, or ' \
            'full videos with lowest quality (360p typically). Default is \'best\''
HELP_PAGES = 'Pages count to process. Required'
HELP_STOP_ID = 'If you want to download only videos above or equal to this id'
HELP_BEGIN_ID = 'If you want to download only videos above or equal to this id'
HELP_PATH = 'Download destination. Default is current folder'
HELP_SEARCH = 'If you want to only traverse pages matching some search query'
HELP_ARG_PROXY = 'Proxy to use in format: a.d.d.r:port'

# ids
HELP_QUALITY = 'Prefered video quality. Default is \'' + QUALITIES[0] + '\'. If not found, falls back to best quality'

MODE_PREVIEW = 'preview'
MODE_BEST = 'best'
MODE_LOWQ = 'lowq'


CONNECT_RETRIES_PAGE = 5
CONNECT_RETRIES_ITEM = 10

MAX_VIDEOS_QUEUE_SIZE = 8

Log = print

#
#
#########################################
