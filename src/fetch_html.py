# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import sleep
from random import uniform as frand
from re import fullmatch as re_fullmatch
from typing import Optional
from urllib import parse

from bs4 import BeautifulSoup
from aiohttp import ClientSession, ClientResponse, http_parser

from defs import CONNECT_RETRIES_PAGE, Log, DEFAULT_HEADERS, HOST, MAX_VIDEOS_QUEUE_SIZE

proxy = None  # type: Optional[str]
bypass_in_progress = False
wellknown_sub = None  # type: Optional[str]
retries_403 = 0


class BypassException(Exception):
    def __init__(self, status: int):
        self.status = status


def set_proxy(prox: str) -> None:
    global proxy
    proxy = prox


async def bypass_ddos_guard_again(s: ClientSession, url: str) -> None:
    global wellknown_sub
    wellknown_sub = None
    await bypass_ddos_guard(s, url)


async def bypass_ddos_guard(s: ClientSession, url: str) -> None:
    global bypass_in_progress
    global wellknown_sub

    if bypass_in_progress is True:
        while bypass_in_progress is True:
            await sleep(1.0)
        return

    bypass_in_progress = True
    try:
        Log.info('Bypass: fetching bypass cookie...')
        if wellknown_sub is None:
            url_parsed = parse.urlparse(url)
            url_base = f'{url_parsed.scheme}://{url_parsed.netloc}'
            r = await s.request('GET', 'https://check.ddos-guard.net/check.js', proxy=proxy)
            if r is None or r.status != 200:
                Log.error('Bypass: no response from the check host (1)!')
                raise BypassException(r.status if r is not None else -1)
            wellknown_sub = re_fullmatch(r'^.*\'(/\.[^\']+)\'.*?$', str(await r.content.read())).group(1)
            await s.request('GET', f'{url_base}{wellknown_sub}', proxy=proxy)
            while True:
                r = await s.request('GET', url, proxy=proxy)
                if r is None or r.status == 403:
                    Log.trace(f'Bypass: response from base host is {r.status if r is not None else -1:d} (2)!')
                    await sleep(frand(1.0, 7.0))
                break
    except BypassException as be:
        if be.status != 200:
            assert False
    except Exception:
        raise
    finally:
        bypass_in_progress = False


async def wrap_request(s: ClientSession, method: str, url: str, **kwargs) -> ClientResponse:
    while bypass_in_progress is True:
        await sleep(1.0)
    s.headers.update(DEFAULT_HEADERS.copy())
    s.cookie_jar.update_cookies({'kt_rt_popAccess': '1', 'kt_tcookie': '1'}, http_parser.URL(HOST))
    kwargs.update(proxy=proxy)
    r = await s.request(method, url, **kwargs)
    if r is not None and r.status in [403, 503] and wellknown_sub is None:
        await bypass_ddos_guard(s, url)
        r = await s.request(method, url, **kwargs)
    return r


async def fetch_html(url: str, *, tries: int = None, session: ClientSession) -> Optional[BeautifulSoup]:
    global retries_403
    # very basic, minimum validation
    tries = tries or CONNECT_RETRIES_PAGE

    r = None
    retries = 0
    retries_403_local = 0
    while retries < tries:
        try:
            # async with s.request('GET', url, timeout=5, proxy=proxy) as r:
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
                retries_403 += 1
                retries_403_local += 1
                if retries_403 >= CONNECT_RETRIES_PAGE * MAX_VIDEOS_QUEUE_SIZE:
                    await bypass_ddos_guard_again(session, url)
                    retries_403 = 0
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
