# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import sleep, get_running_loop, Lock as AsyncLock
from random import uniform as frand
from typing import Optional, List
from urllib.parse import urlparse

from aiohttp import ClientSession, ClientResponse, TCPConnector
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup
from python_socks import ProxyType

from defs import CONNECT_RETRIES_PAGE, Log, DEFAULT_HEADERS, CONNECT_REQUEST_DELAY, MAX_VIDEOS_QUEUE_SIZE, Config, UTF8

__all__ = ('make_session', 'wrap_request', 'fetch_html')


class RequestQueue:
    """
    Request delayed queue wrapper
    """
    _queue = list()  # type: List[str]
    _ready = True
    _lock = AsyncLock()

    @staticmethod
    async def _reset() -> None:
        await sleep(frand(CONNECT_REQUEST_DELAY, CONNECT_REQUEST_DELAY + 0.75))
        RequestQueue._ready = True

    @staticmethod
    async def until_ready(url: str) -> None:
        """Pauses request until base delay passes (since last request)"""
        RequestQueue._queue.append(url)
        while RequestQueue._ready is False or RequestQueue._queue[0] != url:
            await sleep(0.2)
        async with RequestQueue._lock:
            del RequestQueue._queue[0]
            RequestQueue._ready = False
            get_running_loop().create_task(RequestQueue._reset())


async def make_session(session_id: str = None) -> ClientSession:
    if Config.proxy:
        pp = urlparse(Config.proxy)
        ptype = ProxyType.SOCKS5 if pp.scheme in ('socks5', 'socks5h') else ProxyType.HTTP
        connector = ProxyConnector(limit=MAX_VIDEOS_QUEUE_SIZE, proxy_type=ptype, host=pp.hostname, port=pp.port)
    else:
        connector = TCPConnector(limit=MAX_VIDEOS_QUEUE_SIZE)
    s = ClientSession(connector=connector, read_bufsize=2**20)
    s.cookie_jar.update_cookies({'kt_rt_popAccess': '1', 'kt_tcookie': '1'})
    if session_id:
        s.cookie_jar.update_cookies({'PHPSESSID': session_id, 'kt_member': '1'})
        pass
    return s


async def wrap_request(s: ClientSession, method: str, url: str, **kwargs) -> ClientResponse:
    """Queues request, updating headers/proxies beforehand, and returns the response"""
    if Config.nodelay is False:
        await RequestQueue.until_ready(url)
    s.headers.update(DEFAULT_HEADERS.copy())
    r = await s.request(method, url, **kwargs)
    return r


async def fetch_html(url: str, *, tries: int = None, session: ClientSession) -> Optional[BeautifulSoup]:
    # very basic, minimum validation
    tries = tries or CONNECT_RETRIES_PAGE

    r = None
    retries = 0
    retries_403_local = 0
    while retries < tries:
        try:
            async with await wrap_request(
                    session, 'GET', url, timeout=10,
                    headers={'Connection': 'keep-alive', 'X-fancyBox': 'true', 'X-Requested-With': 'XMLHttpRequest'}) as r:
                if r.status != 404:
                    r.raise_for_status()
                content = await r.read()
                if retries_403_local > 0:
                    Log.trace(f'fetch_html success: took {retries_403_local:d} tries...')
                return BeautifulSoup(content, 'html.parser', from_encoding=UTF8)
        except Exception:
            if r is not None and str(r.url).find('404.') != -1:
                Log.error('ERROR: 404')
                assert False
            elif r is not None:
                Log.error(f'fetch_html exception: status {r.status:d}')
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
