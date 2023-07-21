# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import sleep, get_running_loop, Task, CancelledError
from os import path, stat, remove, makedirs
from random import uniform as frand
from typing import Optional, MutableSequence

from aiofile import async_open
from aiohttp import ClientSession, ClientTimeout, ClientResponse

from defs import (
    CONNECT_RETRIES_ITEM, SITE_AJAX_REQUEST_VIDEO, DOWNLOAD_POLICY_ALWAYS, DOWNLOAD_MODE_TOUCH, DOWNLOAD_STATUS_CHECK_TIMER,
    TAGS_CONCAT_CHAR, VideoInfo, Log, ExtraConfig, DownloadResult, NamingFlags, has_naming_flag, prefixp, extract_ext,
    re_media_filename,
)
from downloader import DownloadWorker
from fetch_html import fetch_html, wrap_request
from path_util import file_already_exists
from scenario import DownloadScenario
from tagger import filtered_tags, register_item_tags, is_filtered_out_by_extra_tags

__all__ = ('download', 'at_interrupt')

CTOD = ClientTimeout(total=None, connect=10)
"""Client timeout (download)"""


async def download(sequence: MutableSequence[VideoInfo], by_id: bool, filtered_count: int, session: ClientSession = None) -> None:
    return await DownloadWorker(sequence, (download_file, download_id)[by_id], filtered_count, session).run()


async def download_id(vi: VideoInfo) -> DownloadResult:
    dwn = DownloadWorker.get()
    scenario = ExtraConfig.scenario  # type: Optional[DownloadScenario]
    sname = f'{prefixp()}{vi.my_id:d}.mp4'
    my_tags = 'no_tags'
    rating = vi.my_rating
    score = ''

    vi.set_state(VideoInfo.VIState.ACTIVE)
    i_html = await fetch_html(f'{SITE_AJAX_REQUEST_VIDEO % vi.my_id}?popup_id={2 + vi.my_id % 10:d}', session=dwn.session)
    if i_html is None:
        Log.error(f'Error: unable to retreive html for {sname}! Aborted!')
        return DownloadResult.DOWNLOAD_FAIL_RETRIES

    if i_html.find('title', string='404 Not Found'):
        Log.error(f'Got error 404 for {sname}, skipping...')
        return DownloadResult.DOWNLOAD_FAIL_SKIPPED

    if vi.my_title in (None, ''):
        titleh1 = i_html.find('h1', class_='title_video')
        vi.my_title = titleh1.text if titleh1 else ''
    try:
        dislikes_int = 0
        likes_int = int(i_html.find('span', class_='voters count').text.replace(' likes', ''))
        rating = f'{(likes_int * 100) // (dislikes_int + likes_int):d}' if (dislikes_int + likes_int) > 999999 else rating
        score = f'{likes_int - dislikes_int:d}'
    except Exception:
        pass
    try:
        my_authors = [str(a.string).lower() for a in i_html.find('div', string='Artist:').parent.find_all('span')]
    except Exception:
        Log.warn(f'Warning: cannot extract authors for {sname}.')
        my_authors = list()
    try:
        my_categories = [str(c.string).lower() for c in i_html.find('div', string='Categories:').parent.find_all('span')]
    except Exception:
        Log.warn(f'Warning: cannot extract categories for {sname}.')
        my_categories = list()
    tdiv = i_html.find('div', string='Tags:')
    if tdiv is None:
        Log.info(f'Warning: video {sname} has no tags!')
    tags = [str(elem.string) for elem in tdiv.parent.find_all('a', class_='tag_item')] if tdiv else ['']
    tags_raw = [tag.replace(' ', '_').lower() for tag in tags if len(tag) > 0]
    for add_tag in [ca.replace(' ', '_') for ca in my_categories + my_authors if len(ca) > 0]:
        if add_tag not in tags_raw:
            tags_raw.append(add_tag)
    if is_filtered_out_by_extra_tags(vi.my_id, tags_raw, ExtraConfig.extra_tags, False, vi.my_subfolder):
        Log.info(f'Info: video {sname} is filtered out by{" outer" if scenario is not None else ""} extra tags, skipping...')
        return DownloadResult.DOWNLOAD_FAIL_SKIPPED
    if len(score) > 0 and ExtraConfig.min_score is not None:
        try:
            if int(score) < ExtraConfig.min_score:
                Log.info(f'Info: video {sname} has low score \'{score}\' (required {ExtraConfig.min_score:d}), skipping...')
                return DownloadResult.DOWNLOAD_FAIL_SKIPPED
        except Exception:
            pass
    if len(rating) > 0:
        try:
            if int(rating) < ExtraConfig.min_rating:
                Log.info(f'Info: video {sname} has low rating \'{rating}%\' (required {ExtraConfig.min_rating:d}%), skipping...')
                return DownloadResult.DOWNLOAD_FAIL_SKIPPED
        except Exception:
            pass
    if scenario is not None:
        matching_sq = scenario.get_matching_subquery(vi.my_id, tags_raw, score, rating)
        uvpalways_sq = scenario.get_uvp_always_subquery() if tdiv is None else None
        if matching_sq:
            vi.my_subfolder = matching_sq.subfolder
            vi.my_quality = matching_sq.quality
        elif uvpalways_sq:
            vi.my_subfolder = uvpalways_sq.subfolder
            vi.my_quality = uvpalways_sq.quality
        else:
            Log.info(f'Info: unable to find matching or uvp scenario subquery for {sname}, skipping...')
            return DownloadResult.DOWNLOAD_FAIL_SKIPPED
    elif tdiv is None and len(ExtraConfig.extra_tags) > 0 and ExtraConfig.uvp != DOWNLOAD_POLICY_ALWAYS:
        Log.warn(f'Warning: could not extract tags from {sname}, skipping due to untagged videos download policy...')
        return DownloadResult.DOWNLOAD_FAIL_SKIPPED
    if ExtraConfig.save_tags:
        register_item_tags(vi.my_id, ' '.join(sorted(tags_raw)), vi.my_subfolder)
    tags_str = filtered_tags(list(sorted(tags_raw)))
    if tags_str != '':
        my_tags = tags_str

    tries = 0
    while True:
        ddiv = i_html.find('div', string='Download:')
        if ddiv is not None and ddiv.parent is not None:
            break
        message_span = i_html.find('span', class_='message')
        if message_span:
            Log.warn(f'Cannot find download section for {sname}, reason: \'{message_span.text}\', skipping...')
            return DownloadResult.DOWNLOAD_FAIL_SKIPPED
        elif tries >= 5:
            Log.error(f'Cannot find download section for {sname} after {tries:d} tries, failed!')
            return DownloadResult.DOWNLOAD_FAIL_RETRIES
        tries += 1
        Log.debug(f'No download section for {sname}, retry #{tries:d}...')
        i_html = await fetch_html(f'{SITE_AJAX_REQUEST_VIDEO % vi.my_id}?popup_id={2 + tries + vi.my_id % 10:d}', session=dwn.session)
    links = ddiv.parent.find_all('a', class_='tag_item')
    qualities = list()
    for lin in links:
        try:
            qualities.append(str(lin.text).replace('MP4 ', ''))
        except Exception:
            pass
    if vi.my_quality not in qualities:
        q_idx = 0
        Log.warn(f'Warning: cannot find quality \'{vi.my_quality}\' for {sname}, using \'{qualities[q_idx]}\'')
        vi.my_quality = qualities[q_idx]
        link_idx = q_idx
    else:
        link_idx = qualities.index(vi.my_quality)
    vi.my_link = links[link_idx].get('href')

    my_score = (f'{f"+" if score.isnumeric() else ""}{score}' if len(score) > 0
                else '' if len(rating) > 0 else 'unk')
    my_rating = (f'{", " if  len(my_score) > 0 else ""}{rating}{"%" if rating.isnumeric() else ""}' if len(rating) > 0
                 else '' if len(my_score) > 0 else 'unk')
    extra_len = 5 + 2 + 3  # 3 underscores + 2 brackets + len('2160p') - max len of all qualities
    fname_part2 = extract_ext(vi.my_link)
    fname_part1 = (
        f'{prefixp() if has_naming_flag(NamingFlags.NAMING_FLAG_PREFIX) else ""}'
        f'{vi.my_id:d}'
        f'{f"_score({my_score}{my_rating})" if has_naming_flag(NamingFlags.NAMING_FLAG_SCORE) else ""}'
        f'{f"_{vi.my_title}" if vi.my_title != "" and has_naming_flag(NamingFlags.NAMING_FLAG_TITLE) else ""}'
    )
    if has_naming_flag(NamingFlags.NAMING_FLAG_TAGS):
        while len(my_tags) > max(0, 240 - (len(vi.my_folder) + len(fname_part1) + len(fname_part2) + extra_len)):
            my_tags = my_tags[:max(0, my_tags.rfind(TAGS_CONCAT_CHAR))]
        fname_part1 = f'{fname_part1}{f"_({my_tags})" if len(my_tags) > 0 else ""}'

    if len(my_tags) == 0 and len(fname_part1) > max(0, 240 - (len(vi.my_folder) + len(fname_part2) + extra_len)):
        fname_part1 = fname_part1[:max(0, 240 - (len(vi.my_folder) + len(fname_part2) + extra_len))]

    fname_mid = f'_{vi.my_quality}' if has_naming_flag(NamingFlags.NAMING_FLAG_QUALITY) else ''

    vi.my_filename = f'{fname_part1}{fname_mid}{fname_part2}'

    res = await download_file(vi)
    if res != DownloadResult.DOWNLOAD_SUCCESS:
        vi.set_state(VideoInfo.VIState.FAILED)

    return res


async def check_item_download_status(idi: int, dest: str, resp: ClientResponse) -> None:
    dwn = DownloadWorker.get()
    sname = f'{prefixp()}{idi:d}.mp4'
    try:
        # Log.trace(f'{sname} status check started...')
        last_size = -1
        while True:
            await sleep(DOWNLOAD_STATUS_CHECK_TIMER)
            if dest not in dwn.writes_active:  # finished already
                Log.error(f'{sname} status checker is still running for finished download!')
                break
            file_size = stat(dest).st_size if path.isfile(dest) else 0
            if file_size in (0, last_size):
                Log.error(f'{sname} status check failed (download stalled at {file_size:d})! Interrupting current try...')
                resp.connection.transport.abort()  # abort download task (forcefully - close connection)
                break
            # Log.trace(f'{sname} status check passed at {file_size:d}...')
            last_size = file_size
    except CancelledError:
        # Log.trace(f'{sname} status check cancelled...')
        pass


async def download_file(vi: VideoInfo) -> DownloadResult:
    dwn = DownloadWorker.get()
    sname = f'{prefixp()}{vi.my_id:d}.mp4'
    sfilename = f'{f"{vi.my_subfolder}/" if len(vi.my_subfolder) > 0 else ""}{vi.my_filename}'
    file_size = 0
    retries = 0
    ret = DownloadResult.DOWNLOAD_SUCCESS
    status_checker = None  # type: Optional[Task]

    vi.set_state(VideoInfo.VIState.DOWNLOADING)
    if not path.isdir(vi.my_folder):
        try:
            makedirs(vi.my_folder)
        except Exception:
            raise IOError(f'ERROR: Unable to create subfolder \'{vi.my_folder}\'!')
    else:
        rv_match = re_media_filename.match(vi.my_filename)
        rv_quality = rv_match.group(2)
        if file_already_exists(vi.my_id, rv_quality):
            Log.info(f'{vi.my_filename} (or similar) already exists. Skipped.')
            return DownloadResult.DOWNLOAD_FAIL_ALREADY_EXISTS

    while (not (path.isfile(vi.my_fullpath) and file_size > 0)) and retries < CONNECT_RETRIES_ITEM:
        try:
            if ExtraConfig.dm == DOWNLOAD_MODE_TOUCH:
                Log.info(f'Saving<touch> {0.0:.2f} Mb to {sfilename}')
                with open(vi.my_fullpath, 'wb'):
                    pass
                break

            r = None
            async with await wrap_request(dwn.session, 'GET', vi.my_link, timeout=CTOD) as r:
                if r.status == 404:
                    Log.error(f'Got 404 for {sname}...!')
                    retries = CONNECT_RETRIES_ITEM - 1
                    ret = DownloadResult.DOWNLOAD_FAIL_NOT_FOUND
                if r.content_type and r.content_type.find('text') != -1:
                    Log.error(f'File not found at {vi.my_link}!')
                    raise FileNotFoundError(vi.my_link)

                expected_size = r.content_length
                Log.info(f'Saving {(r.content_length / 1024**2) if r.content_length else 0.0:.2f} Mb to {sfilename}')

                dwn.writes_active.append(vi.my_fullpath)
                vi.set_state(VideoInfo.VIState.WRITING)
                status_checker = get_running_loop().create_task(check_item_download_status(vi.my_id, vi.my_fullpath, r))
                async with async_open(vi.my_fullpath, 'wb') as outf:
                    async for chunk in r.content.iter_chunked(2**22):
                        await outf.write(chunk)
                status_checker.cancel()
                dwn.writes_active.remove(vi.my_fullpath)

                file_size = stat(vi.my_fullpath).st_size
                if expected_size and file_size != expected_size:
                    Log.error(f'Error: file size mismatch for {sfilename}: {file_size:d} / {expected_size:d}')
                    raise IOError(vi.my_link)

                vi.set_state(VideoInfo.VIState.DONE)
                break
        except Exception:
            import sys
            print(sys.exc_info()[0], sys.exc_info()[1])
            if r is None or r.status != 403:
                retries += 1
                Log.error(f'{sfilename}: error #{retries:d}...')
            if r is not None and r.closed is False:
                r.close()
            if path.isfile(vi.my_fullpath):
                remove(vi.my_fullpath)
            # Network error may be thrown before item is added to active downloads
            if vi.my_fullpath in dwn.writes_active:
                dwn.writes_active.remove(vi.my_fullpath)
            if status_checker is not None:
                status_checker.cancel()
            if retries < CONNECT_RETRIES_ITEM:
                vi.set_state(VideoInfo.VIState.DOWNLOADING)
                await sleep(frand(1.0, 7.0))

    ret = (ret if ret == DownloadResult.DOWNLOAD_FAIL_NOT_FOUND else
           DownloadResult.DOWNLOAD_SUCCESS if retries < CONNECT_RETRIES_ITEM else
           DownloadResult.DOWNLOAD_FAIL_RETRIES)
    return ret


def at_interrupt() -> None:
    dwn = DownloadWorker.get()
    if dwn is not None:
        return dwn.at_interrupt()

#
#
#########################################
