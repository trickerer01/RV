# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import run as run_async, as_completed, sleep
from re import search
from sys import argv
from typing import List

from aiohttp import ClientSession, TCPConnector

from defs import Log, SITE, DEFAULT_HEADERS
from download import download_file
from fetch_html import fetch_html
from ids import download_id, extract_id


MAX_VIDEOS_QUEUE_SIZE = 250


class VideoEntryBase:
    def __init__(self, m_id: int):
        self.my_id = m_id or 0


class VideoEntryFull(VideoEntryBase):
    def __init__(self, m_id: int, m_href: str, m_title: str):
        super().__init__(m_id)
        self.my_href = m_href or ''
        self.my_title = m_title or ''


class VideoEntryPrev(VideoEntryBase):
    def __init__(self, m_id: int, m_filename: str, m_link: str):
        super().__init__(m_id)
        self.my_filename = m_filename or ''
        self.my_link = m_link or ''


def get_minmax_ids(entry_list: List[VideoEntryBase]) -> (int, int):
    minid = 0
    maxid = 0
    for entry in entry_list:
        if entry.my_id == 0:
            continue
        if entry.my_id > maxid:
            maxid = entry.my_id
        if entry.my_id < minid or minid == 0:
            minid = entry.my_id

    return minid, maxid


async def main() -> None:
    try:
        # path is not validated
        dest_base = argv[1]
        start_page = int(argv[2])
    except Exception:
        print('Syntax: Destination StartPage [NumPages] [Full] [StopId]'
              '\n destination: str\n startpage: int\n numpages(1): int\n full(0): int[0(preview), 1(full), 2(full lowq)]\n stopid(1): int')
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

        if len(vid_entries) == 0:
            Log('\nNo videos found. Aborted.')
            return
        minid, maxid = get_minmax_ids(vid_entries)
        Log('\nOk! %d videos found, bound %d to %d. Working...\n' % (len(vid_entries), minid, maxid))
        vid_entries = list(reversed(vid_entries))
        while len(vid_entries) > 0:
            index = min(MAX_VIDEOS_QUEUE_SIZE, len(vid_entries))
            vids_cur = vid_entries[:index]
            vid_entries = vid_entries[index:]
            async with ClientSession(connector=TCPConnector(limit=8), read_bufsize=2**20) as s:
                s.headers.update(DEFAULT_HEADERS)
                for cv in as_completed([download_id(v.my_id, v.my_href, v.my_title, dest_base, best_quality=(do_full == 1), session=s)
                                        for v in vids_cur]):
                    await cv
    else:
        # not async here
        for pi in range(start_page, start_page + pages_count):
            Log('page %d...' % pi)
            a_html = await fetch_html(SITE + 'latest-updates/' + str(pi) + '/')
            if not a_html:
                Log('cannot get html for page %d', pi)
                continue

            content_div = a_html.find('div', class_='thumbs clearfix')

            prev_all = content_div.find_all('div', class_='img wrap_image')
            titl_all = content_div.find_all('div', class_='thumb_title')
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
                vid_entries.append(VideoEntryPrev(cur_id, filename, link))

        if len(vid_entries) == 0:
            Log('\nNo videos found. Aborted.')
            return
        minid, maxid = get_minmax_ids(vid_entries)
        Log('\nOk! %d videos found, bound %d to %d. Working...\n' % (len(vid_entries), minid, maxid))
        vid_entries = list(reversed(vid_entries))
        while len(vid_entries) > 0:
            index = min(MAX_VIDEOS_QUEUE_SIZE, len(vid_entries))
            vids_cur = vid_entries[:index]
            vid_entries = vid_entries[index:]
            async with ClientSession(connector=TCPConnector(limit=8), read_bufsize=2**20) as s:
                s.headers.update(DEFAULT_HEADERS)
                for cv in as_completed([download_file(v.my_filename, dest_base, v.my_link, s) for v in vids_cur]):
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
