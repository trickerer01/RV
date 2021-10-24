# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from os import path, stat
from re import sub
from time import sleep

from aiohttp import ClientSession

from defs import Log, CONNECT_RETRIES_ITEM, REPLACE_SYMBOLS


def normalize_filename(filename: str, dest_base: str) -> str:
    filename = sub(REPLACE_SYMBOLS, '_', filename)
    dest = dest_base.replace('\\', '/')
    if dest[-1] != '/':
        dest += '/'
    dest += filename
    return dest


async def download_file(filename: str, dest_base: str, link: str, s: ClientSession) -> bool:
    dest = normalize_filename(filename, dest_base)
    file_size = 0
    retries = 0

    if path.exists(dest):
        file_size = stat(dest).st_size
        if file_size > 0:
            Log('%s already exists. Skipped.' % filename)
            return False

    Log('Retrieving %s...' % filename)
    while (not (path.exists(dest) and file_size > 0)) and retries < CONNECT_RETRIES_ITEM:
        try:
            async with s.request('GET', link, timeout=7200) as r:
                Log('%s: reading %d bytes' % (filename, r.content_length or -1))
                content = await r.read()

                Log('Saving to %s' % dest)
                with open(dest, 'wb') as outf:
                    outf.write(content)
                file_size = stat(dest).st_size
                break
        except (KeyboardInterrupt,):
            assert False
        except (Exception,):
            import sys
            print(sys.exc_info()[0], sys.exc_info()[1])
            retries += 1
            Log('error #%d...' % retries)
            sleep(1)
            continue

    return retries < CONNECT_RETRIES_ITEM


"""
def download_file(filename: str, dest_base: str, link: str, s: Session) -> bool:
    dest = normalize_filename(filename, dest_base)
    file_size = 0
    retries = 0

    if path.exists(dest):
        file_size = stat(dest).st_size
        if file_size > 0:
            Log('%s already exists. Skipped.' % filename)
            return False

    Log('Retrieving %s...' % filename)
    while (not (path.exists(dest) and file_size > 0)) and retries < CONNECT_RETRIES_ITEM:
        try:
            r = s.request('GET', link, timeout=CONNECT_DELAY_PAGE, stream=False, allow_redirects=True)
            r.raise_for_status()
            content = r.content

            Log('Saving to %s' % dest)
            with open(dest, 'wb') as outf:
                outf.write(content)
            file_size = stat(dest).st_size
            break
        except (KeyboardInterrupt,):
            assert False
        except (Exception, HTTPError,):
            retries += 1
            Log('error #%d...' % retries)
            sleep(1)
            continue

    return retries < CONNECT_RETRIES_ITEM
"""

#
#
#########################################
