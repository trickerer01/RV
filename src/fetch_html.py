# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations

import random
import urllib.parse
from asyncio import AbstractEventLoop, get_running_loop, sleep
from asyncio import Lock as AsyncLock
from collections import deque
from contextlib import AsyncExitStack

from aiohttp import ClientConnectorError, ClientResponse, ClientResponseError, ClientSession, TCPConnector
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup
from fake_useragent import FakeUserAgent

from config import Config
from defs import CONNECT_REQUEST_DELAY, CONNECT_RETRY_DELAY, MAX_SCAN_QUEUE_SIZE, MAX_VIDEOS_QUEUE_SIZE, UTF8, Mem
from logger import Log

__all__ = ('create_session', 'ensure_conn_closed', 'fetch_html', 'wrap_request')

USER_AGENT_DEFAULT = 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Goanna/6.7 Firefox/102.0 PaleMoon/33.3.1'
ua_generator = FakeUserAgent(browsers=('Firefox',), platforms=('desktop',), fallback=USER_AGENT_DEFAULT)

sessionw: ClientSessionWrapper | None = None


class UAManager:
    """
    UAManager
    """
    # noinspection PyProtectedMember
    user_agents = list(set(_['useragent'] for _ in ua_generator._filter_useragents()))
    seed_base = int(random.uniform(0, len(user_agents) + 1))

    @staticmethod
    def _addr_to_int(addr: str, seed: int) -> int:
        return int(urllib.parse.urlparse(addr).netloc.replace('.', '').replace(':', '')) + seed + UAManager.seed_base

    @staticmethod
    def _generate(addr: str, seed: int) -> str:
        idx = UAManager._addr_to_int(addr, seed) % len(UAManager.user_agents)
        ua = UAManager.user_agents[idx]
        return ua

    @staticmethod
    def select_useragent(addr: str | None) -> str:
        prox_addr = addr or 'http://127.0.0.1:0'
        prox_seed = 0
        ua = UAManager._generate(prox_addr, prox_seed)
        return ua


class ClientSessionWrapper:
    """
    ClientSessionWrapper
    """
    PSESSION_INDEX = 0
    NPSESSION_INDEX = 1

    def __init__(self) -> None:
        self._exitstack = AsyncExitStack()
        self._sessions = (self.make_session(), self.make_session(True))
        self.default_exc_handler = get_running_loop().get_exception_handler()
        get_running_loop().set_exception_handler(self.ignore_unclosed_session_exc_handler)

    async def __aenter__(self) -> ClientSessionWrapper:
        global sessionw
        assert sessionw is None
        sessionw = self
        [await self._exitstack.enter_async_context(s) for s in self._sessions]
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        global sessionw
        assert sessionw is self
        sessionw = None
        await self._exitstack.aclose()

    @property
    def psession(self) -> ClientSession:
        return self._sessions[ClientSessionWrapper.PSESSION_INDEX]

    @property
    def npsession(self) -> ClientSession:
        return self._sessions[ClientSessionWrapper.NPSESSION_INDEX]

    @staticmethod
    def ignore_unclosed_session_exc_handler(selfloop: AbstractEventLoop, context: dict) -> None:
        message = context.get('message')
        if message not in ('Event loop is closed',) and sessionw is not None and sessionw.default_exc_handler is not None:
            sessionw.default_exc_handler(selfloop, context)
        else:
            Log.trace(f'{message} exception ignored...')

    @staticmethod
    def make_session(noproxy=False) -> ClientSession:
        use_proxy = Config.proxy and noproxy is False
        if use_proxy:
            connector = ProxyConnector.from_url(Config.proxy, limit=MAX_VIDEOS_QUEUE_SIZE + MAX_SCAN_QUEUE_SIZE)
        else:
            connector = TCPConnector(limit=MAX_VIDEOS_QUEUE_SIZE + MAX_SCAN_QUEUE_SIZE)
        s = ClientSession(connector=connector, read_bufsize=Mem.MB)
        new_useragent = UAManager.select_useragent(Config.proxy if use_proxy else None)
        Log.trace(f'[{"P" if use_proxy else "NP"}] Selected user-agent \'{new_useragent}\'...')
        s.headers.update({'User-Agent': new_useragent})
        # s.cookie_jar.update_cookies({'kt_rt_popAccess': '1'})
        s.cookie_jar.update_cookies({'kt_tcookie': '1', 'kt_is_visited': '1'})
        if Config.session_id:
            s.cookie_jar.update_cookies({'PHPSESSID': Config.session_id, 'kt_member': '1'})
        if Config.extra_headers:
            for hk, hv in Config.extra_headers:
                s.headers.update({hk: hv})
        if Config.extra_cookies:
            for ck, cv in Config.extra_cookies:
                s.cookie_jar.update_cookies({ck: cv})
        return s


class RequestQueue:
    """
    Request delayed queue wrapper
    """
    _queue = deque[str]()
    _ready = True
    _lock = AsyncLock()

    @staticmethod
    def _reset() -> None:
        RequestQueue._ready = True
        RequestQueue._queue.clear()

    @staticmethod
    async def _set_ready() -> None:
        await sleep(random.uniform(CONNECT_REQUEST_DELAY, CONNECT_REQUEST_DELAY + 0.75))
        RequestQueue._ready = True

    @staticmethod
    async def until_ready(url: str) -> None:
        """Pauses request until base delay passes (since last request)"""
        async with RequestQueue._lock:
            RequestQueue._queue.append(url)
        while RequestQueue._ready is False or RequestQueue._queue[0] != url:
            await sleep(0.2)
        async with RequestQueue._lock:
            RequestQueue._queue.popleft()
            RequestQueue._ready = False
            get_running_loop().create_task(RequestQueue._set_ready())


def ensure_conn_closed(r: ClientResponse | None) -> None:
    if r is not None and not r.closed:
        r.close()


def create_session() -> ClientSessionWrapper:
    return ClientSessionWrapper()


async def wrap_request(method: str, url: str, **kwargs) -> ClientResponse:
    """Queues request, updating headers/proxies beforehand, and returns the response"""
    if Config.nodelay is False:
        await RequestQueue.until_ready(url)
    if 'timeout' not in kwargs:
        kwargs.update(timeout=Config.timeout)
    noproxy = kwargs.pop('noproxy', False)
    r = await (sessionw.npsession if noproxy else sessionw.psession).request(method, url, **kwargs)
    return r


async def fetch_html(url: str, *, tries=0, **kwargs) -> BeautifulSoup | None:
    # very basic, minimum validation
    tries = tries or Config.retries
    if 'noproxy' not in kwargs:
        kwargs.update({'noproxy': bool(Config.proxy and Config.html_without_proxy)})

    retries = 0
    retries_403_local = 0
    while retries <= tries:
        r = None
        try:
            async with await wrap_request(
                    'GET', url,
                    headers={'Connection': 'keep-alive', 'X-fancyBox': 'true', 'X-Requested-With': 'XMLHttpRequest'}, **kwargs) as r:
                if r.status != 404:
                    r.raise_for_status()
                content = await r.read()
                if retries_403_local > 0:
                    Log.trace(f'fetch_html success: took {retries_403_local:d} tries...')
                return BeautifulSoup(content, 'html.parser', from_encoding=UTF8) if content else BeautifulSoup()
        except Exception as e:
            if r is not None and '404.' in str(r.url):
                Log.error('ERROR: 404')
                assert False
            else:
                Log.error(f'[{retries + 1}] fetch_html exception status {f"{r.status:d}" if r is not None else "???"}: '
                          f'\'{e.message if isinstance(e, ClientResponseError) else str(e)}\'')
            if (r is None or r.status != 403) and not isinstance(e, ClientConnectorError):
                retries += 1
            elif r is not None and r.status == 403:
                retries_403_local += 1
            if Config.aborted:
                break
            if retries <= tries:
                await sleep(random.uniform(*CONNECT_RETRY_DELAY))
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
