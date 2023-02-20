# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import sys
from asyncio import run as run_async, sleep
from re import search
from typing import List, Tuple

from aiohttp import ClientSession, TCPConnector

from cmdargs import prepare_arglist_pages, read_cmdfile, is_parsed_cmdfile
from defs import Log, MAX_VIDEOS_QUEUE_SIZE, ExtraConfig, SITE_AJAX_REQUEST_BASE, QUALITIES, has_naming_flag, prefixp, NamingFlags
from download import DownloadWorker, at_interrupt
from path_util import prefilter_existing_items
from fetch_html import fetch_html
from scenario import DownloadScenario
from tagger import validate_tags
from validators import find_and_resolve_config_conflicts

__all__ = ()


class VideoEntryBase:
    def __init__(self, m_id: int) -> None:
        self.my_id = m_id or 0

    def __eq__(self, other) -> bool:
        return self.my_id == other.my_id if isinstance(other, type(self)) else self.my_id == other if isinstance(other, int) else False


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
        arglist = prepare_arglist_pages(sys.argv[1:])
        while is_parsed_cmdfile(arglist):
            arglist = prepare_arglist_pages(read_cmdfile(arglist.path))
    except Exception:
        Log.fatal(f'\nUnable to parse cmdline. Exiting.\n{sys.exc_info()[0]}: {sys.exc_info()[1]}')
        return

    try:
        ExtraConfig.read_params(arglist)
        start_page = arglist.start  # type: int
        pages_count = arglist.pages  # type: int
        stop_id = arglist.stop_id  # type: int
        begin_id = arglist.begin_id  # type: int
        search_str = arglist.search  # type: str
        ds = arglist.download_scenario  # type: DownloadScenario

        if ExtraConfig.validate_tags is True:
            validate_tags(ExtraConfig.extra_tags)

        full_download = ExtraConfig.quality != QUALITIES[-1]

        if find_and_resolve_config_conflicts(True, ds is not None, full_download) is True:
            await sleep(3.0)
    except Exception:
        Log.fatal('\nError reading parsed arglist!')
        return

    v_entries = list()
    maxpage = 0

    pi = start_page
    async with ClientSession(connector=TCPConnector(limit=MAX_VIDEOS_QUEUE_SIZE), read_bufsize=2**20) as s:
        while pi < start_page + pages_count:
            if pi > maxpage > 0:
                Log.info('reached parsed max page, page scan completed')
                break
            Log.info(f'page {pi:d}...{" (this is the last page!)" if 0 < maxpage == pi else ""}')

            a_html = await fetch_html(SITE_AJAX_REQUEST_BASE % (search_str, pi), session=s)
            if not a_html:
                Log.error(f'Error: cannot get html for page {pi:d}')
                continue

            pi += 1

            if maxpage == 0:
                for page_ajax in a_html.find_all('a', attrs={'data-action': 'ajax'}):
                    try:
                        maxpage = max(maxpage, int(search(r'from_albums:(\d+)', str(page_ajax.get('data-parameters'))).group(1)))
                    except Exception:
                        pass
                if maxpage == 0:
                    Log.info('Could not extract max page, assuming single page search')
                    maxpage = 1

            if full_download:
                arefs = a_html.find_all('a', class_='th js-open-popup')
                for aref in arefs:
                    cur_id = int(search(r'videos/(\d+)/', str(aref.get('href'))).group(1))
                    if cur_id < stop_id:
                        Log.trace(f'skipping {cur_id:d} < {stop_id:d}')
                        continue
                    if cur_id > begin_id:
                        Log.trace(f'skipping {cur_id:d} > {begin_id:d}')
                        continue
                    my_title = str(aref.get('title'))
                    if cur_id in v_entries:
                        Log.warn(f'Warning: id {cur_id:d} already queued, skipping')
                    else:
                        v_entries.append(VideoEntryFull(cur_id, my_title))
            else:
                content_div = a_html.find('div', class_='thumbs clearfix')

                if content_div is None:
                    Log.error(f'Error: cannot get content div for page {pi:d}')
                    continue

                prev_all = content_div.find_all('div', class_='img wrap_image')
                titl_all = content_div.find_all('div', class_='thumb_title')
                cur_num = 1
                for i, p in enumerate(prev_all):
                    cur_num += 1
                    link = str(p.get('data-preview'))
                    title = str(titl_all[i].text)
                    v_id = search(r'/(\d+)_preview[^.]*?\.([^/]+)/', link)
                    cur_id, cur_ext = int(v_id.group(1)), str(v_id.group(2))
                    if cur_id < stop_id:
                        Log.trace(f'skipping {cur_id:d} < {stop_id:d}')
                        continue
                    if cur_id in v_entries:
                        Log.warn(f'Warning: id {cur_id:d} already queued, skipping')
                    else:
                        v_entries.append(
                            VideoEntryPrev(cur_id,
                                           f'{prefixp() if has_naming_flag(NamingFlags.NAMING_FLAG_PREFIX) else ""}{cur_id:d}'
                                           f'{f"_{title}" if has_naming_flag(NamingFlags.NAMING_FLAG_TITLE) else ""}_pypv.{cur_ext}', link))

        if len(v_entries) == 0:
            Log.fatal('\nNo videos found. Aborted.')
            return

        minid, maxid = get_minmax_ids(v_entries)
        Log.info(f'\nOk! {len(v_entries):d} videos found, bound {minid:d} to {maxid:d}. Working...\n')
        v_entries = list(reversed(v_entries))

        prefilter_existing_items(v_entries)

        await DownloadWorker(
            ((v.my_id, v.my_title, ds) if full_download else (v.my_id, v.my_filename, ExtraConfig.dest_base, v.my_link) for v in v_entries),
            full_download, s).run()


async def run_main() -> None:
    await main()
    await sleep(0.5)


if __name__ == '__main__':
    assert sys.version_info >= (3, 7), 'Minimum python version required is 3.7!'
    try:
        run_async(run_main())
    except (KeyboardInterrupt, SystemExit):
        Log.warn(f'Warning: catched KeyboardInterrupt/SystemExit...')
        at_interrupt()
    exit(0)

#
#
#########################################
