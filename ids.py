# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import run as run_async, sleep
from re import search
from sys import argv
from typing import Any

from aiohttp import ClientSession, TCPConnector
from bs4 import BeautifulSoup

from cmdargs import prepare_arglist_ids
from defs import Log, SITE_AJAX_REQUEST_BASE, MAX_VIDEOS_QUEUE_SIZE
from download import download_id, failed_items
from fetch_html import fetch_html, set_proxy


def extract_id(aref: Any) -> int:
    return int(search(r'videos/(\d+)/', str(aref.get('href'))).group(1))


def get_minmax_ids(arefs: list) -> (list, int, int):
    ids = []
    for aref in arefs:
        ids.append(extract_id(aref))
    return (ids, min(ids), max(ids))


async def main() -> None:
    try:
        arglist = prepare_arglist_ids(argv[1:])
    except Exception:
        Log('\nUnable to parse cmdline. Exiting...')
        return

    try:
        dest_base = arglist.path
        start_id = arglist.start
        end_id = arglist.end
        req_quality = arglist.quality
        set_proxy(arglist.proxy)

        if start_id > end_id:
            Log(('\nError: start (%d) > end (%d)' % (start_id, end_id)))
            raise ValueError
    except Exception:
        Log('\nError reading parsed arglist!')
        return

    # pages
    a_html = await fetch_html(SITE_AJAX_REQUEST_BASE % ('', 1))
    if not a_html:
        Log('cannot connect')
        return

    maxpage = 1
    for page_ajax in a_html.find_all('a', attrs={'data-action': 'ajax'}):
        try:
            data_params = str(page_ajax.get('data-parameters'))
            maxpage = max(maxpage, int(search(r'from_albums:(\d+)', data_params).group(1)))
        except Exception:
            pass

    Log('max page: %d...' % maxpage)

    def gather_arefs(base_html: BeautifulSoup) -> list:
        return base_html.find_all('a', class_='th js-open-popup')

    async def gather_surrounding_pages(p_cur: int, p_max: int, incr: int) -> list:
        results = list()
        Log(('gathering arefs from pages %d - %d' % (p_cur - incr, p_cur + incr)))
        for p_num in range(p_cur - incr, p_cur + incr):
            if p_num < 1 or p_num == p_cur:
                continue
            if p_num > p_max:
                break
            base_html = await fetch_html(SITE_AJAX_REQUEST_BASE % ('', p_num))
            if not base_html:
                continue
            results += gather_arefs(base_html)

        return results

    for idi in range(start_id, end_id + 1):
        Log('id %d...' % idi)
        my_href = None
        my_title = None

        # binary search to find a page with that id
        cur_page = 1
        increment = maxpage
        direction = 1

        arefs = []
        while True:
            increment = max(increment // 2, 1)
            cur_page += increment * direction
            Log('page %d/%d...' % (cur_page, maxpage))

            if cur_page < 1 or cur_page > maxpage:
                Log('Page is out of bounds! Cannot find %d' % idi)
                failed_items.append(idi)
                break

            a_html = await fetch_html(SITE_AJAX_REQUEST_BASE % ('', cur_page))
            if not a_html:
                Log('cannot connect')
                return

            arefs = gather_arefs(a_html)
            try:
                ids, id_min, id_max = get_minmax_ids(arefs)
            except Exception:
                Log('cannot find min/max elements on page %d! Aborting' % cur_page)
                return

            if idi in ids:
                # current page is what we want
                maxpage = cur_page
                break
            elif id_min < idi < id_max:
                # failing, try to compensate for unsorted ids
                arefs += await gather_surrounding_pages(cur_page, maxpage, increment)
                break
            elif idi < id_min:
                direction = 1
                continue
            elif idi > id_max:
                direction = -1
                continue

        for aref in arefs:
            c_id = extract_id(aref)
            if c_id == idi:
                my_href = aref.get('href')
                my_title = aref.get('title')
                break

        if not my_href or not my_title:
            Log('id %d is not found! Skipped.' % idi)
            continue

        async with ClientSession(connector=TCPConnector(limit=MAX_VIDEOS_QUEUE_SIZE), read_bufsize=2**20) as s:
            await download_id(idi, my_href, my_title, dest_base, req_quality, True, s)

    if len(failed_items) > 0:
        failed_items.sort()
        Log('Failed items:')
        for fi in failed_items:
            Log(' ', str(fi))


async def run_main():
    await main()
    await sleep(0.5)


if __name__ == '__main__':
    run_async(run_main())
    # Log('Searching by ID is disabled, reason: Buggy, videos are not properly sorted by id, meking binary search mostly useless')
    exit(0)

#
#
#########################################
