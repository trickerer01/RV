# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import sys
from asyncio import run as run_async, sleep
from typing import Optional

from cmdargs import prepare_arglist_ids, read_cmdfile, is_parsed_cmdfile
from defs import Log, ExtraConfig, HelpPrintExitException
from download import DownloadWorker, at_interrupt
from path_util import prefilter_existing_items, scan_dest_folder
from scenario import DownloadScenario
from tagger import try_parse_id_or_group
from validators import find_and_resolve_config_conflicts

__all__ = ()


async def main() -> None:
    try:
        arglist = prepare_arglist_ids(sys.argv[1:])
        while is_parsed_cmdfile(arglist):
            arglist = prepare_arglist_ids(read_cmdfile(arglist.path))
    except HelpPrintExitException:
        return
    except Exception:
        Log.fatal(f'\nUnable to parse cmdline. Exiting.\n{sys.exc_info()[0]}: {sys.exc_info()[1]}')
        return

    try:
        ExtraConfig.read_params(arglist)
        start_id = arglist.start  # type: int
        end_id = arglist.end  # type: int
        ds = arglist.download_scenario  # type: Optional[DownloadScenario]

        if arglist.use_id_sequence is True:
            id_sequence = try_parse_id_or_group(ExtraConfig.extra_tags)
            if id_sequence is None:
                Log.fatal(f'\nInvalid ID \'or\' group \'{ExtraConfig.extra_tags[0] if len(ExtraConfig.extra_tags) > 0 else ""}\'!')
                raise ValueError
        else:
            id_sequence = []
            if start_id > end_id:
                Log.fatal(f'\nError: start ({start_id:d}) > end ({end_id:d})')
                raise ValueError

        if find_and_resolve_config_conflicts(False, ds is not None) is True:
            await sleep(3.0)
    except Exception:
        Log.fatal('\nError reading parsed arglist!')
        return

    if len(id_sequence) == 0:
        id_sequence = list(range(start_id, end_id + 1))
    else:
        ExtraConfig.extra_tags.clear()

    orig_count = len(id_sequence)

    if len(id_sequence) > 0:
        scan_dest_folder()
        if ds is None:
            removed_ids = prefilter_existing_items(id_sequence)
            for i in reversed(range(len(id_sequence))):
                if id_sequence[i] in removed_ids:
                    del id_sequence[i]

    removed_count = orig_count - len(id_sequence)

    if len(id_sequence) == 0:
        if 0 < orig_count == removed_count:
            Log.fatal(f'\nAll {orig_count:d} videos already exist. Aborted.')
        else:
            Log.fatal('\nNo videos found. Aborted.')
        return

    minid, maxid = min(id_sequence), max(id_sequence)
    Log.info(f'\nOk! {len(id_sequence):d} ids in queue (+{removed_count:d} filtered out), bound {minid:d} to {maxid:d}. Working...\n')

    params = tuple((idi, '', ds) for idi in id_sequence)
    await DownloadWorker(params, True, removed_count).run()


async def run_main() -> None:
    await main()
    await sleep(0.5)


if __name__ == '__main__':
    assert sys.version_info >= (3, 7), 'Minimum python version required is 3.7!'
    try:
        run_async(run_main())
    except (KeyboardInterrupt, SystemExit):
        Log.warn('Warning: catched KeyboardInterrupt/SystemExit...')
        at_interrupt()
    exit(0)

#
#
#########################################
