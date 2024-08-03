# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import Lock as AsyncLock, sleep, get_running_loop
from random import uniform as frand
from typing import Optional, List

from aiohttp import ClientSession, ClientResponse, TCPConnector, ClientResponseError
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup

from config import Config
from defs import Mem, UTF8, DEFAULT_HEADERS, CONNECT_REQUEST_DELAY, MAX_VIDEOS_QUEUE_SIZE, CONNECT_RETRY_DELAY, MAX_SCAN_QUEUE_SIZE
from logger import Log

__all__ = ('make_session', 'wrap_request', 'fetch_html', 'ensure_conn_closed')


class RequestQueue:
    """
    Request delayed queue wrapper
    """
    _queue: List[str] = list()
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


def ensure_conn_closed(r: Optional[ClientResponse]) -> None:
    if r is not None and not r.closed:
        r.close()


def make_session(noproxy=False) -> ClientSession:
    if Config.proxy and noproxy is False:
        connector = ProxyConnector.from_url(Config.proxy, limit=MAX_VIDEOS_QUEUE_SIZE + MAX_SCAN_QUEUE_SIZE)
    else:
        connector = TCPConnector(limit=MAX_VIDEOS_QUEUE_SIZE + MAX_SCAN_QUEUE_SIZE)
    s = ClientSession(connector=connector, read_bufsize=Mem.MB)
    s.headers.update(DEFAULT_HEADERS.copy())
    # s.cookie_jar.update_cookies({'kt_rt_popAccess': '1'})
    s.cookie_jar.update_cookies({'kt_tcookie': '1', 'kt_is_visited': '1'})
    if Config.session_id:
        s.cookie_jar.update_cookies({'PHPSESSID': Config.session_id, 'kt_member': '1'})
    return s


async def wrap_request(s: ClientSession, method: str, url: str, noproxy=False, **kwargs) -> ClientResponse:
    """Queues request, updating headers/proxies beforehand, and returns the response"""
    if Config.nodelay is False:
        await RequestQueue.until_ready(url)
    if 'timeout' not in kwargs:
        kwargs.update(timeout=Config.timeout)
    # noinspection PyUnresolvedReferences
    r = await (s.np if noproxy else s).request(method, url, **kwargs)
    return r


async def fetch_html(url: str, *, tries=0, session: ClientSession) -> Optional[BeautifulSoup]:
    # very basic, minimum validation
    tries = tries or Config.retries

    retries = 0
    retries_403_local = 0
    while retries <= tries:
        r = None
        try:
            async with await wrap_request(
                    session, 'GET', url,
                    headers={'Connection': 'keep-alive', 'X-fancyBox': 'true', 'X-Requested-With': 'XMLHttpRequest'}) as r:
                if r.status != 404:
                    r.raise_for_status()
                content = await r.read()
                if retries_403_local > 0:
                    Log.trace(f'fetch_html success: took {retries_403_local:d} tries...')
                return BeautifulSoup(content, 'html.parser', from_encoding=UTF8)
        except Exception as e:
            if r is not None and '404.' in str(r.url):
                Log.error('ERROR: 404')
                assert False
            else:
                Log.error(f'fetch_html exception status {f"{r.status:d}" if r is not None else "???"}: '
                          f'\'{e.message if isinstance(e, ClientResponseError) else str(e)}\'')
            if r is None or r.status != 403:
                retries += 1
            elif r is not None and r.status == 403:
                retries_403_local += 1
            if retries <= tries:
                await sleep(frand(*CONNECT_RETRY_DELAY))
            continue

    if retries > tries:
        errmsg = f'Unable to connect. Aborting {url}'
        Log.error(errmsg)
    elif r is None:
        Log.error('ERROR: Failed to receive any data')

    return None

#
#
#########################################
