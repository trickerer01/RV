# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import sleep
from os import path, stat, remove, makedirs, listdir
from re import compile, sub, search, match
from typing import List

from aiohttp import ClientSession
from aiofile import async_open

from defs import (
    Log, CONNECT_RETRIES_ITEM, REPLACE_SYMBOLS, MAX_VIDEOS_QUEUE_SIZE, __RV_DEBUG__, SLASH, SITE_AJAX_REQUEST_VIDEO, QUALITY_UNK,
    DownloadResult
)
from fetch_html import fetch_html, get_proxy
from tagger import filtered_tags

downloads_queue = []  # type: List[int]
failed_items = []  # type: List[int]

re_rvfile = compile(r'^rv_([^_]+)_.*?(\d{3,4}p)?_py(?:dw|pv)\..+?$')


def is_queue_empty() -> bool:
    return len(downloads_queue) == 0


def is_queue_full() -> bool:
    return len(downloads_queue) >= MAX_VIDEOS_QUEUE_SIZE


def is_in_queue(idi: int) -> bool:
    return downloads_queue.count(idi) > 0


def normalize_filename(filename: str, dest_base: str) -> str:
    filename = sub(REPLACE_SYMBOLS, '_', filename)
    dest = dest_base.replace('\\', SLASH)
    if dest[-1] != SLASH:
        dest += SLASH
    dest += filename
    return dest


def extract_ext(href: str) -> str:
    try:
        return search(r'(\.[^&]{3,5})&', href).group(1)
    except Exception:
        return '.mp4'


async def try_register_in_queue(idi: int) -> bool:
    if is_in_queue(idi):
        if __RV_DEBUG__:
            Log(f'try_register_in_queue: {idi:d} is already in queue')
        return True
    elif not is_queue_full():
        downloads_queue.append(idi)
        if __RV_DEBUG__:
            Log(f'try_register_in_queue: {idi:d} added to queue')
        return True
    return False


async def try_unregister_from_queue(idi: int) -> None:
    try:
        downloads_queue.remove(idi)
        if __RV_DEBUG__:
            Log(f'try_unregister_from_queue: {idi:d} removed from queue')
    except (ValueError,):
        if __RV_DEBUG__:
            Log(f'try_unregister_from_queue: {idi:d} was not in queue')


async def download_id(idi: int, my_title: str, dest_base: str, req_quality: str, best_quality: bool, use_tags: bool,
                      excluded_tags: List[str], session: ClientSession) -> None:

    while not await try_register_in_queue(idi):
        await sleep(0.1)

    i_html = await fetch_html(SITE_AJAX_REQUEST_VIDEO % idi)
    if i_html:
        if i_html.find('title', string='404 Not Found'):
            Log(f'Got error 404 for id {idi:d}, skipping...')
            return await try_unregister_from_queue(idi)

        if my_title in [None, '']:
            titleh1 = i_html.find('h1', class_='title_video')
            if titleh1:
                my_title = titleh1.text
            else:
                my_title = 'unk'
        try:
            likespan = i_html.find('span', class_='voters count')
            likes = int(str(likespan.text[:max(likespan.text.find(' '), 0)]))
            my_score = f'{"+" if likes > 0 else ""}{likes:d}'
        except Exception:
            my_score = 'unk'
        ddiv = i_html.find('div', string='Download:')
        if not ddiv or not ddiv.parent:
            reason = 'probably an error'
            del_span = i_html.find('span', class_='message')
            if del_span:
                reason = f'reason: \'{str(del_span.text)}\''
            Log(f'Cannot find download section for {idi:d}, {reason}, skipping...')
            return await try_unregister_from_queue(idi)

        if use_tags is True or len(excluded_tags) > 0:
            tdiv = i_html.find('div', string='Tags:')
            if not tdiv or not tdiv.parent:
                Log(f'Cannot find tags section for {idi:d}, using title...')
            else:
                tags = tdiv.parent.find_all('a', class_='tag_item')
                if len(excluded_tags) > 0:
                    tags_raw = [str(tag.string) for tag in tags]
                    for exctag in excluded_tags:
                        if exctag in tags_raw:
                            Log(f'Video \'rv_{idi:d}.mp4\' contains excluded tag \'{exctag}\'. Skipped!')
                            return await try_unregister_from_queue(idi)
                if use_tags:
                    my_tags = filtered_tags(list(sorted(str(tag.string).lower().replace(' ', '_') for tag in tags)))
                    if my_tags != '':
                        my_title = my_tags

        links = ddiv.parent.find_all('a', class_='tag_item')
        qualities = []
        for lin in links:
            q = search(r'(\d+p)', str(lin.text))
            if q:
                qualities.append(q.group(1))

        if not (req_quality in qualities):
            q_idx = 0 if best_quality else -1
            if req_quality != QUALITY_UNK:
                Log(f'cannot find quality \'{req_quality}\' for {idi:d}, using \'{qualities[q_idx]}\'')
            req_quality = qualities[q_idx]
            link_idx = q_idx
        else:
            link_idx = qualities.index(req_quality)

        link = links[link_idx].get('href')
        part1 = f'rv_{idi:d}_score({my_score})_'
        part2 = f'_{req_quality}_pydw{extract_ext(link)}'
        while len(my_title) > max(0, 240 - (len(dest_base) + len(part1) + len(part2))):
            my_title = my_title[:max(0, my_title.rfind('_'))]

        filename = f'{part1}{my_title}{part2}'

        await download_file(idi, filename, dest_base, link, session)


async def download_file(idi: int, filename: str, dest_base: str, link: str, s: ClientSession) -> int:
    dest = normalize_filename(filename, dest_base)
    file_size = 0
    retries = 0
    ret = DownloadResult.DOWNLOAD_SUCCESS

    if not path.exists(dest_base):
        try:
            makedirs(dest_base)
        except Exception:
            raise IOError('ERROR: Unable to create subfolder!')
    else:
        # to check if file already exists we only take into account id and quality
        rv_match = match(re_rvfile, filename)
        rv_id = rv_match.group(1)
        rv_quality = rv_match.group(2)
        for fname in listdir(dest_base):
            try:
                f_match = match(re_rvfile, fname)
                f_id = f_match.group(1)
                f_quality = f_match.group(2)
                if rv_id == f_id and rv_quality == f_quality:
                    Log(f'{filename} (or similar) already exists. Skipped.')
                    await try_unregister_from_queue(idi)
                    return DownloadResult.DOWNLOAD_FAIL_ALREADY_EXISTS
            except Exception:
                continue

    while not await try_register_in_queue(idi):
        await sleep(0.1)

    # delay first batch just enough to not make anyone angry
    # we need this when downloading many small files (previews)
    await sleep(1.0 - min(0.9, 0.1 * len(downloads_queue)))

    # filename_short = 'rv_' + str(idi)
    # Log('Retrieving %s...' % filename_short)
    while (not (path.exists(dest) and file_size > 0)) and retries < CONNECT_RETRIES_ITEM:
        try:
            r = None
            # timeout must be relatively long, this is a timeout for actual download, not just connection
            async with s.request('GET', link, timeout=7200, proxy=get_proxy()) as r:
                if r.status == 404:
                    Log(f'Got 404 for {idi:d}...!')
                    retries = CONNECT_RETRIES_ITEM - 1
                    ret = DownloadResult.DOWNLOAD_FAIL_NOT_FOUND
                if r.content_type and r.content_type.find('text') != -1:
                    Log(f'File not found at {link}!')
                    raise FileNotFoundError(link)

                expected_size = r.content_length
                Log(f'Saving {(r.content_length / (1024.0 * 1024.0)) if r.content_length else 0.0:.2f} Mb to {filename}')

                async with async_open(dest, 'wb') as outf:
                    async for chunk in r.content.iter_chunked(2**20):
                        await outf.write(chunk)

                file_size = stat(dest).st_size
                if expected_size and file_size != expected_size:
                    Log(f'Error: file size mismatch for {filename}: {file_size:d} / {expected_size:d}')
                    raise IOError(link)
                break
        except (KeyboardInterrupt,):
            assert False
        except (Exception,):
            import sys
            print(sys.exc_info()[0], sys.exc_info()[1])
            retries += 1
            Log(f'{filename}: error #{retries:d}...')
            if r:
                r.close()
            if path.exists(dest):
                remove(dest)
            if retries >= CONNECT_RETRIES_ITEM and ret != DownloadResult.DOWNLOAD_FAIL_NOT_FOUND:
                failed_items.append(idi)
                break
            await sleep(1)
            continue

    # delay next file if queue is full
    if len(downloads_queue) == MAX_VIDEOS_QUEUE_SIZE:
        await sleep(0.25)

    await try_unregister_from_queue(idi)
    ret = (ret if ret == DownloadResult.DOWNLOAD_FAIL_NOT_FOUND else
           DownloadResult.DOWNLOAD_SUCCESS if retries < CONNECT_RETRIES_ITEM else
           DownloadResult.DOWNLOAD_FAIL_RETRIES)
    return ret

#
#
#########################################
