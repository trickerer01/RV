# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import sleep

from .config import Config
from .download import download
from .fetch_html import create_session
from .iinfo import VideoInfo
from .logger import Log
from .path_util import prefilter_existing_items
from .tagger import extract_id_or_group, extract_ids_from_links
from .validators import find_and_resolve_config_conflicts

__all__ = ('process_ids',)


async def process_ids() -> int:
    if Config.use_id_sequence:
        Config.id_sequence = extract_id_or_group(Config.extra_tags)
        if not Config.id_sequence:
            Log.fatal('\nNo ID \'or\' group provided!' if not Config.extra_tags else
                      f'\nNo valid ID \'or\' group found in \'{Config.extra_tags!s}\'!')
            raise ValueError
        Log.info(f'Parsed ids sequence of length {len(Config.id_sequence):d}')
    elif Config.use_link_sequence:
        Config.id_sequence = extract_ids_from_links(Config.extra_tags)
        if not Config.id_sequence:
            Log.fatal('\nNo links provided!' if not Config.extra_tags else
                      f'\nNo valid links found in \'{Config.extra_tags!s}\'!')
            raise ValueError
        Log.info(f'Parsed {len(Config.id_sequence):d} links')
    else:
        Config.id_sequence = list(range(Config.start, Config.end + 1))

    if find_and_resolve_config_conflicts() is True:
        await sleep(3.0)

    orig_sequence_len = len(Config.id_sequence)
    removed_ids = set[int]()
    ridx: int
    for ridx in reversed(range(len(Config.id_sequence))):
        if 236 <= Config.id_sequence[ridx] <= 3045049:
            if not removed_ids:
                Log.warn('Warning: found ids known to be non-existent. Erasing from sequence...')
            removed_ids.add(Config.id_sequence[ridx])
            del Config.id_sequence[ridx]
    if removed_ids:
        Log.warn(f'Removed {len(removed_ids):d} / {orig_sequence_len:d} known to be non-existent ids!')

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
        return -1

    async with create_session():
        await download(v_entries, True, removed_count)

    return 0

#
#
#########################################
