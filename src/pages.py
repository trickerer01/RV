# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import sys
from asyncio import run as run_async, sleep
from re import compile as re_compile

from cmdargs import prepare_arglist_pages, read_cmdfile, is_parsed_cmdfile
from defs import (
    VideoInfo, Log, ExtraConfig, SITE_AJAX_REQUEST_PAGE, QUALITIES, SEARCH_RULE_ALL, has_naming_flag, prefixp, NamingFlags,
    HelpPrintExitException,
)
from download import download, at_interrupt
from path_util import prefilter_existing_items
from fetch_html import make_session, fetch_html
from validators import find_and_resolve_config_conflicts

__all__ = ()


async def main() -> None:
    try:
        arglist = prepare_arglist_pages(sys.argv[1:])
        while is_parsed_cmdfile(arglist):
            arglist = prepare_arglist_pages(read_cmdfile(arglist.path))
    except HelpPrintExitException:
        return
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
        search_tags = arglist.search_tag  # type: str
        search_arts = arglist.search_art  # type: str
        search_cats = arglist.search_cat  # type: str
        search_rule_tag = arglist.search_rule_tag  # type: str
        search_rule_art = arglist.search_rule_art  # type: str
        search_rule_cat = arglist.search_rule_cat  # type: str

        full_download = ExtraConfig.quality != QUALITIES[-1]
        re_page_entry = re_compile(r'videos/(\d+)/')
        re_preview_entry = re_compile(r'/(\d+)_preview[^.]*?\.([^/]+)/')
        re_paginator = re_compile(r'from_albums:(\d+)')

        if search_tags.find(',') != -1 and search_rule_tag == SEARCH_RULE_ALL:
            search_tags = f'{SEARCH_RULE_ALL},{search_tags}'
        if search_arts.find(',') != -1 and search_rule_art == SEARCH_RULE_ALL:
            search_arts = f'{SEARCH_RULE_ALL},{search_arts}'
        if search_cats.find(',') != -1 and search_rule_cat == SEARCH_RULE_ALL:
            search_cats = f'{SEARCH_RULE_ALL},{search_cats}'

        if find_and_resolve_config_conflicts(full_download) is True:
            await sleep(3.0)
    except Exception:
        Log.fatal('\nError reading parsed arglist!')
        return

    v_entries = list()
    maxpage = 0

    pi = start_page
    async with await make_session() as s:
        while pi < start_page + pages_count:
            if pi > maxpage > 0:
                Log.info('reached parsed max page, page scan completed')
                break
            Log.info(f'page {pi:d}...{" (this is the last page!)" if (0 < maxpage == pi) else ""}')

            a_html = await fetch_html(SITE_AJAX_REQUEST_PAGE % (search_tags, search_arts, search_cats, search_str, pi), session=s)
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

            if full_download:
                arefs = a_html.find_all('a', class_='th js-open-popup')
                for aref in arefs:
                    cur_id = int(re_page_entry.search(str(aref.get('href'))).group(1))
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
                        v_entries.append(VideoInfo(cur_id, my_title))
            else:
                content_div = a_html.find('div', class_='thumbs clearfix')

                if content_div is None:
                    Log.error(f'Error: cannot get content div for page {pi:d}')
                    continue

                prev_all = content_div.find_all('div', class_='img wrap_image')
                titl_all = content_div.find_all('div', class_='thumb_title')
                for i, p in enumerate(prev_all):
                    link = str(p.get('data-preview'))
                    title = str(titl_all[i].text)
                    v_id = re_preview_entry.search(link)
                    cur_id, cur_ext = int(v_id.group(1)), str(v_id.group(2))
                    if cur_id < stop_id:
                        Log.trace(f'skipping {cur_id:d} < {stop_id:d}')
                        continue
                    if cur_id in v_entries:
                        Log.warn(f'Warning: id {cur_id:d} already queued, skipping')
                    else:
                        v_entries.append(
                            VideoInfo(
                                cur_id, '', link, '', f'{prefixp() if has_naming_flag(NamingFlags.NAMING_FLAG_PREFIX) else ""}{cur_id:d}'
                                f'{f"_{title}" if has_naming_flag(NamingFlags.NAMING_FLAG_TITLE) else ""}_preview.{cur_ext}',
                            ))

        v_entries.reverse()
        orig_count = len(v_entries)

        if len(v_entries) > 0:
            prefilter_existing_items(v_entries)

        removed_count = orig_count - len(v_entries)

        if len(v_entries) == 0:
            if 0 < orig_count == removed_count:
                Log.fatal(f'\nAll {orig_count:d} videos already exist. Aborted.')
            else:
                Log.fatal('\nNo videos found. Aborted.')
            return

        minid, maxid = min(v_entries, key=lambda x: x.my_id).my_id, max(v_entries, key=lambda x: x.my_id).my_id
        Log.info(f'\nOk! {len(v_entries):d} ids (+{removed_count:d} filtered out), bound {minid:d} to {maxid:d}. Working...\n')

        await download(v_entries, full_download, removed_count, s)


async def run_main() -> None:
    await main()
    await sleep(0.5)


if __name__ == '__main__':
    assert sys.version_info >= (3, 7), 'Minimum python version required is 3.7!'

    interrupted = False
    try:
        run_async(run_main())
    except (KeyboardInterrupt, SystemExit):
        Log.warn('Warning: catched KeyboardInterrupt/SystemExit...')
        interrupted = True
    except Exception:
        interrupted = True
    finally:
        if interrupted:
            at_interrupt()
    exit(0)

#
#
#########################################
