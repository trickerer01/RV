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
from typing import List, Tuple

from aiohttp import ClientSession, TCPConnector

from cmdargs import prepare_arglist_pages
from defs import Log, SITE_AJAX_REQUEST_BASE, DEFAULT_HEADERS, MAX_VIDEOS_QUEUE_SIZE, MODE_BEST, MODE_LOWQ, QUALITY_UNK, NAMING_CHOICES
from download import download_file, download_id, after_download
from fetch_html import fetch_html, set_proxy


class VideoEntryBase:
    def __init__(self, m_id: int) -> None:
        self.my_id = m_id or 0


class VideoEntryFull(VideoEntryBase):
    def __init__(self, m_id: int, m_title: str) -> None:
        super().__init__(m_id)
        self.my_title = m_title or ''


class VideoEntryPrev(VideoEntryBase):
    def __init__(self, m_id: int, m_filename: str, m_link: str) -> None:
        super().__init__(m_id)
        self.my_filename = m_filename or ''
        self.my_link = m_link or ''


def get_minmax_ids(entry_list: List[VideoEntryBase]) -> Tuple[int, int]:
    minid = maxid = 0
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
        arglist = prepare_arglist_pages(argv[1:])
    except Exception:
        Log('\nUnable to parse cmdline. Exiting...')
        return

    try:
        dest_base = arglist.path
        start_page = arglist.start
        pages_count = arglist.pages
        do_full = arglist.mode
        stop_id = arglist.stop_id
        begin_id = arglist.begin_id
        search_str = arglist.search
        naming = arglist.naming
        up = arglist.untag_video_policy
        dm = arglist.download_mode
        extra_tags = arglist.extra_tags
        set_proxy(arglist.proxy if hasattr(arglist, 'proxy') else None)
        use_tags = naming == NAMING_CHOICES[1]
    except Exception:
        Log('\nError reading parsed arglist!')
        return

    vid_entries = list()
    maxpage = 0

    full_download = do_full in [MODE_BEST, MODE_LOWQ]
    pi = start_page
    while pi < start_page + pages_count:
        if pi > maxpage > 0:
            Log('reached parsed max page, page scan completed')
            break
        Log(f'page {pi:d}...{" (this is the last page!)" if 0 < maxpage == pi else ""}')

        a_html = await fetch_html(SITE_AJAX_REQUEST_BASE % (search_str, pi))
        if not a_html:
            Log(f'cannot get html for page {pi:d}')
            continue

        pi += 1

        if maxpage == 0:
            for page_ajax in a_html.find_all('a', attrs={'data-action': 'ajax'}):
                try:
                    maxpage = max(maxpage, int(search(r'from_albums:(\d+)', str(page_ajax.get('data-parameters'))).group(1)))
                except Exception:
                    pass

        if full_download:
            arefs = a_html.find_all('a', class_='th js-open-popup')
            for aref in arefs:
                cur_id = int(search(r'videos/(\d+)/', str(aref.get('href'))).group(1))  # cur_id = extract_id(aref)
                if cur_id < stop_id:
                    Log(f'skipping {cur_id:d} < {stop_id:d}')
                    continue
                if cur_id > begin_id:
                    Log(f'skipping {cur_id:d} > {begin_id:d}')
                    continue
                my_title = aref.get('title')
                already_queued = False
                for v in vid_entries:
                    if v.my_id == cur_id:
                        Log(f'Warning: id {cur_id:d} already queued, skipping')
                        already_queued = True
                        break
                if not already_queued:
                    vid_entries.append(VideoEntryFull(cur_id, my_title))
        else:
            content_div = a_html.find('div', class_='thumbs clearfix')

            if content_div is None:
                Log(f'cannot get content div for page {pi:d}')
                continue

            prev_all = content_div.find_all('div', class_='img wrap_image')
            titl_all = content_div.find_all('div', class_='thumb_title')
            cur_num = 1
            for i, p in enumerate(prev_all):
                cur_num += 1
                link = p.get('data-preview')
                name = titl_all[i].text
                v_id = search(r'/(\d+)_preview[^.]*?\.([^/]+)/', link)
                try:
                    cur_id, cur_ext = int(v_id.group(1)), str(v_id.group(2))
                except Exception:
                    cur_id, cur_ext = 1000000000, '.mp4'
                if cur_id < stop_id:
                    Log(f'skipping {cur_id:d} < {stop_id:d}')
                    continue
                already_queued = False
                for v in vid_entries:
                    if v.my_id == cur_id:
                        Log(f'Warning: id {cur_id:d} already queued, skipping')
                        already_queued = True
                        break
                if not already_queued:
                    vid_entries.append(VideoEntryPrev(cur_id, f'rv_{cur_id:d}_{name}_pypv.{cur_ext}', link))

    if len(vid_entries) == 0:
        Log('\nNo videos found. Aborted.')
        return

    minid, maxid = get_minmax_ids(vid_entries)
    Log(f'\nOk! {len(vid_entries):d} videos found, bound {minid:d} to {maxid:d}. Working...\n')
    vid_entries = list(reversed(vid_entries))
    async with ClientSession(connector=TCPConnector(limit=MAX_VIDEOS_QUEUE_SIZE), read_bufsize=2**20) as s:
        s.headers.update(DEFAULT_HEADERS.copy())
        if full_download:
            best = do_full == MODE_BEST
            for cv in as_completed(
                    [download_id(v.my_id, v.my_title, dest_base, QUALITY_UNK, best, use_tags, extra_tags, up, dm, s) for v in vid_entries]):
                await cv
        else:
            for cv in as_completed(
                    [download_file(v.my_id, v.my_filename, dest_base, v.my_link, dm, s) for v in vid_entries]):
                await cv

    await after_download()


async def run_main() -> None:
    await main()
    await sleep(0.5)


if __name__ == '__main__':
    run_async(run_main())
    exit(0)

#
#
#########################################
