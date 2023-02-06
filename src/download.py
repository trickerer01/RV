# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import sleep
from os import path, stat, remove, makedirs, listdir
from random import uniform as frand
from re import compile as re_compile, match, search
from typing import List, Optional, Set

from aiohttp import ClientSession
from aiofile import async_open

from defs import (
    CONNECT_RETRIES_ITEM, MAX_VIDEOS_QUEUE_SIZE, SITE_AJAX_REQUEST_VIDEO, TAGS_CONCAT_CHAR,
    DownloadResult, DOWNLOAD_POLICY_ALWAYS, DOWNLOAD_MODE_TOUCH, NAMING_FLAG_PREFIX, NAMING_FLAG_SCORE, NAMING_FLAG_TITLE, NAMING_FLAG_TAGS,
    Log, ExtraConfig, normalize_path, normalize_filename, get_elapsed_time_s, has_naming_flag, prefixp, LoggingFlags, extract_ext
)
from fetch_html import fetch_html, wrap_request
from scenario import DownloadScenario
from tagger import (
    filtered_tags, get_matching_tag, get_or_group_matching_tag, is_neg_and_group_matches, register_item_tags,
)

__all__ = ('download_id', 'download_file', 'after_download', 'report_total_queue_size_callback', 'register_id_sequence', 'scan_dest_folder')

NEWLINE = '\n'
re_rvfile = re_compile(r'^(?:rv_)?(\d+)_.*?(\d{3,4}p)?_py(?:dw|pv)\..+?$')

found_filenames_base = set()  # type: Set[str]
found_filenames_all = set()  # type: Set[str]
downloads_queue = []  # type: List[int]
failed_items = []  # type: List[int]
total_queue_size = 0
total_queue_size_last = 0
download_queue_size_last = 0
id_sequence = []  # type: List[int]
current_ididx = 0


def register_id_sequence(id_seq: List[int]) -> None:
    global id_sequence
    global total_queue_size
    id_sequence = id_seq
    total_queue_size = len(id_sequence)


def is_queue_empty() -> bool:
    return len(downloads_queue) == 0


def is_queue_full() -> bool:
    return len(downloads_queue) >= MAX_VIDEOS_QUEUE_SIZE


def is_in_queue(idi: int) -> bool:
    return downloads_queue.count(idi) > 0


async def try_register_in_queue(idi: int) -> bool:
    if is_in_queue(idi):
        Log.debug(f'try_register_in_queue: {prefixp()}{idi:d}.mp4 is already in queue')
        return True
    elif not is_queue_full():
        downloads_queue.append(idi)
        Log.debug(f'try_register_in_queue: {prefixp()}{idi:d}.mp4 added to queue')
        return True
    return False


async def try_unregister_from_queue(idi: int) -> None:
    global total_queue_size
    try:
        downloads_queue.remove(idi)
        total_queue_size -= 1
        Log.debug(f'try_unregister_from_queue: {prefixp()}{idi:d}.mp4 removed from queue')
    except (ValueError,):
        Log.debug(f'try_unregister_from_queue: {prefixp()}{idi:d}.mp4 was not in queue')


async def report_total_queue_size_callback(base_sleep_time: float) -> None:
    global total_queue_size_last
    global download_queue_size_last
    while total_queue_size > 0:
        wait_time = base_sleep_time if total_queue_size > 1 else 1.0
        await sleep(wait_time)
        downloading_count = len(downloads_queue)
        queue_size = total_queue_size - downloading_count
        if total_queue_size_last != queue_size or (queue_size == 0 and download_queue_size_last != downloading_count):
            Log.info(f'[{get_elapsed_time_s()}] queue: {queue_size}, downloading: {downloading_count}')
            total_queue_size_last = queue_size
            download_queue_size_last = downloading_count


def is_filtered_out_by_extra_tags(idi: int, tags_raw: List[str], extra_tags: List[str], subfolder: str) -> bool:
    suc = True
    if len(extra_tags) > 0:
        for extag in extra_tags:
            if extag[0] == '(':
                if get_or_group_matching_tag(extag, tags_raw) is None:
                    suc = False
                    Log.trace(f'[{subfolder}] Video \'{prefixp()}{idi:d}.mp4\' misses required tag matching \'{extag}\'!',
                              LoggingFlags.LOGGING_EX_MISSING_TAGS)
            elif extag.startswith('-('):
                if is_neg_and_group_matches(extag, tags_raw):
                    suc = False
                    Log.info(f'[{subfolder}] Video \'{prefixp()}{idi:d}.mp4\' contains excluded tags combination \'{extag[1:]}\'!',
                             LoggingFlags.LOGGING_EX_EXCLUDED_TAGS)
            else:
                my_extag = extag[1:] if extag[0] == '-' else extag
                mtag = get_matching_tag(my_extag, tags_raw)
                if mtag is not None and extag[0] == '-':
                    suc = False
                    Log.info(f'[{subfolder}] Video \'{prefixp()}{idi:d}.mp4\' contains excluded tag \'{mtag}\'!',
                             LoggingFlags.LOGGING_EX_EXCLUDED_TAGS)
                elif mtag is None and extag[0] != '-':
                    suc = False
                    Log.trace(f'[{subfolder}] Video \'{prefixp()}{idi:d}.mp4\' misses required tag matching \'{my_extag}\'!',
                              LoggingFlags.LOGGING_EX_MISSING_TAGS)
    return not suc


def get_matching_scenario_subquery_idx(idi: int, tags_raw: List[str], likes: str, scenario: DownloadScenario) -> int:
    for idx, sq in enumerate(scenario.queries):
        if not is_filtered_out_by_extra_tags(idi, tags_raw, sq.extra_tags, sq.subfolder):
            if len(likes) > 0:
                try:
                    if int(likes) < sq.minscore:
                        Log.info(f'[{sq.subfolder}] Video \'{prefixp()}{idi:d}.mp4\''
                                 f' has low score \'{int(likes):d}\' (required {sq.minscore:d})!',
                                 LoggingFlags.LOGGING_EX_LOW_SCORE)
                        continue
                except Exception:
                    pass
            return idx
    return -1


def get_uvp_always_subquery_idx(scenario: DownloadScenario) -> int:
    for idx, sq in enumerate(scenario.queries):
        if sq.uvp == DOWNLOAD_POLICY_ALWAYS:
            return idx
    return -1


def scan_dest_folder() -> None:
    global found_filenames_base
    global found_filenames_all

    if path.exists(ExtraConfig.dest_base):
        Log.info('Scanning dest folder...')
        subfolders = list()
        cur_names = listdir(ExtraConfig.dest_base)
        for idx_c in reversed(range(len(cur_names))):
            fullpath_c = f'{ExtraConfig.dest_base}{cur_names[idx_c]}'
            if path.isdir(fullpath_c):
                subfolders.append(normalize_path(fullpath_c))
                del cur_names[idx_c]
            elif path.isfile(fullpath_c):
                found_filenames_all.add(cur_names[idx_c])
        found_filenames_base = cur_names
        for subfolder in subfolders:
            for sub_name in listdir(subfolder):
                fullpath_s = f'{subfolder}{sub_name}'
                if path.isfile(fullpath_s):
                    found_filenames_all.add(sub_name)
        Log.info(f'Found {len(found_filenames_base):d} files in base and '
                 f'{len(found_filenames_all) - len(found_filenames_base):d} files in {len(subfolders):d} subfolders '
                 f'(total files: {len(found_filenames_all):d})')


def file_exists_in_folder(base_folder: str, idi: int, quality: str, check_subfolders: bool) -> bool:
    if path.exists(base_folder):
        for fname in sorted(found_filenames_all if check_subfolders else found_filenames_base):
            try:
                f_match = match(re_rvfile, fname)
                f_id = f_match.group(1)
                f_quality = f_match.group(2)
                if str(idi) == f_id and quality == f_quality:
                    return True
            except Exception:
                continue
    return False


async def download_id(idi: int, my_title: str, scenario: Optional[DownloadScenario], session: ClientSession) -> None:
    global current_ididx

    my_index = id_sequence.index(idi)
    while id_sequence[current_ididx] != idi:
        diff = abs(my_index - current_ididx)
        await sleep((0.1 * diff) if (diff < 100) else (10.0 + 0.05 * diff))

    while not await try_register_in_queue(idi):
        await sleep(1.5)

    current_ididx += 1

    if file_exists_in_folder(ExtraConfig.dest_base, idi, ExtraConfig.quality, True):
        Log.info(f'download_id: {prefixp()}{idi:d}.mp4 (or similar) found in {ExtraConfig.dest_base} (or subfolder). Skipped.')
        return await try_unregister_from_queue(idi)

    my_subfolder = ''
    my_quality = ExtraConfig.quality
    my_tags = 'no_tags'
    likes = ''
    i_html = await fetch_html(f'{SITE_AJAX_REQUEST_VIDEO % idi}?popup_id={2 + current_ididx % 10:d}', session=session)
    if i_html:
        if i_html.find('title', string='404 Not Found'):
            Log.error(f'Got error 404 for {prefixp()}{idi:d}.mp4, skipping...')
            return await try_unregister_from_queue(idi)

        if my_title in [None, '']:
            titleh1 = i_html.find('h1', class_='title_video')
            if titleh1:
                my_title = titleh1.text
            else:
                my_title = ''
        try:
            likespan = i_html.find('span', class_='voters count')
            likes = str(likespan.text[:max(likespan.text.find(' '), 0)])
        except Exception:
            pass
        try:
            my_author = str(i_html.find('div', string='Artist:').parent.find('span').string).lower()
        except Exception:
            Log.warn(f'Warning: cannot extract author for {prefixp()}{idi:d}.mp4.')
            my_author = ''
        try:
            my_categories = [str(a.string).lower() for a in i_html.find('div', string='Categories:').parent.find_all('span')]
        except Exception:
            Log.warn(f'Warning: cannot extract categories for {prefixp()}{idi:d}.mp4.')
            my_categories = []
        try:
            tdiv = i_html.find('div', string='Tags:')
            tags = tdiv.parent.find_all('a', class_='tag_item')
            tags_raw = [str(tag.string).replace(' ', '_').lower() for tag in tags]
            for add_tag in [ca.replace(' ', '_') for ca in my_categories + [my_author] if len(ca) > 0]:
                if add_tag not in tags_raw:
                    tags_raw.append(add_tag)
            if is_filtered_out_by_extra_tags(idi, tags_raw, ExtraConfig.extra_tags, my_subfolder):
                Log.info(f'Info: video {prefixp()}{idi:d}.mp4 is filtered out by outer extra tags, skipping...')
                return await try_unregister_from_queue(idi)
            if len(likes) > 0:
                try:
                    if int(likes) < ExtraConfig.min_score:
                        Log.info(f'Info: video {prefixp()}{idi:d}.mp4'
                                 f' has low score \'{int(likes):d}\' (required {ExtraConfig.min_score:d}), skipping...')
                        return await try_unregister_from_queue(idi)
                except Exception:
                    pass
            if scenario is not None:
                sub_idx = get_matching_scenario_subquery_idx(idi, tags_raw, likes, scenario)
                if sub_idx == -1:
                    Log.info(f'Info: unable to find matching scenario subquery for {prefixp()}{idi:d}.mp4, skipping...')
                    return await try_unregister_from_queue(idi)
                my_subfolder = scenario.queries[sub_idx].subfolder
                my_quality = scenario.queries[sub_idx].quality
            if ExtraConfig.save_tags:
                register_item_tags(idi, ' '.join(sorted(tags_raw)), my_subfolder)
            tags_str = filtered_tags(list(sorted(tags_raw)))
            if tags_str != '':
                my_tags = tags_str
        except Exception:
            if scenario is not None:
                uvp_idx = get_uvp_always_subquery_idx(scenario)
                if uvp_idx == -1:
                    Log.warn(f'Warning: could not extract tags from {prefixp()}{idi:d}.mp4, '
                             f'skipping due to untagged videos download policy (scenario)...')
                    return await try_unregister_from_queue(idi)
                my_subfolder = scenario.queries[uvp_idx].subfolder
                my_quality = scenario.queries[uvp_idx].quality
            elif len(ExtraConfig.extra_tags) > 0 and ExtraConfig.uvp != DOWNLOAD_POLICY_ALWAYS:
                Log.warn(f'Warning: could not extract tags from {prefixp()}{idi:d}.mp4, skipping due to untagged videos download policy...')
                return await try_unregister_from_queue(idi)
            Log.warn(f'Warning: could not extract tags from {prefixp()}{idi:d}.mp4...')

        tries = 0
        while True:
            ddiv = i_html.find('div', string='Download:')
            if ddiv is not None and ddiv.parent is not None:
                break
            reason = 'probably an error'
            del_span = i_html.find('span', class_='message')
            if del_span:
                reason = f'reason: \'{str(del_span.text)}\''
            Log.error(f'Cannot find download section for {prefixp()}{idi:d}.mp4, {reason}, skipping...')
            tries += 1
            if tries >= 5:
                failed_items.append(idi)
                return await try_unregister_from_queue(idi)
            elif reason != 'probably an error':
                return await try_unregister_from_queue(idi)
            i_html = await fetch_html(SITE_AJAX_REQUEST_VIDEO % idi, session=session)

        links = ddiv.parent.find_all('a', class_='tag_item')
        qualities = []
        for lin in links:
            q = search(r'(\d+p)', str(lin.text))
            if q:
                qualities.append(q.group(1))

        if not (my_quality in qualities):
            q_idx = 0
            Log.warn(f'Warning: cannot find quality \'{my_quality}\' for {prefixp()}{idi:d}.mp4, using \'{qualities[q_idx]}\'')
            my_quality = qualities[q_idx]
            link_idx = q_idx
        else:
            link_idx = qualities.index(my_quality)

        link = links[link_idx].get('href')
    else:
        Log.error(f'Error: unable to retreive html for {prefixp()}{idi:d}.mp4! Aborted!')
        failed_items.append(idi)
        return await try_unregister_from_queue(idi)

    my_dest_base = normalize_path(f'{ExtraConfig.dest_base}{my_subfolder}')
    my_score = f'+{likes}' if len(likes) > 0 else 'unk'
    extra_len = 5 + 2 + 2  # 2 underscores + 2 brackets + len('2160p') - max len of all qualities
    fname_part2 = f'{my_quality}_pydw{extract_ext(link)}'
    fname_part1 = (
        f'{prefixp() if has_naming_flag(NAMING_FLAG_PREFIX) else ""}'
        f'{idi:d}'
        f'{f"_score({my_score})" if has_naming_flag(NAMING_FLAG_SCORE) else ""}'
        f'{f"_{my_title}" if my_title != "" and has_naming_flag(NAMING_FLAG_TITLE) else ""}'
    )
    if has_naming_flag(NAMING_FLAG_TAGS):
        while len(my_tags) > max(0, 240 - (len(my_dest_base) + len(fname_part1) + len(fname_part2) + extra_len)):
            my_tags = my_tags[:max(0, my_tags.rfind(TAGS_CONCAT_CHAR))]
        fname_part1 = f'{fname_part1}{f"_({my_tags})" if len(my_tags) > 0 else ""}'

    if len(my_tags) == 0 and len(fname_part1) > max(0, 240 - (len(my_dest_base) + len(fname_part2) + extra_len)):
        fname_part1 = fname_part1[:max(0, 240 - (len(my_dest_base) + len(fname_part2) + extra_len))]
    filename = f'{fname_part1}_{fname_part2}'

    await download_file(idi, filename, my_dest_base, link, session, True, my_subfolder)

    return await try_unregister_from_queue(idi)


async def download_file(idi: int, filename: str, my_dest_base: str, link: str, s: ClientSession, from_ids=False, subfolder='') -> int:
    dest = normalize_filename(filename, my_dest_base)
    sfilename = f'{f"{subfolder}/" if len(subfolder) > 0 else ""}{filename}'
    file_size = 0
    retries = 0
    ret = DownloadResult.DOWNLOAD_SUCCESS

    if not path.exists(my_dest_base):
        try:
            makedirs(my_dest_base)
        except Exception:
            raise IOError(f'ERROR: Unable to create subfolder \'{my_dest_base}\'!')
    else:
        rv_match = match(re_rvfile, filename)
        rv_quality = rv_match.group(2)
        if file_exists_in_folder(my_dest_base, idi, rv_quality, False):
            Log.info(f'{filename} (or similar) already exists. Skipped.')
            if from_ids is False:
                await try_unregister_from_queue(idi)
            return DownloadResult.DOWNLOAD_FAIL_ALREADY_EXISTS

    while not await try_register_in_queue(idi):
        await sleep(1.0)

    # delay first batch just enough to not make anyone angry
    # we need this when downloading many small files (previews)
    await sleep(1.0 - min(0.9, 0.1 * len(downloads_queue)))

    # filename_short = 'rv_' + str(idi)
    # Log('Retrieving %s...' % filename_short)
    while (not (path.exists(dest) and file_size > 0)) and retries < CONNECT_RETRIES_ITEM:
        try:
            if ExtraConfig.dm == DOWNLOAD_MODE_TOUCH:
                Log.info(f'Saving<touch> {0.0:.2f} Mb to {sfilename}')
                with open(dest, 'wb'):
                    pass
                break

            r = None
            # timeout must be relatively long, this is a timeout for actual download, not just connection
            async with await wrap_request(s, 'GET', link, timeout=7200, headers={'Referer': link}) as r:
                if r.status == 404:
                    Log.error(f'Got 404 for {prefixp()}{idi:d}.mp4...!')
                    retries = CONNECT_RETRIES_ITEM - 1
                    ret = DownloadResult.DOWNLOAD_FAIL_NOT_FOUND
                if r.content_type and r.content_type.find('text') != -1:
                    Log.error(f'File not found at {link}!')
                    raise FileNotFoundError(link)

                expected_size = r.content_length
                Log.info(f'Saving {(r.content_length / (1024.0 * 1024.0)) if r.content_length else 0.0:.2f} Mb to {sfilename}')

                async with async_open(dest, 'wb') as outf:
                    async for chunk in r.content.iter_chunked(2**20):
                        await outf.write(chunk)

                file_size = stat(dest).st_size
                if expected_size and file_size != expected_size:
                    Log.error(f'Error: file size mismatch for {sfilename}: {file_size:d} / {expected_size:d}')
                    raise IOError(link)
                break
        except (KeyboardInterrupt,):
            assert False
        except (Exception,):
            import sys
            print(sys.exc_info()[0], sys.exc_info()[1])
            if r is None or r.status != 403:
                retries += 1
                Log.error(f'{sfilename}: error #{retries:d}...')
            if r:
                r.close()
            if path.exists(dest):
                remove(dest)
            if retries >= CONNECT_RETRIES_ITEM and ret != DownloadResult.DOWNLOAD_FAIL_NOT_FOUND:
                failed_items.append(idi)
                break
            await sleep(frand(1.0, 7.0))
            continue

    # delay next file if queue is full
    if len(downloads_queue) == MAX_VIDEOS_QUEUE_SIZE:
        await sleep(0.25)

    ret = (ret if ret == DownloadResult.DOWNLOAD_FAIL_NOT_FOUND else
           DownloadResult.DOWNLOAD_SUCCESS if retries < CONNECT_RETRIES_ITEM else
           DownloadResult.DOWNLOAD_FAIL_RETRIES)
    if from_ids is False:
        await try_unregister_from_queue(idi)
    return ret


async def after_download() -> None:
    if not is_queue_empty():
        Log.error('queue is not empty at exit!')

    if total_queue_size != 0:
        Log.error(f'total queue is still at {total_queue_size} != 0!')

    if len(failed_items) > 0:
        Log.error(f'Failed items:\n{NEWLINE.join(str(fi) for fi in sorted(failed_items))}')

#
#
#########################################
