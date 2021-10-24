# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from bs4 import BeautifulSoup
from aiohttp import ClientSession

from defs import CONNECT_RETRIES_PAGE, Log


async def fetch_html(url: str, tries=None) -> (BeautifulSoup, None):
    tries = tries or CONNECT_RETRIES_PAGE

    r = None
    retries = 0
    async with ClientSession() as s:
        while retries < tries:
            try:
                async with s.request('GET', url, timeout=7200) as r:
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


"""
def fetch_html(url: str, tries=None) -> (BeautifulSoup, None):
    tries = tries or CONNECT_RETRIES_PAGE

    r = None
    retries = 0
    with Session() as s:
        s.keep_alive = False
        while retries < tries:
            try:
                r = s.request('GET', url, timeout=CONNECT_DELAY_PAGE, stream=False, allow_redirects=True)
                r.raise_for_status()
                break
            except (KeyboardInterrupt,):
                assert False
            except (Exception, HTTPError,):
                if r.url.find('404.') != -1:
                    Log('ERROR: 404')
                    assert False
                retries += 1
                continue

    if retries >= tries:
        errmsg = 'Unable to connect. Aborting %s' % url
        Log(errmsg, True)
        r = None
    elif r is None:
        Log('ERROR: Failed to receive any data', True)

    return None if r is None else BeautifulSoup(r.content, 'html.parser')
"""

#
#
#########################################
