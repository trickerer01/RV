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

from defs import Log, SITE_AJAX_REQUEST_BASE, DEFAULT_HEADERS, MAX_VIDEOS_QUEUE_SIZE
from download import download_file, download_id, is_queue_empty, failed_items
from fetch_html import fetch_html
from ids import extract_id


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
        print('Syntax: Destination StartPage [NumPages] [Full] [StopId] [Search_string]'
              '\n destination: str\n startpage: int\n numpages(1): int\n full(0): int[0(preview), 1(full), 2(full lowq)]\n stopid(1): int'
              '\n search_string: str')
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

    try:
        search_str = str(argv[6])
    except Exception:
        search_str = ''

    vid_entries = list()
    maxpage = 0

    full_download = do_full in [1, 2]
    for pi in range(start_page, start_page + pages_count):
        if maxpage and pi > maxpage:
            Log('reached parsed max page, page scan completed')
            break
        Log(('page %d...%s' % (pi, ' (this is the last page!)' if maxpage and pi == maxpage else '')))

        a_html = await fetch_html(SITE_AJAX_REQUEST_BASE % (search_str, pi))
        if not a_html:
            Log('cannot get html for page %d', pi)
            continue

        if maxpage == 0:
            for page_ajax in a_html.find_all('a', attrs={'data-action': 'ajax'}):
                try:
                    data_params = str(page_ajax.get('data-parameters'))
                    maxpage = max(maxpage, int(search(r'from_albums:(\d+)', data_params).group(1)))
                except Exception:
                    pass

        if full_download:
            arefs = a_html.find_all('a', class_='th js-open-popup')
            for aref in arefs:
                cur_id = extract_id(aref)
                if cur_id < stop_id:
                    Log('skipping %d < %d' % (cur_id, stop_id))
                    continue
                my_href = aref.get('href')
                my_title = aref.get('title')
                vid_entries.append(VideoEntryFull(cur_id, my_href, my_title))
        else:
            content_div = a_html.find('div', class_='thumbs clearfix')

            if content_div is None:
                Log(('cannot get content div for page %d' % pi))
                continue

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
    async with ClientSession(connector=TCPConnector(limit=MAX_VIDEOS_QUEUE_SIZE), read_bufsize=2**20) as s:
        s.headers.update(DEFAULT_HEADERS)
        if full_download:
            best = (do_full == 1)
            for cv in as_completed([download_id(v.my_id, v.my_href, v.my_title, dest_base, 'unknown', best, s) for v in vid_entries]):
                await cv
        else:
            for cv in as_completed([download_file(v.my_id, v.my_filename, dest_base, v.my_link, s) for v in vid_entries]):
                await cv

    if not is_queue_empty():
        Log('pages: queue is not empty at exit!')

    if len(failed_items) > 0:
        Log('Failed items:')
        for fi in failed_items:
            Log(' ', str(fi))


async def run_main():
    await main()
    await sleep(0.25)


if __name__ == '__main__':
    run_async(run_main())
    exit(0)

#
#
#########################################
