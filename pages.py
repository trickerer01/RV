# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from re import search
from sys import argv

from asyncio import run as run_async, as_completed, sleep
from aiohttp import ClientSession, TCPConnector

from defs import Log, SITE
from download import download_file
from fetch_html import fetch_html
from ids import download_id, extract_id


class VideoEntryFull:
    def __init__(self, m_id: int, m_href: str, m_title: str):
        self.my_id = m_id or 0
        self.my_href = m_href or ''
        self.my_title = m_title or ''


class VideoEntryPrev:
    def __init__(self, m_filename: str, m_link: str):
        self.my_filename = m_filename or ''
        self.my_link = m_link or ''


async def main() -> None:
    try:
        dest_base = argv[1]
        start_page = int(argv[2])
    except Exception:
        print('ivalid syntax')
        return

    try:
        pages_count = int(argv[3])
    except Exception:
        pages_count = 1

    try:
        do_full = int(argv[4])
        assert 0 <= do_full <= 2
    except Exception:
        do_full = 0

    try:
        stop_id = int(argv[5])
    except Exception:
        stop_id = 1

    vid_entries = list()
    if do_full in [1, 2]:
        # not async here
        for pi in range(start_page, start_page + pages_count):
            Log('page %d...' % pi)
            a_html = await fetch_html(SITE + 'latest-updates/' + str(pi) + '/')
            if not a_html:
                Log('cannot get html for page %d', pi)
                continue
            arefs = a_html.find_all('a', class_='th js-open-popup')
            for aref in arefs:
                cur_id = extract_id(aref)
                if cur_id < stop_id:
                    Log('skipping %d < %d' % (cur_id, stop_id))
                    continue
                my_href = aref.get('href')
                my_title = aref.get('title')
                vid_entries.append(VideoEntryFull(cur_id, my_href, my_title))

        async with ClientSession(connector=TCPConnector(limit=10), read_bufsize=2**20) as s:
            for cv in as_completed([download_id(v.my_id, v.my_href, v.my_title, dest_base, best_quality=(do_full == 1), session=s)
                                    for v in list(reversed(vid_entries))]):
                await cv
    else:
        # not async here
        for pi in range(start_page, start_page + pages_count):
            Log('page %d...' % pi)
            a_html = await fetch_html(SITE + 'latest-updates/' + str(pi) + '/')
            if not a_html:
                Log('cannot get html for page %d', pi)
                continue

            prev_all = a_html.find_all('div', class_='img wrap_image')
            titl_all = a_html.find_all('div', class_='thumb_title')
            cur_num = 1
            for i, p in enumerate(prev_all):
                cur_num += 1
                link = p.get('data-preview')
                name = titl_all[i].text
                v_id = search(r'/(\d+)_preview.*(\.[^/]+)/', link)
                try:
                    cur_id = int(v_id.group(1)) if v_id else 1000000000
                except Exception:
                    cur_id = 1000000000
                if cur_id < stop_id:
                    Log('skipping %d < %d' % (cur_id, stop_id))
                    continue
                filename = 'rv_' + (v_id.group(1) + '_' + name + '_pypv' + v_id.group(2) if v_id else name + '_pypv.mp4')
                vid_entries.append(VideoEntryPrev(filename, link))

        async with ClientSession(connector=TCPConnector(limit=10), connector_owner=False) as s:
            for cv in as_completed([download_file(v.my_filename, dest_base, v.my_link, s)] for v in list(reversed(vid_entries))):
                await cv


async def run_main():
    await main()
    await sleep(0.25)


if __name__ == '__main__':
    run_async(run_main())
    exit(0)

#
#
#########################################
