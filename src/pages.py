# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import sys
from asyncio import run as run_async, sleep
from collections.abc import Sequence

from cmdargs import HelpPrintExitException, prepare_arglist
from config import Config
from defs import (
    NamingFlags, SITE_AJAX_REQUEST_SEARCH_PAGE, SITE_AJAX_REQUEST_UPLOADER_PAGE, SITE_AJAX_REQUEST_PLAYLIST_PAGE, PREFIX, QUALITIES,
    SITE_AJAX_REQUEST_FAVOURITES_PAGE, SITE_AJAX_REQUEST_MODEL_PAGE,
)
from download import download, at_interrupt
from fetch_html import create_session, fetch_html
from iinfo import VideoInfo
from logger import Log
from path_util import prefilter_existing_items
from rex import re_page_entry, re_paginator, re_preview_entry
from util import at_startup, has_naming_flag, get_time_seconds
from validators import find_and_resolve_config_conflicts
from version import APP_NAME

__all__ = ('main_sync',)


async def main(args: Sequence[str]) -> None:
    try:
        arglist = prepare_arglist(args, True)
    except HelpPrintExitException:
        return

    Config.read(arglist, True)

    full_download = Config.quality != QUALITIES[-1]
    video_ref_class = 'th' if Config.playlist_name else 'th js-open-popup'

    if find_and_resolve_config_conflicts(full_download) is True:
        await sleep(3.0)

    def check_id_bounds(video_id: int) -> int:
        if video_id > Config.end_id:
            Log.trace(f'skipping {video_id:d} > {Config.end_id:d}')
            return 1
        if video_id < Config.start_id:
            Log.trace(f'skipping {video_id:d} < {Config.start_id:d}')
            return -1
        return 0

    v_entries = list()
    maxpage = Config.end if Config.start == Config.end else 0

    pi = Config.start
    async with create_session():
        while pi <= Config.end:
            if pi > maxpage > 0:
                Log.info('reached parsed max page, page scan completed')
                break

            page_addr = (
                (SITE_AJAX_REQUEST_PLAYLIST_PAGE % (Config.playlist_id, Config.playlist_name, pi)) if Config.playlist_name else
                (SITE_AJAX_REQUEST_FAVOURITES_PAGE % (Config.favourites, pi)) if Config.favourites else
                (SITE_AJAX_REQUEST_UPLOADER_PAGE % (Config.uploader, pi)) if Config.uploader else
                (SITE_AJAX_REQUEST_MODEL_PAGE % (Config.model, pi)) if Config.model else
                (SITE_AJAX_REQUEST_SEARCH_PAGE % (Config.search_tags, Config.search_arts, Config.search_cats, Config.search, pi))
            )
            a_html = await fetch_html(page_addr)
            if not a_html:
                Log.error(f'Error: cannot get html for page {pi:d}')
                continue

            pi += 1

            if maxpage == 0:
                for page_ajax in a_html.find_all('a', attrs={'data-action': 'ajax'}):
                    try:
                        maxpage = max(maxpage, int(re_paginator.search(str(page_ajax.get('data-parameters'))).group(1)))
                    except Exception:
                        pass
                if maxpage == 0:
                    Log.info('Could not extract max page, assuming single page search')
                    maxpage = 1
                else:
                    Log.debug(f'Extracted max page: {maxpage:d}')

            if Config.get_maxid:
                mirefs = a_html.find_all('a', class_=video_ref_class)
                max_id = max(int(re_page_entry.search(str(_.get('href'))).group(1)) for _ in mirefs)
                Log.fatal(f'{APP_NAME}: {max_id:d}')
                return

            Log.info(f'page {pi - 1:d}...{" (this is the last page!)" if (0 < maxpage == pi - 1) else ""}')

            lower_count = 0
            if full_download:
                arefs = a_html.find_all('a', class_=video_ref_class)
                orig_count = len(arefs)
                for aref in arefs:
                    try:  # some post previews may be invalid
                        cur_id = int(re_page_entry.search(str(aref.get('href'))).group(1))
                    except Exception:
                        continue
                    bound_res = check_id_bounds(cur_id)
                    if bound_res != 0:
                        if bound_res < 0:
                            lower_count += 1
                        continue
                    elif cur_id in v_entries:
                        Log.warn(f'Warning: id {cur_id:d} already queued, skipping')
                        continue
                    my_title = str(aref.find('div', class_='thumb_title').text)
                    my_utitle = str(aref['href'][:-1][aref['href'][:-1].rfind('/') + 1:])
                    my_duration = get_time_seconds(str(aref.find('div', class_='time').text))
                    use_utitle = has_naming_flag(NamingFlags.USE_URL_TITLE)
                    v_entries.append(VideoInfo(cur_id, my_utitle if use_utitle else my_title, m_duration=my_duration))
            else:
                content_div = a_html.find('div', class_='thumbs clearfix')

                if content_div is None:
                    Log.error(f'Error: cannot get content div for page {pi:d}')
                    continue

                prev_all = content_div.find_all('div', class_='img wrap_image')
                titl_all = content_div.find_all('div', class_='thumb_title')
                utitl_all = content_div.find_all('a', class_='th js-open-popup')
                orig_count = len(prev_all)
                for i, p in enumerate(prev_all):
                    link = str(p.get('data-preview'))
                    title = str(titl_all[i].text)
                    urltitle = str(utitl_all[i]['href'][:-1][utitl_all[i]['href'][:-1].rfind('/') + 1:])
                    v_id = re_preview_entry.search(link)
                    cur_id, cur_ext = int(v_id.group(1)), str(v_id.group(2))
                    bound_res = check_id_bounds(cur_id)
                    if bound_res != 0:
                        if bound_res < 0:
                            lower_count += 1
                        continue
                    elif cur_id in v_entries:
                        Log.warn(f'Warning: id {cur_id:d} already queued, skipping')
                        continue
                    use_prefix = has_naming_flag(NamingFlags.PREFIX)
                    use_title = has_naming_flag(NamingFlags.TITLE)
                    use_utitle = has_naming_flag(NamingFlags.USE_URL_TITLE)
                    v_entries.append(VideoInfo(
                        cur_id, '', link, '', f'{PREFIX if use_prefix else ""}{cur_id:d}'
                        f'{f"_{urltitle if use_utitle else title}" if use_title else ""}_preview.{cur_ext}',
                    ))

            if pi - 1 > Config.start and lower_count == orig_count > 0 and not Config.scan_all_pages:
                if maxpage == 0 or pi - 1 < maxpage:
                    Log.info(f'Page {pi - 1:d} has all post ids below lower bound. Pages scan stopped!')
                break

        v_entries.reverse()
        orig_count = len(v_entries)

        if orig_count > 0:
            prefilter_existing_items(v_entries)

        removed_count = orig_count - len(v_entries)

        if orig_count == removed_count:
            if orig_count > 0:
                Log.fatal(f'\nAll {orig_count:d} videos already exist. Aborted.')
            else:
                Log.fatal('\nNo videos found. Aborted.')
            return

        await download(v_entries, full_download, removed_count)


async def run_main(args: Sequence[str]) -> None:
    await main(args)
    await sleep(0.5)


def main_sync(args: Sequence[str]) -> None:
    assert sys.version_info >= (3, 9), 'Minimum python version required is 3.9!'

    try:
        run_async(run_main(args))
    except (KeyboardInterrupt, SystemExit):
        Log.warn('Warning: catched KeyboardInterrupt/SystemExit...')
    finally:
        at_interrupt()


if __name__ == '__main__':
    at_startup()
    main_sync(sys.argv[1:])
    exit(0)

#
#
#########################################
