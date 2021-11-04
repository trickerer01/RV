# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from os import path, stat, remove
from re import sub
from time import sleep

from aiohttp import ClientSession
from aiofile import async_open

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
            expected_size = r.content_length
            async with s.request('GET', link, timeout=7200) as r:
                # Log('%s: reading %d bytes' % (filename, r.content_length or -1))
                Log('Saving %d bytes to %s' % (r.content_length or -1, filename))
                # content = await r.read()

                async with async_open(dest, 'wb') as outf:
                    async for chunk in r.content.iter_chunked(2**20):
                        await outf.write(chunk)
                # with open(dest, 'wb') as outf:
                #     outf.write(content)
                file_size = stat(dest).st_size
                if expected_size and file_size != expected_size:
                    Log('Error: file size mismatch for %s: %d / %d' % (filename, file_size, expected_size))
                    raise IOError
                break
        except (KeyboardInterrupt,):
            assert False
        except (Exception,):
            import sys
            print(sys.exc_info()[0], sys.exc_info()[1])
            retries += 1
            Log('%s: error #%d...' % (filename, retries))
            r.close()
            remove(dest)
            sleep(1)
            continue

    return retries < CONNECT_RETRIES_ITEM

#
#
#########################################
