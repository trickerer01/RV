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

from defs import Log, SITE_AJAX_REQUEST_BASE
from download import download_id, failed_items
from fetch_html import fetch_html


QUALITIES = ['1080p', '720p', '480p', '360p']


def extract_id(aref: Any) -> int:
    return int(search(r'videos/(\d+)/', str(aref.get('href'))).group(1))


def get_minmax_ids(arefs: list) -> (list, int, int):
    ids = []
    for aref in arefs:
        ids.append(extract_id(aref))
    return (ids, min(ids), max(ids))


async def main():
    try:
        # path is not validated
        dest_base = argv[1]
        start_id = int(argv[2])
    except Exception:
        print('Syntax: Destination StartId [EndId] [Quality]\n  qualities:%s' % ''.join(' ' + q for q in QUALITIES))
        return

    try:
        end_id = int(argv[3])
    except Exception:
        end_id = start_id

    try:
        req_quality = argv[4]
        if not (req_quality in QUALITIES):
            req_quality = QUALITIES[0]
    except Exception:
        req_quality = QUALITIES[0]

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

            arefs = a_html.find_all('a', class_='th js-open-popup')
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
                # failing
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

        await download_id(idi, my_href, my_title, dest_base, req_quality)

    if len(failed_items) > 0:
        Log('Failed items:')
        for fi in failed_items:
            Log(' ', str(fi))


async def run_main():
    await main()
    await sleep(0.25)


if __name__ == '__main__':
    run_async(run_main())
    # Log('Searching by ID is disabled, reason: Buggy, videos are not properly sorted by id, meking binary search mostly useless')
    exit(0)

#
#
#########################################
