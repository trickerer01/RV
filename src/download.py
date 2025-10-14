# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import os
import random
import urllib.parse
from asyncio import Task, as_completed, get_running_loop, sleep

from aiofile import async_open
from aiohttp import ClientPayloadError

from config import Config
from defs import (
    CONNECT_REQUEST_DELAY,
    CONNECT_RETRY_DELAY,
    DOWNLOAD_MODE_SKIP,
    DOWNLOAD_MODE_TOUCH,
    DOWNLOAD_POLICY_ALWAYS,
    FULLPATH_MAX_BASE_LEN,
    PREFIX,
    SCAN_CANCEL_KEYSTROKE,
    SCREENSHOTS_COUNT,
    SITE,
    SITE_AJAX_REQUEST_VIDEO,
    TAGS_CONCAT_CHAR,
    DownloadResult,
    Mem,
    NamingFlags,
    Quality,
)
from downloader import VideoDownloadWorker
from dscanner import VideoScanWorker
from dthrottler import ThrottleChecker
from fetch_html import ensure_conn_closed, fetch_html, wrap_request
from iinfo import VideoInfo, export_video_info, get_min_max_ids
from logger import Log
from path_util import file_already_exists, is_file_being_used, register_new_file, try_rename
from rex import re_media_filename, re_time
from tagger import filtered_tags, is_filtered_out_by_extra_tags, solve_tag_conflicts
from util import extract_ext, format_time, get_elapsed_time_i, get_time_seconds, has_naming_flag, normalize_path

__all__ = ('at_interrupt', 'download')


async def download(sequence: list[VideoInfo], by_id: bool, filtered_count: int) -> None:
    minid, maxid = get_min_max_ids(sequence)
    eta_min = int(2.0 + (CONNECT_REQUEST_DELAY + 0.2 + 0.02) * len(sequence))
    interrupt_msg = f'\nPress \'{SCAN_CANCEL_KEYSTROKE}\' twice to stop' if by_id else ''
    Log.info(f'\nOk! {len(sequence):d} ids (+{filtered_count:d} filtered out), bound {minid:d} to {maxid:d}.'
             f' Working...{interrupt_msg}\n'
             f'\nThis will take at least {eta_min:d} seconds{f" ({format_time(eta_min)})" if eta_min >= 60 else ""}!\n')
    with (VideoScanWorker(sequence, scan_video) as scn, VideoDownloadWorker(sequence, process_video, filtered_count) as dwn):
        for cv in as_completed([scn.run(), dwn.run()] if by_id else [dwn.run()]):
            await cv
    export_video_info(sequence)


async def scan_video(vi: VideoInfo) -> DownloadResult:
    scn = VideoScanWorker.get()
    scenario = Config.scenario
    sname = vi.sname
    extra_ids: list[int] = scn.get_extra_ids() if scn else []
    my_tags = 'no_tags'
    rating = vi.rating
    score = ''

    predict_gap4 = Config.predict_id_gaps and 3670052 <= vi.id <= 9999999  # 1-3-1
    predict_gap2 = Config.predict_id_gaps and 3638828 <= vi.id <= 3639245  # 1-1-1
    predict_gap3 = Config.predict_id_gaps and 3400000 <= vi.id <= 9999999 and not (predict_gap2 or predict_gap4)  # 1-2-1
    predict_expects = [(predict_gap4, 4), (predict_gap2, 2), (predict_gap3, 3)]
    predicted_skip = False
    predicted_prefix = ''
    if predict_gap4:
        predicted_prefix = '4'
        vi_prev1 = scn.find_vinfo_last(vi.id - 1)
        vi_prev2 = scn.find_vinfo_last(vi.id - 2)
        vi_prev3 = scn.find_vinfo_last(vi.id - 3)
        if vi_prev1 and vi_prev2 and vi_prev3:
            f_404s = [vip.has_flag(VideoInfo.Flags.RETURNED_404) for vip in (vi_prev1, vi_prev2, vi_prev3)]
            predicted_skip = not (f_404s[0] is f_404s[1] is f_404s[2])
        elif vi_prev1 and vi_prev2:
            f_404s = [vip.has_flag(VideoInfo.Flags.RETURNED_404) for vip in (vi_prev1, vi_prev2)]
            predicted_skip = f_404s[0] is not f_404s[1]
        else:
            predicted_skip = vi_prev1 and not vi_prev1.has_flag(VideoInfo.Flags.RETURNED_404)
    elif predict_gap3:
        predicted_prefix = '3'
        vi_prev1 = scn.find_vinfo_last(vi.id - 1)
        vi_prev2 = scn.find_vinfo_last(vi.id - 2)
        if vi_prev1 and vi_prev2:
            f_404s = [vip.has_flag(VideoInfo.Flags.RETURNED_404) for vip in (vi_prev1, vi_prev2)]
            predicted_skip = f_404s[0] is not f_404s[1]
        else:
            predicted_skip = vi_prev1 and not vi_prev1.has_flag(VideoInfo.Flags.RETURNED_404)
    elif predict_gap2:
        predicted_prefix = '2'
        vi_prev1 = scn.find_vinfo_last(vi.id - 1)
        predicted_skip = vi_prev1 and not vi_prev1.has_flag(VideoInfo.Flags.RETURNED_404)
    if predicted_skip:
        Log.warn(f'Id gap prediction {predicted_prefix} forces error 404 for {sname}, skipping...')
        return DownloadResult.FAIL_NOT_FOUND

    vi.set_state(VideoInfo.State.SCANNING)
    a_html = await fetch_html(f'{SITE_AJAX_REQUEST_VIDEO % vi.id}?popup_id={2 + vi.id % 10:d}')
    if a_html is None:
        Log.error(f'Error: unable to retreive html for {sname}! Aborted!')
        return DownloadResult.FAIL_SKIPPED if Config.aborted else DownloadResult.FAIL_RETRIES

    if not len(a_html):
        Log.error(f'Got empty HTML page for {sname}! Rescanning...')
        return DownloadResult.FAIL_EMPTY_HTML

    if a_html.find('title', string='404 Not Found'):
        Log.error(f'Got error 404 for {sname}, skipping...')
        return DownloadResult.FAIL_NOT_FOUND

    for predict, gap_size in predict_expects:
        if predict:
            # find previous valid id and check the offset
            id_dec = gap_size
            vi_prev_x = scn.find_vinfo_last(vi.id - id_dec)
            while vi_prev_x and vi_prev_x.has_flag(VideoInfo.Flags.RETURNED_404):
                id_dec += 1
                vi_prev_x = scn.find_vinfo_last(vi.id - id_dec)
            if vi_prev_x and (id_dec % gap_size) != 0:
                Log.error(f'Error: id gap predictor encountered unexpected valid post offset != {gap_size:d}. Disabling prediction!')
                Config.predict_id_gaps = False
            break

    if not vi.title:
        titleh1 = a_html.find('h1', class_='title_video')
        vi.title = titleh1.text if titleh1 else ''
    if not vi.duration:
        try:
            vi.duration = get_time_seconds(str(a_html.find('div', class_='info row').find('span', string=re_time).text))
        except Exception:
            Log.error(f'Unable to extract duration for {sname}!')
            vi.duration = 0

    Log.info(f'Scanning {sname}: {vi.fduration} \'{vi.title}\'')

    try:
        rating, votes = tuple(a_html.find('span', class_='voters count').text.split(' ', 1))
        votes = votes[1:-1].replace(',', '')
        rating = rating.replace('%', '')
        dislikes_int = int(votes) * (100 - (int(rating) or 100)) // 100
        likes_int = int(votes) - dislikes_int
        score = f'{likes_int - dislikes_int:d}'
    except Exception:
        Log.warn(f'Warning: cannot extract score for {sname}.')
    try:
        my_authors = [str(a.string).lower() for a in a_html.find('div', string='Artist').parent.find_all('span')]
    except Exception:
        Log.warn(f'Warning: cannot extract authors for {sname}.')
        my_authors = []
    try:
        my_categories = [str(c.string).lower() for c in a_html.find('div', string='Categories').parent.find_all('span')]
    except Exception:
        Log.warn(f'Warning: cannot extract categories for {sname}.')
        my_categories = []
    try:
        vi.uploader = str(a_html.find('div', string='Uploaded by').parent.find('a').get_text(strip=True)).lower()
    except Exception:
        Log.warn(f'Warning: cannot extract uploader for {sname}.')
    tdiv = a_html.find('div', string='Tags')
    if tdiv is None:
        Log.info(f'Warning: video {sname} has no tags!')
    tags = [str(elem.string) for elem in tdiv.parent.find_all('a', class_='tag_item')] if tdiv else ['']
    tags_raw = [tag.replace(' ', '_').lower() for tag in tags if tag]
    for calist in (my_categories, my_authors):
        for add_tag in [ca.replace(' ', '_') for ca in calist if ca]:
            if add_tag not in tags_raw:
                tags_raw.append(add_tag)
    if Config.save_tags:
        vi.tags = ' '.join(sorted(tags_raw))
    if Config.save_descriptions or Config.save_comments or Config.check_description_pos or Config.check_description_neg:
        cidivs = a_html.find_all('div', class_='comment-info')
        cudivs = [cidiv.find('a') for cidiv in cidivs]
        ctdivs = [cidiv.find('div', class_='coment-text') for cidiv in cidivs]
        desc_em = a_html.find('em')  # exactly one
        my_uploader = vi.uploader or 'unknown'
        has_description = (cudivs[-1].text.lower() == my_uploader) if (cudivs and ctdivs) else False  # first comment by uploader
        if cudivs and ctdivs:
            assert len(ctdivs) == len(cudivs)
        if Config.save_descriptions or Config.check_description_pos or Config.check_description_neg:
            desc_comment = (f'{cudivs[-1].text}:\n' + ctdivs[-1].get_text('\n').strip()) if has_description else ''
            desc_base = (f'\n{my_uploader}:\n' + desc_em.get_text('\n') + '\n') if desc_em else ''
            vi.description = desc_base or (f'\n{desc_comment}\n' if desc_comment else '')
        if Config.save_comments:
            comments_list = [f'{cudivs[i].text}:\n' + ctdivs[i].get_text('\n').strip() for i in range(len(ctdivs) - int(has_description))]
            vi.comments = ('\n' + '\n\n'.join(comments_list) + '\n') if comments_list else ''
    if Config.check_uploader and vi.uploader and vi.uploader not in tags_raw:
        tags_raw.append(vi.uploader)
    va_list = list(filter(lambda x: 'audio' in x or '(va)' in x or x.endswith('va'), my_authors))
    aucat_count = max(len(my_authors) - len(va_list), len(my_categories))
    if aucat_count >= 6 and 'compilation' not in tags_raw and 'pmv' not in tags_raw:
        Log.warn(f'{sname} has {len(my_authors):d} arts ({len(va_list):d} VA) and {len(my_categories):d} cats! Assuming compilation')
        tags_raw.append('compilation')
    if Config.solve_tag_conflicts:
        solve_tag_conflicts(vi, tags_raw)
    Log.debug(f'{sname} tags: \'{",".join(tags_raw)}\'')
    if is_filtered_out_by_extra_tags(vi, tags_raw, Config.extra_tags, Config.id_sequence, vi.subfolder, extra_ids):
        Log.info(f'Info: video {sname} is filtered out by{" outer" if scenario else ""} extra tags, skipping...')
        return DownloadResult.FAIL_FILTERED_OUTER if scenario else DownloadResult.FAIL_SKIPPED
    for vsrs, csri, srn, pc in zip((score, rating), (Config.min_score, Config.min_rating), ('score', 'rating'), ('', '%'), strict=True):
        if len(vsrs) > 0 and csri is not None:
            try:
                if int(vsrs) < csri:
                    Log.info(f'Info: video {sname} has low {srn} \'{vsrs}{pc}\' (required {csri:d}), skipping...')
                    return DownloadResult.FAIL_SKIPPED
            except Exception:
                pass
    if scenario:
        matching_sq = scenario.get_matching_subquery(vi, tags_raw, score, rating)
        utpalways_sq = scenario.get_utp_always_subquery() if tdiv is None else None
        if matching_sq:
            vi.subfolder = matching_sq.subfolder
            vi.quality = matching_sq.quality
        elif utpalways_sq:
            vi.subfolder = utpalways_sq.subfolder
            vi.quality = utpalways_sq.quality
        else:
            Log.info(f'Info: unable to find matching or utp scenario subquery for {sname}, skipping...')
            return DownloadResult.FAIL_SKIPPED
    elif tdiv is None and len(Config.extra_tags) > 0 and Config.utp != DOWNLOAD_POLICY_ALWAYS:
        Log.warn(f'Warning: could not extract tags from {sname}, skipping due to untagged videos download policy...')
        return DownloadResult.FAIL_SKIPPED
    if Config.duration and vi.duration and not (Config.duration.first <= vi.duration <= Config.duration.second):
        Log.info(f'Info: video {sname} duration \'{vi.duration:d}\' is out of bounds ({Config.duration!s}), skipping...')
        return DownloadResult.FAIL_SKIPPED
    if scn.find_vinfo_pred(lambda _: _.id == vi.id and VideoInfo.State.DOWNLOAD_PENDING <= _.state <= VideoInfo.State.DONE):
        Log.info(f'{sname} was already processed, skipping...')
        return DownloadResult.FAIL_ALREADY_EXISTS
    my_tags = filtered_tags(sorted(tags_raw)) or my_tags

    tries = 0
    while True:
        ddiv = a_html.find('div', string='Download')
        if ddiv is not None and ddiv.parent is not None:
            break
        message_span = a_html.find('span', class_='message')
        if message_span:
            Log.warn(f'Cannot find download section for {sname}, reason: \'{message_span.text}\', skipping...')
            return DownloadResult.FAIL_DELETED
        elif tries >= 5:
            Log.error(f'Cannot find download section for {sname} after {tries:d} tries, failed!')
            return DownloadResult.FAIL_RETRIES
        tries += 1
        Log.debug(f'No download section for {sname}, retry #{tries:d}...')
        a_html = await fetch_html(f'{SITE_AJAX_REQUEST_VIDEO % vi.id}?popup_id={2 + tries + vi.id % 10:d}')
    links = ddiv.parent.find_all('a', class_='tag_item')
    qualities = []
    for lin in links:
        try:
            qualities.append(lin.text.replace('MP4 ', ''))
        except Exception:
            pass
    if vi.quality not in qualities:
        q_idx = 0
        Log.warn(f'Warning: cannot find quality \'{vi.quality}\' for {sname}, selecting \'{qualities[q_idx]}\'')
        vi.quality = qualities[q_idx]
        link_idx = q_idx
    else:
        link_idx = qualities.index(vi.quality)
    vi.link = links[link_idx].get('href')

    prefix = PREFIX if has_naming_flag(NamingFlags.PREFIX) else ''
    fname_part2 = extract_ext(vi.link)
    my_score = (f'{"+" if score.isnumeric() else ""}{score}' if len(score) > 0
                else '' if len(rating) > 0 else 'unk')
    my_rating = (f'{", " if len(my_score) > 0 else ""}{rating}{"%" if rating.isnumeric() else ""}' if len(rating) > 0
                 else '' if len(my_score) > 0 else 'unk')
    fname_part1 = (
        f'{prefix}{vi.id:d}'
        f'{f"_({my_score}{my_rating})" if has_naming_flag(NamingFlags.SCORE) else ""}'
        f'{f"_{vi.title}" if vi.title and has_naming_flag(NamingFlags.TITLE) else ""}'
    )
    # <fname_part1>_(<TAGS...>)_<QUALITY><fname_part2>
    extra_len = 2 + 2 + 5  # 2 underscores + 2 brackets + len('2160p') - max len of all qualities
    if has_naming_flag(NamingFlags.TAGS):
        while len(my_tags) > max(0, FULLPATH_MAX_BASE_LEN - (len(vi.my_folder) + len(fname_part1) + len(fname_part2) + extra_len)):
            my_tags = my_tags[:max(0, my_tags.rfind(TAGS_CONCAT_CHAR))]
        fname_part1 += f'_({my_tags})' if len(my_tags) > 0 else ''
    if len(my_tags) == 0 and len(fname_part1) > max(0, FULLPATH_MAX_BASE_LEN - (len(vi.my_folder) + len(fname_part2) + extra_len)):
        fname_part1 = fname_part1[:max(0, FULLPATH_MAX_BASE_LEN - (len(vi.my_folder) + len(fname_part2) + extra_len))]
    fname_part1 = fname_part1.strip()

    fname_mid = f'_{vi.quality}' if has_naming_flag(NamingFlags.QUALITY) else ''
    vi.filename = f'{fname_part1}{fname_mid}{fname_part2}'

    vi.set_state(VideoInfo.State.SCANNED)
    return DownloadResult.SUCCESS


async def process_video(vi: VideoInfo) -> DownloadResult:
    vi.set_state(VideoInfo.State.DOWNLOAD_PENDING)
    res = await download_video(vi)
    if res not in (DownloadResult.SUCCESS, DownloadResult.FAIL_SKIPPED, DownloadResult.FAIL_ALREADY_EXISTS):
        vi.set_state(VideoInfo.State.FAILED)
    return res


async def download_sceenshot(vi: VideoInfo, scr_num: int) -> DownloadResult:
    sname = f'{PREFIX}{vi.id:d}_{scr_num:02d}.webp'
    sfilename = f'{f"{vi.subfolder}/" if len(vi.subfolder) > 0 else ""}{PREFIX}{vi.id:d}/{scr_num:02d}.webp'
    my_folder = f'{vi.my_folder}{PREFIX}{vi.id:d}/'
    fullpath = f'{my_folder}{scr_num:02d}.webp'
    my_link = f'{SITE}/contents/videos_screenshots/{vi.id - vi.id % 1000:d}/{vi.id:d}/336x189/{scr_num:d}.jpg'
    ret = DownloadResult.SUCCESS

    if not os.path.isdir(my_folder):
        try:
            os.makedirs(my_folder)
        except Exception:
            raise OSError(f'ERROR: Unable to create subfolder \'{my_folder}\'!')

    try:
        async with await wrap_request('GET', my_link) as r:
            if r.status == 404:
                Log.error(f'Got 404 for {sname}...!')
                ret = DownloadResult.FAIL_NOT_FOUND
            elif r.content_type and 'text' in r.content_type:
                Log.error(f'File not found at {my_link}!')
                ret = DownloadResult.FAIL_NOT_FOUND

            expected_size = r.content_length
            async with async_open(fullpath, 'wb') as outf:
                async for chunk in r.content.iter_chunked(256 * Mem.KB):
                    await outf.write(chunk)

            file_size = os.stat(fullpath).st_size
            if expected_size and file_size != expected_size:
                Log.error(f'Error: file size mismatch for {sfilename}: {file_size:d} / {expected_size:d}')
                ret = DownloadResult.FAIL_RETRIES
    except Exception:
        ret = DownloadResult.FAIL_NOT_FOUND

    return ret


async def download_sceenshots(vi: VideoInfo) -> DownloadResult:
    ret = DownloadResult.SUCCESS
    t: Task[DownloadResult]
    for t in [get_running_loop().create_task(download_sceenshot(vi, scr_idx + 1)) for scr_idx in range(SCREENSHOTS_COUNT)]:
        res = await t
        if res not in (DownloadResult.SUCCESS, ret):
            ret = res
    return ret


async def download_video(vi: VideoInfo) -> DownloadResult:
    dwn = VideoDownloadWorker.get()
    retries = 0
    exact_quality = False
    ret = DownloadResult.SUCCESS
    skip = Config.dm == DOWNLOAD_MODE_SKIP
    status_checker = ThrottleChecker(vi)

    if skip is True:
        vi.set_state(VideoInfo.State.DONE)
        ret = DownloadResult.FAIL_SKIPPED
    else:
        vi.set_state(VideoInfo.State.DOWNLOADING)
        curfile_match = re_media_filename.match(vi.filename)
        curfile_quality = Quality(curfile_match.group(2) or vi.quality)
        curfile = file_already_exists(vi.id, curfile_quality)
        if curfile:
            curfile_folder, curfile_name = os.path.split(curfile)
            curfile_omatch = re_media_filename.match(curfile_name)
            curfile_oquality = Quality(curfile_omatch.group(2) or '')
            exact_name = curfile == vi.my_fullpath
            exact_quality = curfile_oquality and curfile_quality == curfile_oquality
            vi.set_flag(VideoInfo.Flags.ALREADY_EXISTED_EXACT if exact_name else VideoInfo.Flags.ALREADY_EXISTED_SIMILAR)
            if Config.continue_mode and exact_quality:
                proc_str = is_file_being_used(curfile)
                if proc_str:
                    Log.error(f'Error: file {vi.sffilename} already exists and is locked by \'{proc_str}\'!! Parallel download? Aborted!')
                    return DownloadResult.FAIL_ALREADY_EXISTS
                if not exact_name:
                    same_loc = os.path.isdir(vi.my_folder) and os.path.samefile(curfile_folder, vi.my_folder)
                    loc_str = f' ({"same" if same_loc else "different"} location)'
                    if Config.no_rename_move is False or same_loc:
                        Log.info(f'{vi.sffilename} {vi.quality} found{loc_str}. Enforcing new name (was \'{curfile}\').')
                        if not try_rename(curfile, vi.my_fullpath):
                            Log.warn(f'Warning: file {vi.sffilename} already exists! Old file will be preserved.')
                    else:
                        new_subfolder = normalize_path(os.path.relpath(curfile_folder, Config.dest_base))
                        Log.info(f'{vi.sffilename} {vi.quality} found{loc_str}. Enforcing old path + new name '
                                 f'\'{curfile_folder}/{vi.filename}\' due to \'--no-rename-move\' flag (was \'{curfile_name}\').')
                        vi.subfolder = new_subfolder
                        if not try_rename(curfile, normalize_path(os.path.abspath(vi.my_fullpath), False)):
                            Log.warn(f'Warning: file {vi.sffilename} already exists! Old file will be preserved.')
            else:
                qstr = f'\'{curfile_oquality}\' {"==" if exact_quality else ">=" if curfile_oquality else "<?>"} \'{curfile_quality}\''
                Log.info(f'{vi.sfsname} already exists ({qstr}). Skipped.\n Location: \'{curfile}\'')
                vi.subfolder = normalize_path(os.path.relpath(curfile_folder, Config.dest_base))
                vi.set_state(VideoInfo.State.DONE)
                return DownloadResult.FAIL_ALREADY_EXISTS
        if not os.path.isdir(vi.my_folder):
            try:
                os.makedirs(vi.my_folder)
            except Exception:
                raise OSError(f'ERROR: Unable to create subfolder \'{vi.my_folder}\'!')

    while (not skip) and retries <= Config.retries:
        r = None
        try:
            file_exists = os.path.isfile(vi.my_fullpath)
            if file_exists and retries == 0:
                vi.set_flag(VideoInfo.Flags.ALREADY_EXISTED_EXACT)
            file_size = os.stat(vi.my_fullpath).st_size if file_exists else 0

            if Config.dm == DOWNLOAD_MODE_TOUCH:
                if file_exists:
                    Log.info(f'{vi.sfsname} ({vi.quality}) already exists, size: {file_size:d} ({file_size / Mem.MB:.2f} Mb)')
                    vi.set_state(VideoInfo.State.DONE)
                    return DownloadResult.FAIL_ALREADY_EXISTS
                else:
                    Log.info(f'Saving<touch> {vi.sdname} {0.0:.2f} Mb to {vi.sffilename}')
                    with open(vi.my_fullpath, 'wb'):
                        vi.set_flag(VideoInfo.Flags.FILE_WAS_CREATED)
                        vi.set_state(VideoInfo.State.DONE)
                break

            hkwargs: dict[str, dict[str, str]] = {'headers': {'Range': f'bytes={file_size:d}-'} if file_size > 0 else {}}
            ckwargs = {'allow_redirects': not Config.proxy or not Config.download_without_proxy}
            # hkwargs['headers'].update({'Referer': SITE_AJAX_REQUEST_VIDEO % vi.id})
            r = await wrap_request('GET', vi.link, **ckwargs, **hkwargs)
            while r.status in (301, 302):
                if urllib.parse.urlparse(r.headers['Location']).hostname != urllib.parse.urlparse(vi.link).hostname:
                    ckwargs.update(noproxy=True, allow_redirects=True)
                ensure_conn_closed(r)
                r = await wrap_request('GET', r.headers['Location'], **ckwargs, **hkwargs)
            content_len = r.content_length or 0
            content_range_s = r.headers.get('Content-Range', '/').split('/', 1)
            content_range = int(content_range_s[1]) if len(content_range_s) > 1 and content_range_s[1].isnumeric() else 1
            if (content_len == 0 or r.status == 416) and file_size >= content_range:
                Log.warn(f'{vi.sfsname} ({vi.quality}) is already completed, size: {file_size:d} ({file_size / Mem.MB:.2f} Mb)')
                vi.set_state(VideoInfo.State.DONE)
                ret = DownloadResult.FAIL_ALREADY_EXISTS
                break
            if r.status == 404:
                Log.error(f'Got 404 for {vi.sfsname}...!')
                retries = Config.retries
                ret = DownloadResult.FAIL_NOT_FOUND
            if r.content_type and 'text' in r.content_type:
                Log.error(f'File not found at {vi.link}!')
                raise FileNotFoundError(vi.link)

            status_checker.prepare(r, file_size)
            vi.expected_size = file_size + content_len
            vi.last_check_size = vi.start_size = file_size
            vi.last_check_time = vi.start_time = get_elapsed_time_i()
            starting_str = f' <continuing at {file_size:d}>' if file_size else ''
            total_str = f' / {vi.expected_size / Mem.MB:.2f}' if file_size else ''
            Log.info(f'Saving{starting_str} {vi.sdname} {content_len / Mem.MB:.2f}{total_str} Mb to {vi.sffilename}')

            if Config.continue_mode and exact_quality:
                proc_str = is_file_being_used(vi.my_fullpath)
                if proc_str:
                    Log.error(f'Error: file {vi.sffilename} already exists and is locked by \'{proc_str}\'!! Parallel download? Aborted!')
                    return DownloadResult.FAIL_ALREADY_EXISTS

            dwn.add_to_writes(vi)
            vi.set_state(VideoInfo.State.WRITING)
            status_checker.run()
            async with async_open(vi.my_fullpath, 'ab') as outf:
                register_new_file(vi)
                vi.set_flag(VideoInfo.Flags.FILE_WAS_CREATED)
                if vi.dstart_time == 0:
                    vi.dstart_time = get_elapsed_time_i()
                async for chunk in r.content.iter_chunked(512 * Mem.KB):
                    await outf.write(chunk)
                    vi.bytes_written += len(chunk)
            status_checker.reset()
            dwn.remove_from_writes(vi)

            file_size = os.stat(vi.my_fullpath).st_size
            if vi.expected_size and file_size != vi.expected_size:
                Log.error(f'Error: file size mismatch for {vi.sfsname}: {file_size:d} / {vi.expected_size:d}')
                raise OSError(vi.link)

            total_time = (get_elapsed_time_i() - vi.dstart_time) or 1
            Log.info(f'[download] {vi.sfsname} ({vi.quality}) completed in {format_time(total_time)} '
                     f'({(vi.bytes_written / total_time) / Mem.KB:.1f} Kb/s)')

            vi.set_state(VideoInfo.State.DONE)
            break
        except Exception as e:
            import sys
            print(sys.exc_info()[0], sys.exc_info()[1])
            if (r is None or r.status != 403) and isinstance(e, ClientPayloadError) is False:
                retries += 1
                Log.error(f'{vi.sffilename}: error #{retries:d}...')
            if r is not None and r.closed is False:
                r.close()
            # Network error may be thrown before item is added to active downloads
            if dwn.is_writing(vi):
                dwn.remove_from_writes(vi)
            status_checker.reset()
            if retries <= Config.retries:
                vi.set_state(VideoInfo.State.DOWNLOADING)
                await sleep(random.uniform(*CONNECT_RETRY_DELAY))
            elif Config.keep_unfinished is False and os.path.isfile(vi.my_fullpath) and vi.has_flag(VideoInfo.Flags.FILE_WAS_CREATED):
                Log.error(f'Failed to download {vi.sffilename}. Removing unfinished file...')
                os.remove(vi.my_fullpath)
        finally:
            ensure_conn_closed(r)

    ret = (ret if ret in (DownloadResult.FAIL_NOT_FOUND, DownloadResult.FAIL_SKIPPED, DownloadResult.FAIL_ALREADY_EXISTS) else
           DownloadResult.SUCCESS if retries <= Config.retries else
           DownloadResult.FAIL_RETRIES)

    if Config.save_screenshots:
        sret = await download_sceenshots(vi)
        if sret != DownloadResult.SUCCESS:
            Log.warn(f'{vi.sffilename}: `download_sceenshots()` has failed items (ret = {sret!s})')

    return ret


def at_interrupt() -> None:
    dwn = VideoDownloadWorker.get()
    if dwn is not None:
        return dwn.at_interrupt()

#
#
#########################################
