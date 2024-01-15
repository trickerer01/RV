# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import sys
from asyncio import run as run_async, sleep
from typing import Sequence

from cmdargs import prepare_arglist, HelpPrintExitException
from config import Config
from download import download, at_interrupt
from logger import Log
from path_util import prefilter_existing_items
from tagger import try_parse_id_or_group
from util import at_startup
from validators import find_and_resolve_config_conflicts
from vinfo import VideoInfo

__all__ = ('main_sync',)


async def main(args: Sequence[str]) -> None:
    try:
        arglist = prepare_arglist(args, False)
    except HelpPrintExitException:
        return

    Config.read(arglist, False)

    if Config.use_id_sequence:
        Config.id_sequence = try_parse_id_or_group(Config.extra_tags)
        if not Config.id_sequence:
            Log.fatal('\nNo ID \'or\' group provided!' if not Config.extra_tags else
                      f'\nInvalid ID \'or\' group: \'{Config.extra_tags[0]}\'!' if len(Config.extra_tags) == 1 else
                      '\nID \'or\' group must be the only extra tag used!')
            raise ValueError
        Config.extra_tags.clear()
    else:
        Config.id_sequence = list(range(Config.start_id, Config.end_id + 1))

    if find_and_resolve_config_conflicts() is True:
        await sleep(3.0)

    v_entries = [VideoInfo(idi) for idi in Config.id_sequence]
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

    minid, maxid = min(v_entries, key=lambda x: x.my_id).my_id, max(v_entries, key=lambda x: x.my_id).my_id
    Log.info(f'\nOk! {len(v_entries):d} ids (+{removed_count:d} filtered out), bound {minid:d} to {maxid:d}. Working...\n')

    await download(v_entries, True, removed_count)


async def run_main(args: Sequence[str]) -> None:
    await main(args)
    await sleep(0.5)


def main_sync(args: Sequence[str]) -> None:
    assert sys.version_info >= (3, 7), 'Minimum python version required is 3.7!'

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
