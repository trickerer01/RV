# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import sys
from asyncio import run as run_async, as_completed, sleep, get_running_loop

from aiohttp import ClientSession, TCPConnector

from cmdargs import prepare_arglist_ids, read_cmdfile, is_parsed_cmdfile
from defs import Log, MAX_VIDEOS_QUEUE_SIZE, DEFAULT_HEADERS, DOWNLOAD_MODE_FULL, DOWNLOAD_POLICY_DEFAULT, DEFAULT_QUALITY, ExtraConfig
from download import download_id, after_download, report_total_queue_size_callback, register_id_sequence, scan_dest_folder
from tagger import try_parse_id_or_group, dump_item_tags, validate_tags


async def main() -> None:
    try:
        arglist = prepare_arglist_ids(sys.argv[1:])
        while is_parsed_cmdfile(arglist):
            arglist = prepare_arglist_ids(read_cmdfile(arglist.path))
    except Exception:
        Log.fatal(f'\nUnable to parse cmdline. Exiting.\n{sys.exc_info()[0]}: {sys.exc_info()[1]}')
        return

    try:
        ExtraConfig.read_params(arglist)
        start_id = arglist.start
        end_id = arglist.end
        ds = arglist.download_scenario

        if ExtraConfig.validate_tags:
            validate_tags(ExtraConfig.extra_tags)

        if arglist.use_id_sequence:
            id_sequence = try_parse_id_or_group(ExtraConfig.extra_tags)
            if id_sequence is None:
                Log.fatal(f'\nInvalid ID \'or\' group \'{ExtraConfig.extra_tags[0] if len(ExtraConfig.extra_tags) > 0 else ""}\'!')
                raise ValueError
        else:
            id_sequence = None
            if start_id > end_id:
                Log.fatal(f'\nError: start ({start_id:d}) > end ({end_id:d})')
                raise ValueError

        delay_for_message = False
        if ds:
            if ExtraConfig.uvp != DOWNLOAD_POLICY_DEFAULT:
                Log.info('Info: running download script, outer untagged policy will be ignored')
                ExtraConfig.uvp = DOWNLOAD_POLICY_DEFAULT
                delay_for_message = True
            if len(ExtraConfig.extra_tags) > 0:
                Log.info(f'Info: running download script: outer extra tags: {str(ExtraConfig.extra_tags)}')
                delay_for_message = True
            if ExtraConfig.quality != DEFAULT_QUALITY:
                Log.info('Info: running download script, outer quality setting will be ignored')
                delay_for_message = True

        if delay_for_message:
            await sleep(3.0)
    except Exception:
        Log.fatal('\nError reading parsed arglist!')
        return

    if id_sequence is None:
        id_sequence = list(range(start_id, end_id + 1))
    else:
        ExtraConfig.extra_tags = []

    register_id_sequence(id_sequence)
    scan_dest_folder()
    reporter = get_running_loop().create_task(report_total_queue_size_callback(3.0 if ExtraConfig.dm == DOWNLOAD_MODE_FULL else 1.0))
    async with ClientSession(connector=TCPConnector(limit=MAX_VIDEOS_QUEUE_SIZE), read_bufsize=2**20) as s:
        s.headers.update(DEFAULT_HEADERS.copy())
        for cv in as_completed([download_id(idi, '', ds, s) for idi in id_sequence]):
            await cv
    await reporter

    if ExtraConfig.save_tags:
        dump_item_tags()

    await after_download()


async def run_main() -> None:
    await main()
    await sleep(0.5)


if __name__ == '__main__':
    assert sys.version_info >= (3, 7), 'Minimum python version required is 3.7!'
    run_async(run_main())
    exit(0)

#
#
#########################################
