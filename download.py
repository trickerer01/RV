# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import sleep
from os import path, stat, remove, makedirs
from re import sub, search
from typing import List

from aiohttp import ClientSession
from aiofile import async_open

from defs import Log, CONNECT_RETRIES_ITEM, REPLACE_SYMBOLS, DEFAULT_HEADERS, MAX_VIDEOS_QUEUE_SIZE, __RV_DEBUG__
from fetch_html import fetch_html


downloads_queue = []  # type: List[int]
failed_items = []  # type: List[int]


def is_queue_empty() -> bool:
    return len(downloads_queue) == 0


def is_queue_full() -> bool:
    return len(downloads_queue) >= MAX_VIDEOS_QUEUE_SIZE


def is_in_queue(idi: int) -> bool:
    return downloads_queue.count(idi) > 0


def normalize_filename(filename: str, dest_base: str) -> str:
    filename = sub(REPLACE_SYMBOLS, '_', filename)
    dest = dest_base.replace('\\', '/')
    if dest[-1] != '/':
        dest += '/'
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
            Log('try_register_in_queue: ', idi, ' is already in queue')
        return True
    elif not is_queue_full():
        downloads_queue.append(idi)
        if __RV_DEBUG__:
            Log('try_register_in_queue: ', idi, ' added to queue')
        return True
    return False


async def try_unregister_from_queue(idi: int) -> None:
    try:
        downloads_queue.remove(idi)
        if __RV_DEBUG__:
            Log('try_unregister_from_queue: ', idi, ' removed from queue')
    except (ValueError,):
        if __RV_DEBUG__:
            Log('try_unregister_from_queue: ', idi, 'was not in queue')


async def download_id(idi: int, my_href: str, my_title: str, dest_base: str,
                      req_quality: str = 'unknown', best_quality: bool = True,
                      session: ClientSession = None) -> None:

    while not await try_register_in_queue(idi):
        await sleep(0.1)

    i_html = await fetch_html(my_href)
    if i_html:
        ddiv = i_html.find('div', text='Download:')
        if not ddiv or not ddiv.parent:
            Log('cannot find download section for %d, skipping...' % idi)
            return await try_unregister_from_queue(idi)

        links = ddiv.parent.find_all('a', class_='tag_item')
        qualities = []
        for lin in links:
            q = search(r'(\d+0p)', lin.text)
            if q:
                qstr = q.group(1)
                qualities.append(qstr)

        if not (req_quality in qualities):
            q_idx = 0 if best_quality else -1
            if best_quality is False and req_quality != 'unknown':
                Log('cannot find proper quality for %d, using %s' % (idi, qualities[q_idx]))
            req_quality = qualities[q_idx]
            link_idx = q_idx
        else:
            link_idx = qualities.index(req_quality)

        link = links[link_idx].get('href')
        filename = 'rv_' + str(idi) + '_' + my_title + '_FULL_' + req_quality + '_pydw' + extract_ext(link)

        if session:
            await download_file(idi, filename, dest_base, link, session)
        else:
            async with ClientSession() as s:
                s.headers.update(DEFAULT_HEADERS)
                await download_file(idi, filename, dest_base, link, s)


async def download_file(idi: int, filename: str, dest_base: str, link: str, s: ClientSession) -> bool:
    dest = normalize_filename(filename, dest_base)
    file_size = 0
    retries = 0

    if path.exists(dest):
        file_size = stat(dest).st_size
        if file_size > 0:
            Log('%s already exists. Skipped.' % filename)
            await try_unregister_from_queue(idi)
            return False

    if not path.exists(dest_base):
        try:
            makedirs(dest_base)
        except Exception:
            raise IOError('ERROR: Unable to create subfolder!')

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
            async with s.request('GET', link, timeout=7200) as r:
                if r.content_type and r.content_type.find('text') != -1:
                    Log(('File not found at %s!' % link))
                    if retries >= 10:
                        failed_items.append(idi)
                        break
                    else:
                        raise FileNotFoundError(link)

                expected_size = r.content_length
                Log('Saving %.2f Mb to %s' % ((r.content_length / (1024.0 * 1024.0)) if r.content_length else 0.0, filename))

                async with async_open(dest, 'wb') as outf:
                    async for chunk in r.content.iter_chunked(2**20):
                        await outf.write(chunk)

                file_size = stat(dest).st_size
                if expected_size and file_size != expected_size:
                    Log('Error: file size mismatch for %s: %d / %d' % (filename, file_size, expected_size))
                    await try_unregister_from_queue(idi)
                    raise IOError
                break
        except (KeyboardInterrupt,):
            assert False
        except (Exception,):
            import sys
            print(sys.exc_info()[0], sys.exc_info()[1])
            retries += 1
            Log('%s: error #%d...' % (filename, retries))
            if r:
                r.close()
            if path.exists(dest):
                remove(dest)
            await sleep(1)
            continue

    # delay next file if queue is full
    if len(downloads_queue) == MAX_VIDEOS_QUEUE_SIZE:
        await sleep(0.25)

    await try_unregister_from_queue(idi)
    return retries < CONNECT_RETRIES_ITEM

#
#
#########################################
