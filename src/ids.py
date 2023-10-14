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

from cmdargs import prepare_arglist_ids, read_cmdfile, is_parsed_cmdfile
from defs import Log, Config, HelpPrintExitException, at_startup
from download import download, at_interrupt
from path_util import prefilter_existing_items
from tagger import try_parse_id_or_group
from validators import find_and_resolve_config_conflicts
from vinfo import VideoInfo

__all__ = ('main_sync',)


async def main(args: Sequence[str]) -> None:
    try:
        arglist = prepare_arglist_ids(args)
        while is_parsed_cmdfile(arglist):
            arglist = prepare_arglist_ids(read_cmdfile(arglist.path))
    except HelpPrintExitException:
        return
    except Exception:
        Log.fatal(f'\nUnable to parse cmdline. Exiting.\n{sys.exc_info()[0]}: {sys.exc_info()[1]}')
        return
    finally:
        at_startup()

    try:
        Config.read(arglist, False)

        if arglist.use_id_sequence is True:
            id_sequence = try_parse_id_or_group(Config.extra_tags)
            if len(id_sequence) == 0:
                Log.fatal(f'\nInvalid ID \'or\' group \'{Config.extra_tags[0] if len(Config.extra_tags) > 0 else ""}\'!')
                raise ValueError
        else:
            id_sequence = list()
            if Config.start_id > Config.end_id:
                Log.fatal(f'\nError: invalid video id bounds: start ({Config.start_id:d}) > end ({Config.end_id:d})')
                raise ValueError

        if find_and_resolve_config_conflicts() is True:
            await sleep(3.0)
    except Exception:
        Log.fatal('\nError reading parsed arglist!')
        return

    if len(id_sequence) == 0:
        id_sequence = list(range(Config.start_id, Config.end_id + 1))
    else:
        Config.extra_tags.clear()

    v_entries = [VideoInfo(idi) for idi in id_sequence]
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

    await download(v_entries, True, removed_count)


async def run_main(args: Sequence[str]) -> None:
    await main(args)
    await sleep(0.5)


def main_sync(args: Sequence[str]) -> None:
    assert sys.version_info >= (3, 7), 'Minimum python version required is 3.7!'

    interrupted = False
    try:
        run_async(run_main(args))
    except (KeyboardInterrupt, SystemExit):
        Log.warn('Warning: catched KeyboardInterrupt/SystemExit...')
        interrupted = True
    except Exception:
        interrupted = True
    finally:
        if interrupted:
            at_interrupt()


if __name__ == '__main__':
    main_sync(sys.argv[1:])
    exit(0)

#
#
#########################################
