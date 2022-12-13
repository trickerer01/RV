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
from download import download_id, after_download, report_total_queue_size_callback, register_id_sequence
from fetch_html import set_proxy
from tagger import try_parse_id_or_group, init_tags_files, dump_item_tags, validate_tags


async def main() -> None:
    try:
        arglist = prepare_arglist_ids(sys.argv[1:])
        while is_parsed_cmdfile(arglist):
            arglist = prepare_arglist_ids(read_cmdfile(arglist.path))
    except Exception:
        Log(f'\nUnable to parse cmdline. Exiting.\n{sys.exc_info()[0]}: {sys.exc_info()[1]}')
        return

    try:
        ExtraConfig.verbose = arglist.verbose
        ExtraConfig.min_score = arglist.minimum_score
        ExtraConfig.naming_flags = arglist.naming
        ExtraConfig.validate_tags = not arglist.no_validation

        dest_base = arglist.path
        start_id = arglist.start
        end_id = arglist.end
        quality = arglist.quality
        up = arglist.untag_video_policy
        dm = arglist.download_mode
        st = arglist.dump_tags
        ex_tags = arglist.extra_tags
        ds = arglist.download_scenario
        set_proxy(arglist.proxy)

        if ExtraConfig.validate_tags:
            validate_tags(ex_tags)

        if arglist.use_id_sequence:
            id_sequence = try_parse_id_or_group(ex_tags)
            if id_sequence is None:
                Log(f'\nInvalid ID \'or\' group \'{ex_tags[0] if len(ex_tags) > 0 else ""}\'!')
                raise ValueError
        else:
            id_sequence = None
            if start_id > end_id:
                Log(f'\nError: start ({start_id:d}) > end ({end_id:d})')
                raise ValueError

        delay_for_message = False
        if ds:
            if up != DOWNLOAD_POLICY_DEFAULT:
                Log('Info: running download script, outer untagged policy will be ignored')
                up = DOWNLOAD_POLICY_DEFAULT
                delay_for_message = True
            if len(ex_tags) > 0:
                Log(f'Info: running download script: outer extra tags: {str(ex_tags)}')
                delay_for_message = True
            if quality != DEFAULT_QUALITY:
                Log('Info: running download script, outer quality setting will be ignored')
                delay_for_message = True

        if delay_for_message:
            await sleep(3.0)
    except Exception:
        Log('\nError reading parsed arglist!')
        return

    if id_sequence is None:
        id_sequence = list(range(start_id, end_id + 1))
    else:
        ex_tags = []

    if st:
        init_tags_files(dest_base)
    register_id_sequence(id_sequence)
    reporter = get_running_loop().create_task(report_total_queue_size_callback(3.0 if dm == DOWNLOAD_MODE_FULL else 1.0))
    async with ClientSession(connector=TCPConnector(limit=MAX_VIDEOS_QUEUE_SIZE), read_bufsize=2**20) as s:
        s.headers.update(DEFAULT_HEADERS.copy())
        for cv in as_completed([download_id(idi, '', dest_base, quality, ds, ex_tags, up, dm, st, s) for idi in id_sequence]):
            await cv
    await reporter

    if st:
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
