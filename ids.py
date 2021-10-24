# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from re import search
from sys import argv
from typing import Any

from asyncio import run as run_async
from aiohttp import ClientSession

from defs import Log, SITE
from download import download_file
from fetch_html import fetch_html


QUALITIES = ['1080p', '720p', '480p', '360p']


def extract_id(aref: Any) -> int:
    return int(search(r'videos/(\d+)/', str(aref.get('href'))).group(1))


def extract_ext(href: str) -> str:
    try:
        return search(r'(\.[^&]{3,5})&', href).group(1)
    except Exception:
        return '.mp4'


async def download_id(idi: int, my_href: str, my_title: str, dest_base: str,
                      req_quality: str = 'unknown', best_quality: bool = True,
                      session: ClientSession = None) -> None:

    i_html = await fetch_html(my_href)
    if i_html:
        ddiv = i_html.find('div', text='Download:')
        if not ddiv or not ddiv.parent:
            Log('cannot find download section for %d, skipping...' % idi)
            return
        links = ddiv.parent.find_all('a', class_='tag_item')
        qualities = []
        for lin in links:
            q = search(r'(\d+0p)', lin.text)
            if q:
                qstr = q.group(1)
                qualities.append(qstr)
                # Log('%d - found %s' % (idi, qstr))
        if not (req_quality in qualities):
            q_idx = 0 if best_quality else -1
            if best_quality is False and req_quality != 'unknown':
                Log('cannot find proper quality for %d, using %s' % (idi, qualities[q_idx]))
            req_quality = qualities[q_idx]
            link_id = q_idx
        else:
            link_id = qualities.index(req_quality)

        link = links[link_id].get('href')
        filename = 'rv_' + str(idi) + '_' + my_title + '_FULL_' + req_quality + '_pydw' + extract_ext(link)

        if session:
            await download_file(filename, dest_base, link, session)
        else:
            async with ClientSession() as s:
                await download_file(filename, dest_base, link, s)

"""
def download_id(idi: int, my_href: str, my_title: str, dest_base: str, req_quality: str = 'unknown', best_quality: bool = True) -> None:

    i_html = fetch_html(my_href)
    if i_html:
        ddiv = i_html.find('div', text='Download:')
        if not ddiv or not ddiv.parent:
            Log('cannot find download section for %d, skipping...' % idi)
            return
        links = ddiv.parent.find_all('a', class_='tag_item')
        qualities = []
        for lin in links:
            q = search(r'(\\d+0p)', lin.text)
            if q:
                qstr = q.group(1)
                qualities.append(qstr)
                # Log('%d - found %s' % (idi, qstr))
        if not (req_quality in qualities):
            q_idx = 0 if best_quality else -1
            if best_quality is False and req_quality != 'unknown':
                Log('cannot find proper quality for %d, using %s' % (idi, qualities[q_idx]))
            req_quality = qualities[q_idx]
            link_id = q_idx
        else:
            link_id = qualities.index(req_quality)

        link = links[link_id].get('href')
        filename = 'rv_' + str(idi) + '_' + my_title + '_FULL_' + req_quality + '_pydw' + extract_ext(link)

        with Session() as s:
            s.keep_alive = True
            if download_file(filename, dest_base, link, s):
                sleep(0.25)
"""


def get_minmax_ids(arefs: list) -> (list, int, int):
    ids = []
    for aref in arefs:
        ids.append(extract_id(aref))
    return (ids, min(ids), max(ids))


async def main() -> None:
    try:
        dest_base = argv[1]
        start_id = int(argv[2])
    except Exception:
        print('ivalid syntax')
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
    a_html = await fetch_html(SITE + 'latest-updates/1/')
    if not a_html:
        Log('cannot connect')
        return

    maxpage = 1
    for page in a_html.find_all('a', attrs={'data-action': 'ajax'}):
        try:
            page_href = str(page.get('href'))
            maxpage = max(maxpage, int(search(r'latest-updates/(\d+)/', page_href).group(1)))
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
        while True:
            increment = max(increment // 2, 1)
            cur_page += increment * direction
            Log('page %d/%d...' % (cur_page, maxpage))
            a_html = await fetch_html(SITE + 'latest-updates/' + str(cur_page) + '/')
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


if __name__ == '__main__':
    run_async(main())
    exit(0)

#
#
#########################################
