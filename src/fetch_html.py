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
from aiohttp import ClientSession
# noinspection PyPackageRequirements
from yarl import URL

from defs import CONNECT_RETRIES_PAGE, Log, DEFAULT_HEADERS, HOST

proxy = None  # type: Optional[str]
bypass_in_progress = False
wellknown_sub = ''


class BypassException(Exception):
    def __init__(self, status: int):
        self.status = status


def set_proxy(prox: str) -> None:
    global proxy
    proxy = prox


# def get_proxy() -> str:
#     return proxy


async def bypass_ddos_guard(s: ClientSession, url: str) -> None:
    global bypass_in_progress
    global wellknown_sub
    bypass_in_progress = True

    Log.info('Fetching bypass cookie...')
    url_parsed = parse.urlparse(url)
    url_base = f'{url_parsed.scheme}://{url_parsed.netloc}'
    try:
        if wellknown_sub == '':
            r = await s.request('GET', 'https://check.ddos-guard.net/check.js', proxy=proxy)
            if r is None or r.status != 200:
                Log.info('No response from the check host (2)!')
                raise BypassException(r.status if r is not None else -2)
            wellknown_sub = re_fullmatch(r'^.*\'(/\.[^\']+)\'.*?$', str(await r.content.read())).group(1)
            # wellknown_id = wellknown_sub[wellknown_sub.rfind('/') + 1:]
            await s.request('GET', f'{url_base}{wellknown_sub}', proxy=proxy)
            # if r is None or r.status != 200:
            #     Log.info('No response from the wks host (3)!')
            #     raise BypassException(r.status if r is not None else -3)
            # bypass_cookie.update(__ddg2_=wellknown_id)
            # noinspection PyTypeChecker
            # bypass_cookie.update(__ddg5_=s.cookie_jar.filter_cookies(url_base).get('__ddg5_').value)
            # s.cookie_jar.update_cookies(bypass_cookie, URL(url_base))
            # await s.request('GET', f'https://check.ddos-guard.net/set/id/{wellknown_id}', proxy=proxy)
            # r = await s.request('POST', f'{url_base}/.well-known/ddos-guard/mark/', proxy=proxy, data=post_data)
            # assert r and r.status == 200
            # await sleep(2.5)
            while True:
                r = await s.request('GET', url, proxy=proxy)
                if r is None or r.status == 403:
                    Log.info(f'Response from base host is {r.status if r is not None else -1:d} (5)!')
                    await sleep(frand(1.0, 7.0))
                break
    except BypassException as be:
        if be.status != 200:
            assert False
    except Exception:
        raise
    finally:
        bypass_in_progress = False
    return


# noinspection PyProtectedMember
async def wrap_request(s: ClientSession, method: str, url: str, **kwargs):
    while bypass_in_progress is True:
        await sleep(1.0)
    # if len(bypass_cookie) == 0:
    #     await bypass_ddos_guard(s, url)
    s.headers.update(DEFAULT_HEADERS.copy())
    s.cookie_jar.update_cookies({'kt_rt_popAccess': '1', 'kt_tcookie': '1'}, URL(HOST))
    kwargs.update(proxy=proxy)
    # kwargs.update(cookies=bypass_cookie)
    r = await s.request(method, url, **kwargs)
    if r is not None and r.status in [403, 503] and wellknown_sub == '':
        await bypass_ddos_guard(s, url)
        s.headers.update(DEFAULT_HEADERS.copy())
        return s.request(method, url, **kwargs)
    return r


async def fetch_html(url: str, *, tries: int = None, session: ClientSession) -> Optional[BeautifulSoup]:
    # very basic, minimum validation
    tries = tries or CONNECT_RETRIES_PAGE

    r = None
    retries = 0
    while retries < tries:
        try:
            # async with s.request('GET', url, timeout=5, proxy=proxy) as r:
            async with await wrap_request(
                    session, 'GET', url, timeout=5,
                    headers={'X-fancyBox': 'true', 'X-Requested-With': 'XMLHttpRequest', 'Host': HOST, 'Referer': url}) as r:
                if r.status != 404:
                    r.raise_for_status()
                content = await r.read()
                return BeautifulSoup(content, 'html.parser')
        except (KeyboardInterrupt,):
            assert False
        except (Exception,):
            if r is not None and str(r.url).find('404.') != -1:
                Log.error('ERROR: 404')
                assert False
            elif r is not None:
                Log.error(f'fetch_html exception: status {r.status:d}')
            retries += 1
            if retries < tries:
                await sleep(frand(1.5, 3.0))
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
