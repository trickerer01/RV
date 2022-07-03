# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from typing import Optional

from bs4 import BeautifulSoup
from aiohttp import ClientSession

from defs import CONNECT_RETRIES_PAGE, Log, DEFAULT_HEADERS


proxy = None  # type: Optional[str]


def set_proxy(prox: str) -> None:
    global proxy
    proxy = prox


def get_proxy() -> str:
    return proxy


async def fetch_html(url: str, tries=None) -> (BeautifulSoup, None):
    # very basic, minimum validation
    tries = tries or CONNECT_RETRIES_PAGE

    r = None
    retries = 0
    async with ClientSession() as s:
        s.headers.update(DEFAULT_HEADERS)
        while retries < tries:
            try:
                async with s.request('GET', url, timeout=7200, proxy=proxy) as r:
                    content = await r.read()
                    return BeautifulSoup(content, 'html.parser')
            except (KeyboardInterrupt,):
                assert False
            except (Exception,):
                if r and str(r.url).find('404.') != -1:
                    Log('ERROR: 404')
                    assert False
                retries += 1
                continue

    if retries >= tries:
        errmsg = 'Unable to connect. Aborting %s' % url
        Log(errmsg, True)
    elif r is None:
        Log('ERROR: Failed to receive any data', True)

    return None

#
#
#########################################
