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
    'aHR0cHM6Ly9ydWxlMzR2aWRlby5jb20vc2VhcmNoLz9tb2RlPWFzeW5jJmZ1bmN0aW9uPWdldF9ibG9jayZibG9ja19pZD1jdXN0b21fbGlzdF92aWRlb3NfdmlkZW9zX2'
    'xpc3Rfc2VhcmNoJnE9JXMmc29ydF9ieT1pZCZmcm9tX3ZpZGVvcz0lZA==').decode()

USER_AGENT = 'Mozilla/5.0 (X11; Linux i686; rv:68.9) Gecko/20100101 Goanna/4.8 Firefox/68.9'
DEFAULT_HEADERS = {'User-Agent': USER_AGENT}

REPLACE_SYMBOLS = r'[^\da-zA-Z._\-\[\] ]'

CONNECT_RETRIES_PAGE = 10000
CONNECT_RETRIES_ITEM = 10000

MAX_VIDEOS_QUEUE_SIZE = 8

Log = print

#
#
#########################################
