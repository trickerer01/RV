# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from base64 import b64decode


SITE = b64decode('aHR0cHM6Ly9ydWxlMzR2aWRlby5jb20v').decode()

REPLACE_SYMBOLS = r'[^\dA-z._\-\[\] ]'

CONNECT_RETRIES_PAGE = 10000
CONNECT_RETRIES_ITEM = 10000

Log = print

#
#
#########################################
