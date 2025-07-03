# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations
from asyncio import Lock as AsyncLock, AbstractEventLoop, sleep, get_running_loop
from random import uniform as frand
from urllib.parse import urlparse

from aiohttp import ClientSession, ClientResponse, TCPConnector, ClientResponseError
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup
from fake_useragent import FakeUserAgent

from config import Config
from defs import Mem, UTF8, CONNECT_REQUEST_DELAY, MAX_VIDEOS_QUEUE_SIZE, CONNECT_RETRY_DELAY, MAX_SCAN_QUEUE_SIZE
from logger import Log

__all__ = ('create_session', 'wrap_request', 'fetch_html', 'ensure_conn_closed')

USER_AGENT_DEFAULT = 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Goanna/6.7 Firefox/102.0 PaleMoon/33.3.1'
ua_generator = FakeUserAgent(browsers=('Firefox',), platforms=('desktop',), fallback=USER_AGENT_DEFAULT)

sessionw: ClientSessionWrapper | None = None


class UAManager:
    """
    UAManager
    """
    # noinspection PyProtectedMember
    user_agents = list(set(_['useragent'] for _ in ua_generator._filter_useragents()))
    seed_base = int(frand(0, len(user_agents) + 1))

    @staticmethod
    def _addr_to_int(addr: str, seed: int) -> int:
        return int(urlparse(addr).netloc.replace('.', '').replace(':', '')) + seed + UAManager.seed_base

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
    def __init__(self) -> None:
        self.psession = self.make_session()
        self.npsession = self.make_session(True)
        self.default_exc_handler = get_running_loop().get_exception_handler()
        get_running_loop().set_exception_handler(self.ignore_unclosed_session_exc_handler)

    async def __aenter__(self) -> ClientSessionWrapper:
        global sessionw
        assert sessionw is None
        sessionw = self
        await self.psession.__aenter__()
        await self.npsession.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        global sessionw
        assert sessionw is self
        sessionw = None
        await self.npsession.__aexit__(exc_type, exc_val, exc_tb)
        await self.psession.__aexit__(exc_type, exc_val, exc_tb)

    @staticmethod
    def ignore_unclosed_session_exc_handler(self: AbstractEventLoop, context: dict) -> None:
        message = context.get('message')
        if message not in ('Event loop is closed',) and sessionw is not None and sessionw.default_exc_handler is not None:
            sessionw.default_exc_handler(self, context)
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
        Log.trace(f'[{"P" if Config.proxy and noproxy is False else "NP"}] Selected user-agent \'{new_useragent}\'...')
        s.headers.update({'User-Agent': new_useragent})
        # s.cookie_jar.update_cookies({'kt_rt_popAccess': '1'})
        s.cookie_jar.update_cookies({'kt_tcookie': '1', 'kt_is_visited': '1'})
        if Config.session_id:
            s.cookie_jar.update_cookies({'PHPSESSID': Config.session_id, 'kt_member': '1'})
        return s


class RequestQueue:
    """
    Request delayed queue wrapper
    """
    _queue: list[str] = list()
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
                return BeautifulSoup(content, 'html.parser', from_encoding=UTF8)
        except Exception as e:
            if r is not None and '404.' in str(r.url):
                Log.error('ERROR: 404')
                assert False
            else:
                Log.error(f'[{retries + 1}] fetch_html exception status {f"{r.status:d}" if r is not None else "???"}: '
                          f'\'{e.message if isinstance(e, ClientResponseError) else str(e)}\'')
            if r is None or r.status != 403:
                retries += 1
            elif r is not None and r.status == 403:
                retries_403_local += 1
            if Config.aborted:
                break
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
