# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import run as run_async, sleep, as_completed
from sys import argv

from aiohttp import ClientSession, TCPConnector

from cmdargs import prepare_arglist_ids
from defs import Log, SITE_AJAX_REQUEST_BASE, MAX_VIDEOS_QUEUE_SIZE, NAMING_CHOICES
from download import download_id, after_download
from fetch_html import fetch_html, set_proxy


async def main() -> None:
    try:
        arglist = prepare_arglist_ids(argv[1:])
    except Exception:
        Log('\nUnable to parse cmdline. Exiting...')
        return

    try:
        dest_base = arglist.path
        start_id = arglist.start
        end_id = arglist.end
        req_quality = arglist.quality
        naming = arglist.naming
        extra_tags = arglist.extra_tags
        set_proxy(arglist.proxy if hasattr(arglist, 'proxy') else None)
        use_tags = naming == NAMING_CHOICES[1]

        if start_id > end_id:
            Log(f'\nError: start ({start_id:d}) > end ({end_id:d})')
            raise ValueError
    except Exception:
        Log('\nError reading parsed arglist!')
        return

    # pages
    a_html = await fetch_html(SITE_AJAX_REQUEST_BASE % ('', 1))
    if not a_html:
        Log('cannot connect')
        return

    async with ClientSession(connector=TCPConnector(limit=MAX_VIDEOS_QUEUE_SIZE), read_bufsize=2**20) as s:
        for cv in as_completed(
                [download_id(idi, '', dest_base, req_quality, True, use_tags, extra_tags, s) for idi in range(start_id, end_id + 1)]):
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
