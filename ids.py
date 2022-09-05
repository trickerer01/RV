# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import run as run_async, sleep, as_completed
from re import search
from sys import argv
from typing import Any, Tuple, List

from aiohttp import ClientSession, TCPConnector

from cmdargs import prepare_arglist_ids
from defs import Log, SITE_AJAX_REQUEST_BASE, MAX_VIDEOS_QUEUE_SIZE
from download import download_id, failed_items
from fetch_html import fetch_html, set_proxy


def extract_id(aref: Any) -> int:
    return int(search(r'videos/(\d+)/', str(aref.get('href'))).group(1))


def get_minmax_ids(arefs: list) -> Tuple[List[int], int, int]:
    ids = []  # type: List[int]
    for aref in arefs:
        ids.append(extract_id(aref))
    return (ids, min(ids), max(ids))


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
        set_proxy(arglist.proxy if hasattr(arglist, 'proxy') else None)

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
        for cv in as_completed([download_id(idi, '', dest_base, req_quality, True, s) for idi in range(start_id, end_id + 1)]):
            await cv

    if len(failed_items) > 0:
        failed_items.sort()
        Log('Failed items:')
        for fi in failed_items:
            Log(' ', str(fi))


async def run_main():
    await main()
    await sleep(0.5)


if __name__ == '__main__':
    run_async(run_main())
    # Log('Searching by ID is disabled, reason: Buggy, videos are not properly sorted by id, meking binary search mostly useless')
    exit(0)

#
#
#########################################
