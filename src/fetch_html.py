# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import sleep
from random import uniform as frand
from typing import Optional

from bs4 import BeautifulSoup
from aiohttp import ClientSession, ClientResponse, http_parser

from defs import CONNECT_RETRIES_PAGE, Log, DEFAULT_HEADERS, HOST, CONNECT_REQUEST_DELAY

proxy = None  # type: Optional[str]
request_delay = 0.0


class BypassException(Exception):
    def __init__(self, status: int):
        self.status = status


def set_proxy(prox: str) -> None:
    global proxy
    proxy = prox


async def wrap_request(s: ClientSession, method: str, url: str, **kwargs) -> ClientResponse:
    global request_delay
    while request_delay > 0.0:
        d = request_delay
        request_delay = 0.0
        await sleep(d)
    request_delay = CONNECT_REQUEST_DELAY
    s.headers.update(DEFAULT_HEADERS.copy())
    s.cookie_jar.update_cookies({'kt_rt_popAccess': '1', 'kt_tcookie': '1'}, http_parser.URL(HOST))
    kwargs.update(proxy=proxy)
    return await s.request(method, url, **kwargs)


async def fetch_html(url: str, *, tries: int = None, session: ClientSession) -> Optional[BeautifulSoup]:
    # very basic, minimum validation
    tries = tries or CONNECT_RETRIES_PAGE

    r = None
    retries = 0
    retries_403_local = 0
    while retries < tries:
        try:
            async with await wrap_request(
                    session, 'GET', url, timeout=5,
                    headers={'X-fancyBox': 'true', 'X-Requested-With': 'XMLHttpRequest', 'Host': HOST, 'Referer': url}) as r:
                if r.status != 404:
                    r.raise_for_status()
                content = await r.read()
                if retries_403_local > 0:
                    Log.trace(f'fetch_html success: took {retries_403_local:d} tries...')
                return BeautifulSoup(content, 'html.parser')
        except (KeyboardInterrupt,):
            assert False
        except (Exception,):
            if r is not None and str(r.url).find('404.') != -1:
                Log.error('ERROR: 404')
                assert False
            elif r is not None:
                Log.error(f'fetch_html exception: status {r.status:d}')
            # do not count tries if blocked by ddg
            if r is None or r.status != 403:
                retries += 1
            elif r is not None and r.status == 403:
                retries_403_local += 1
            if retries < tries:
                await sleep(frand(1.0, 7.0))
            continue

    if retries >= tries:
        errmsg = f'Unable to connect. Aborting {url}'
        Log.error(errmsg)
    elif r is None:
        Log.error('ERROR: Failed to receive any data')

    return None

#
#
#########################################
