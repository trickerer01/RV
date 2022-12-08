# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import sleep
from os import path, stat, remove, makedirs, listdir
from re import compile, sub, search, match
from typing import List, Optional

from aiohttp import ClientSession
from aiofile import async_open

from defs import (
    Log, CONNECT_RETRIES_ITEM, REPLACE_SYMBOLS, MAX_VIDEOS_QUEUE_SIZE, __RV_DEBUG__, SLASH, SITE_AJAX_REQUEST_VIDEO,
    TAGS_CONCAT_CHAR, DownloadResult, DOWNLOAD_POLICY_ALWAYS, DOWNLOAD_MODE_TOUCH, normalize_path, get_elapsed_time_s, ExtraConfig,
)
from fetch_html import fetch_html, get_proxy
from scenario import DownloadScenario
from tagger import (
    filtered_tags, get_matching_tag, get_or_group_matching_tag, is_neg_and_group_matches, register_item_tags,
)

NEWLINE = '\n'
re_rvfile = compile(r'^rv_([^_]+)_.*?(\d{3,4}p)?_py(?:dw|pv)\..+?$')

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


def normalize_filename(filename: str, dest_base: str) -> str:
    filename = sub(REPLACE_SYMBOLS, '_', filename)
    dest = dest_base.replace('\\', SLASH)
    if dest[-1] != SLASH:
        dest += SLASH
    dest += filename
    return dest


def extract_ext(href: str) -> str:
    try:
        return search(r'(\.[^&]{3,5})&', href).group(1)
    except Exception:
        return '.mp4'


async def try_register_in_queue(idi: int) -> bool:
    if is_in_queue(idi):
        if __RV_DEBUG__:
            Log(f'try_register_in_queue: {idi:d} is already in queue')
        return True
    elif not is_queue_full():
        downloads_queue.append(idi)
        if __RV_DEBUG__:
            Log(f'try_register_in_queue: {idi:d} added to queue')
        return True
    return False


async def try_unregister_from_queue(idi: int) -> None:
    global total_queue_size
    try:
        downloads_queue.remove(idi)
        total_queue_size -= 1
        if __RV_DEBUG__:
            Log(f'try_unregister_from_queue: {idi:d} removed from queue')
    except (ValueError,):
        if __RV_DEBUG__:
            Log(f'try_unregister_from_queue: {idi:d} was not in queue')


async def report_total_queue_size_callback(base_sleep_time: float) -> None:
    global total_queue_size_last
    global download_queue_size_last
    while total_queue_size > 0:
        wait_time = base_sleep_time if total_queue_size > 1 else 1.0
        await sleep(wait_time)
        downloading_count = len(downloads_queue)
        queue_size = total_queue_size - downloading_count
        if total_queue_size_last != queue_size or (queue_size == 0 and download_queue_size_last != downloading_count):
            Log(f'[{get_elapsed_time_s()}] queue: {queue_size}, downloading: {downloading_count}')
            total_queue_size_last = queue_size
            download_queue_size_last = downloading_count


def is_filtered_out_by_extra_tags(idi: int, tags_raw: List[str], extra_tags: List[str], subfolder: str, do_log=True) -> bool:
    suc = True
    if len(extra_tags) > 0:
        for extag in extra_tags:
            if extag[0] == '(':
                if get_or_group_matching_tag(extag, tags_raw) is None:
                    suc = False
                    if do_log or ExtraConfig.verbose:
                        Log(f'[{subfolder}] Video \'rv_{idi:d}.mp4\' misses required tag matching \'{extag}\'!')
            elif extag.startswith('-('):
                if is_neg_and_group_matches(extag, tags_raw):
                    suc = False
                    if do_log or ExtraConfig.verbose:
                        Log(f'[{subfolder}] Video \'rv_{idi:d}.mp4\' contains excluded tags combination \'{extag[1:]}\'!')
            else:
                my_extag = extag[1:] if extag[0] == '-' else extag
                mtag = get_matching_tag(my_extag, tags_raw)
                if mtag is not None and extag[0] == '-':
                    suc = False
                    if do_log or ExtraConfig.verbose:
                        Log(f'[{subfolder}] Video \'rv_{idi:d}.mp4\' contains excluded tag \'{mtag}\'!')
                elif mtag is None and extag[0] != '-':
                    suc = False
                    if do_log or ExtraConfig.verbose:
                        Log(f'[{subfolder}] Video \'rv_{idi:d}.mp4\' misses required tag matching \'{my_extag}\'!')
    return not suc


def get_matching_scenario_subquery_idx(idi: int, tags_raw: List[str], scenario: DownloadScenario) -> int:
    for idx, sq in enumerate(scenario.queries):
        if not is_filtered_out_by_extra_tags(idi, tags_raw, sq.extra_tags, sq.subfolder, False):
            return idx
    return -1


def get_uvp_always_subquery_idx(scenario: DownloadScenario) -> int:
    for idx, sq in enumerate(scenario.queries):
        if sq.uvp == DOWNLOAD_POLICY_ALWAYS:
            return idx
    return -1


async def download_id(idi: int, my_title: str, dest_base: str, quality: str, scenario: Optional[DownloadScenario],
                      extra_tags: List[str], untagged_policy: str, download_mode: str, save_tags: bool, session: ClientSession) -> None:
    global current_ididx

    my_index = id_sequence.index(idi)
    while id_sequence[current_ididx] != idi:
        diff = abs(my_index - current_ididx)
        await sleep((0.1 * diff) if (diff < 100) else (10.0 + 0.05 * diff))

    while not await try_register_in_queue(idi):
        await sleep(1.5)

    await sleep(0.25)  # max 4 base requests per second

    current_ididx += 1

    my_subfolder = ''
    my_quality = quality
    my_tags = 'no_tags'
    likes = ''
    i_html = await fetch_html(SITE_AJAX_REQUEST_VIDEO % idi)
    if i_html:
        if i_html.find('title', string='404 Not Found'):
            Log(f'Got error 404 for id {idi:d}, skipping...')
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
            Log(f'Warning: cannot extract author for {idi:d}.')
            my_author = ''
        try:
            my_categories = [str(a.string).lower() for a in i_html.find('div', string='Categories:').parent.find_all('span')]
        except Exception:
            Log(f'Warning: cannot extract categories for {idi:d}.')
            my_categories = []
        try:
            tdiv = i_html.find('div', string='Tags:')
            tags = tdiv.parent.find_all('a', class_='tag_item')
            tags_raw = [str(tag.string).replace(' ', '_').lower() for tag in tags]
            for add_tag in [ca.replace(' ', '_') for ca in my_categories + [my_author] if len(ca) > 0]:
                if add_tag not in tags_raw:
                    tags_raw.append(add_tag)
            if is_filtered_out_by_extra_tags(idi, tags_raw, extra_tags, my_subfolder):
                Log(f'Info: video {idi:d} is filtered out by outer extra tags, skipping...')
                return await try_unregister_from_queue(idi)
            if scenario is not None:
                sub_idx = get_matching_scenario_subquery_idx(idi, tags_raw, scenario)
                if sub_idx == -1:
                    Log(f'Info: unable to find matching scenario subquery for {idi:d}, skipping...')
                    return await try_unregister_from_queue(idi)
                my_subfolder = scenario.queries[sub_idx].subfolder
                my_quality = scenario.queries[sub_idx].quality
            if save_tags:
                register_item_tags(idi, ' '.join(sorted(tags_raw)), my_subfolder)
            tags_str = filtered_tags(list(sorted(tags_raw)))
            if tags_str != '':
                my_tags = tags_str
        except Exception:
            if scenario is not None:
                uvp_idx = get_uvp_always_subquery_idx(scenario)
                if uvp_idx == -1:
                    Log(f'Warning: could not extract tags from id {idi:d}, skipping due to untagged videos download policy (scenario)...')
                    return await try_unregister_from_queue(idi)
                my_subfolder = scenario.queries[uvp_idx].subfolder
                my_quality = scenario.queries[uvp_idx].quality
            elif len(extra_tags) > 0 and untagged_policy != DOWNLOAD_POLICY_ALWAYS:
                Log(f'Warning: could not extract tags from id {idi:d}, skipping due to untagged videos download policy...')
                return await try_unregister_from_queue(idi)
            Log(f'Warning: could not extract tags from id {idi:d}...')

        tries = 0
        while True:
            ddiv = i_html.find('div', string='Download:')
            if ddiv is not None and ddiv.parent is not None:
                break
            reason = 'probably an error'
            del_span = i_html.find('span', class_='message')
            if del_span:
                reason = f'reason: \'{str(del_span.text)}\''
            Log(f'Cannot find download section for {idi:d}, {reason}, skipping...')
            tries += 1
            if tries >= 5:
                failed_items.append(idi)
                return await try_unregister_from_queue(idi)
            elif reason != 'probably an error':
                return await try_unregister_from_queue(idi)
            i_html = await fetch_html(SITE_AJAX_REQUEST_VIDEO % idi)

        links = ddiv.parent.find_all('a', class_='tag_item')
        qualities = []
        for lin in links:
            q = search(r'(\d+p)', str(lin.text))
            if q:
                qualities.append(q.group(1))

        if not (my_quality in qualities):
            q_idx = 0
            Log(f'cannot find quality \'{my_quality}\' for {idi:d}, using \'{qualities[q_idx]}\'')
            my_quality = qualities[q_idx]
            link_idx = q_idx
        else:
            link_idx = qualities.index(my_quality)

        link = links[link_idx].get('href')
    else:
        Log(f'Unable to retreive html for {idi:d}! Aborted!')
        return await try_unregister_from_queue(idi)

    my_dest_base = normalize_path(f'{dest_base}{my_subfolder}')
    my_score = f'+{likes}' if len(likes) > 0 else 'unk'
    fname_part1 = f'rv_{idi:d}_score({my_score}){f"_{my_title}" if my_title != "" else ""}'
    fname_part2 = f'{my_quality}_pydw{extract_ext(link)}'
    extra_len = 5 + 2 + 2  # 2 underscores + 2 brackets + len('2160p') - max len of all qualities
    while len(my_tags) > max(0, 240 - (len(my_dest_base) + len(fname_part1) + len(fname_part2) + extra_len)):
        my_tags = my_tags[:max(0, my_tags.rfind(TAGS_CONCAT_CHAR))]
    if len(my_tags) == 0 and len(fname_part1) > max(0, 240 - (len(my_dest_base) + len(fname_part2) + extra_len)):
        fname_part1 = fname_part1[:max(0, 240 - (len(my_dest_base) + len(fname_part2) + extra_len))]
    filename = f'{fname_part1}{f"_({my_tags})" if len(my_tags) > 0 else ""}_{fname_part2}'

    await download_file(idi, filename, my_dest_base, link, download_mode, session, True, my_subfolder)

    return await try_unregister_from_queue(idi)


async def download_file(idi: int, filename: str, dest_base: str, link: str, download_mode: str, s: ClientSession,
                        from_ids=False, subfolder='') -> int:
    dest = normalize_filename(filename, dest_base)
    sfilename = f'{f"{subfolder}/" if len(subfolder) > 0 else ""}{filename}'
    file_size = 0
    retries = 0
    ret = DownloadResult.DOWNLOAD_SUCCESS

    if not path.exists(dest_base):
        try:
            makedirs(dest_base)
        except Exception:
            raise IOError(f'ERROR: Unable to create subfolder \'{dest_base}\'!')
    else:
        # to check if file already exists we only take into account id and quality
        rv_match = match(re_rvfile, filename)
        rv_id = rv_match.group(1)
        rv_quality = rv_match.group(2)
        for fname in listdir(dest_base):
            try:
                f_match = match(re_rvfile, fname)
                f_id = f_match.group(1)
                f_quality = f_match.group(2)
                if rv_id == f_id and rv_quality == f_quality:
                    Log(f'{filename} (or similar) already exists. Skipped.')
                    if from_ids is False:
                        await try_unregister_from_queue(idi)
                    return DownloadResult.DOWNLOAD_FAIL_ALREADY_EXISTS
            except Exception:
                continue

    while not await try_register_in_queue(idi):
        await sleep(1.0)

    # delay first batch just enough to not make anyone angry
    # we need this when downloading many small files (previews)
    await sleep(1.0 - min(0.9, 0.1 * len(downloads_queue)))

    # filename_short = 'rv_' + str(idi)
    # Log('Retrieving %s...' % filename_short)
    while (not (path.exists(dest) and file_size > 0)) and retries < CONNECT_RETRIES_ITEM:
        try:
            if download_mode == DOWNLOAD_MODE_TOUCH:
                Log(f'Saving<touch> {0.0:.2f} Mb to {sfilename}')
                with open(dest, 'wb'):
                    pass
                break

            r = None
            # timeout must be relatively long, this is a timeout for actual download, not just connection
            async with s.request('GET', link, timeout=7200, proxy=get_proxy()) as r:
                if r.status == 404:
                    Log(f'Got 404 for {idi:d}...!')
                    retries = CONNECT_RETRIES_ITEM - 1
                    ret = DownloadResult.DOWNLOAD_FAIL_NOT_FOUND
                if r.content_type and r.content_type.find('text') != -1:
                    Log(f'File not found at {link}!')
                    raise FileNotFoundError(link)

                expected_size = r.content_length
                Log(f'Saving {(r.content_length / (1024.0 * 1024.0)) if r.content_length else 0.0:.2f} Mb to {sfilename}')

                async with async_open(dest, 'wb') as outf:
                    async for chunk in r.content.iter_chunked(2**20):
                        await outf.write(chunk)

                file_size = stat(dest).st_size
                if expected_size and file_size != expected_size:
                    Log(f'Error: file size mismatch for {sfilename}: {file_size:d} / {expected_size:d}')
                    raise IOError(link)
                break
        except (KeyboardInterrupt,):
            assert False
        except (Exception,):
            import sys
            print(sys.exc_info()[0], sys.exc_info()[1])
            retries += 1
            Log(f'{sfilename}: error #{retries:d}...')
            if r:
                r.close()
            if path.exists(dest):
                remove(dest)
            if retries >= CONNECT_RETRIES_ITEM and ret != DownloadResult.DOWNLOAD_FAIL_NOT_FOUND:
                failed_items.append(idi)
                break
            await sleep(1)
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
        Log('queue is not empty at exit!')

    if total_queue_size != 0:
        Log(f'total queue is still at {total_queue_size} != 0!')

    if len(failed_items) > 0:
        Log(f'Failed items:\n{NEWLINE.join(str(fi) for fi in sorted(failed_items))}')

#
#
#########################################
