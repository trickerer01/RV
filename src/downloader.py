# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations
from asyncio.queues import Queue as AsyncQueue
from asyncio.tasks import sleep, as_completed
from os import path, remove, makedirs, stat
from typing import List, Tuple, Coroutine, Any, Callable, Optional, Iterable, Union

from aiohttp import ClientSession

from config import Config
from defs import (
    DownloadResult, Mem, MAX_VIDEOS_QUEUE_SIZE, DOWNLOAD_QUEUE_STALL_CHECK_TIMER, DOWNLOAD_CONTINUE_FILE_CHECK_TIMER, PREFIX,
    START_TIME, UTF8, LOGGING_FLAGS, CONNECT_TIMEOUT_BASE, DOWNLOAD_POLICY_DEFAULT, NAMING_FLAGS_DEFAULT, DEFAULT_QUALITY,
    DOWNLOAD_MODE_DEFAULT,
)
from logger import Log
from util import format_time, get_elapsed_time_i, get_elapsed_time_s, calc_sleep_time
from vinfo import VideoInfo, get_min_max_ids

__all__ = ('VideoDownloadWorker',)


class VideoDownloadWorker:
    """
    Async queue wrapper which binds list of lists of arguments to a download function call and processes them
    asynchronously with a limit of simulteneous downloads defined by MAX_VIDEOS_QUEUE_SIZE
    """
    _instance = None  # type: Optional[VideoDownloadWorker]

    @staticmethod
    def get() -> Optional[VideoDownloadWorker]:
        return VideoDownloadWorker._instance

    def __init__(self, sequence: Iterable[VideoInfo], func: Callable[[VideoInfo], Coroutine[Any, Any, DownloadResult]],
                 filtered_count: int, session: ClientSession) -> None:
        assert VideoDownloadWorker._instance is None
        VideoDownloadWorker._instance = self

        self._func = func
        self._seq = [vi for vi in sequence]  # form our own container to erase from
        self._queue = AsyncQueue(MAX_VIDEOS_QUEUE_SIZE)  # type: AsyncQueue[Tuple[VideoInfo, Coroutine[Any, Any, DownloadResult]]]
        self._session = session
        self._orig_count = len(self._seq)
        self._downloaded_count = 0
        self._filtered_count_pre = filtered_count
        self._filtered_count_after = 0
        self._skipped_count = 0
        self._minmax_id = get_min_max_ids(self._seq)

        self._downloads_active = list()  # type: List[VideoInfo]
        self._writes_active = list()  # type: List[str]
        self._failed_items = list()  # type: List[int]

        self._total_queue_size_last = 0
        self._download_queue_size_last = 0
        self._write_queue_size_last = 0

    async def _at_task_start(self, vi: VideoInfo) -> None:
        self._downloads_active.append(vi)
        Log.trace(f'[queue] {vi.sname} added to queue')

    async def _at_task_finish(self, vi: VideoInfo, result: DownloadResult) -> None:
        self._downloads_active.remove(vi)
        Log.trace(f'[queue] {vi.sname} removed from queue')
        if result == DownloadResult.FAIL_ALREADY_EXISTS:
            self._filtered_count_after += 1
        elif result == DownloadResult.FAIL_SKIPPED:
            self._skipped_count += 1
        elif result == DownloadResult.FAIL_RETRIES:
            self._failed_items.append(vi.my_id)
        elif result == DownloadResult.SUCCESS:
            self._downloaded_count += 1

    async def _prod(self) -> None:
        while len(self._seq) > 0:
            if self._queue.full() is False:
                self._seq[0].set_state(VideoInfo.State.QUEUED)
                await self._queue.put((self._seq[0], self._func(self._seq[0])))
                del self._seq[0]
            else:
                await sleep(0.1)

    async def _cons(self) -> None:
        while len(self._seq) + self._queue.qsize() > 0:
            if self._queue.empty() is False and len(self._downloads_active) < MAX_VIDEOS_QUEUE_SIZE:
                vi, task = await self._queue.get()
                await self._at_task_start(vi)
                result = await task
                await self._at_task_finish(vi, result)
                self._queue.task_done()
            else:
                await sleep(0.35)

    async def _state_reporter(self) -> None:
        base_sleep_time = calc_sleep_time(3.0)
        force_check_seconds = DOWNLOAD_QUEUE_STALL_CHECK_TIMER
        last_check_seconds = 0
        while len(self._seq) + self._queue.qsize() + len(self._downloads_active) > 0:
            await sleep(base_sleep_time if len(self._seq) + self._queue.qsize() > 0 else 1.0)
            queue_size = len(self._seq) + self._queue.qsize()
            download_count = len(self._downloads_active)
            write_count = len(self._writes_active)
            queue_last = self._total_queue_size_last
            downloading_last = self._download_queue_size_last
            write_last = self._write_queue_size_last
            elapsed_seconds = get_elapsed_time_i()
            force_check = elapsed_seconds >= force_check_seconds and elapsed_seconds - last_check_seconds >= force_check_seconds
            if queue_last != queue_size or downloading_last != download_count or write_last != write_count or force_check:
                Log.info(f'[{get_elapsed_time_s()}] queue: {queue_size:d}, active: {download_count:d} (writing: {write_count:d})')
                last_check_seconds = elapsed_seconds
                self._total_queue_size_last = queue_size
                self._download_queue_size_last = download_count
                self._write_queue_size_last = write_count
                wc_threshold = MAX_VIDEOS_QUEUE_SIZE // (2 - int(force_check))
                if force_check or (queue_size == 0 and download_count == write_count <= wc_threshold):
                    item_states = list()
                    for vi in self._downloads_active:
                        cursize = stat(vi.my_fullpath).st_size if path.isfile(vi.my_fullpath) else 0
                        remsize = vi.my_expected_size - cursize if cursize else 0
                        cursize_str = f'{cursize / Mem.MB:.2f}' if cursize else '???'
                        totalsize_str = f'{vi.my_expected_size / Mem.MB:.2f}' if vi.my_expected_size else '???'
                        size_pct = f'{cursize * 100 / vi.my_expected_size:.1f}' if cursize and vi.my_expected_size else '??.?'
                        dfull_seconds = max(0, elapsed_seconds - vi.my_start_time)
                        dfull_size_b = cursize - vi.my_start_size
                        dfull_speed_kb = ((dfull_size_b / Mem.KB) / dfull_seconds) if dfull_seconds and dfull_size_b >= Mem.KB else 0.0
                        dfull_speed_str = f'{dfull_speed_kb:.1f}' if dfull_speed_kb >= 0.1 else '???.?'
                        dfull_time_str = format_time(dfull_seconds) if dfull_speed_kb >= 0.1 else '??:??:??'
                        dfull_str = f'{dfull_size_b / Mem.MB:.2f} Mb in {dfull_time_str}, avg {dfull_speed_str} Kb/s'
                        d_seconds = max(0, elapsed_seconds - vi.my_last_check_time)
                        d_size_b = cursize - vi.my_last_check_size
                        d_speed_kb = ((d_size_b / Mem.KB) / d_seconds) if d_seconds and d_size_b >= Mem.KB else 0.0
                        speed_str = f'{d_speed_kb:.1f}' if d_speed_kb >= 0.1 else '???.?'
                        eta_str = (format_time(0) if vi.my_expected_size == cursize else
                                   format_time(int((remsize / Mem.KB) / d_speed_kb)) if remsize and d_speed_kb >= 0.1 else '??:??:??')
                        item_states.append(f' {vi.my_sfolder}{PREFIX}{vi.my_id:d}:'
                                           f' {cursize_str} / {totalsize_str} Mb ({size_pct}%),'
                                           f' {speed_str} Kb/s, ETA: {eta_str} ({dfull_str})')
                        vi.my_last_check_size = cursize
                        vi.my_last_check_time = elapsed_seconds
                    Log.debug('\n'.join(item_states))

    async def _continue_file_checker(self) -> None:
        if not Config.store_continue_cmdfile:
            return
        minmax_id = self._minmax_id
        continue_file_path = (
            f'{Config.dest_base}{PREFIX}{START_TIME.strftime("%Y-%m-%d_%H_%M_%S")}_{minmax_id[0]:d}-{minmax_id[1]:d}.continue.conf'
        )
        arglist_base = [
            '-path', Config.dest_base, '-continue', '--store-continue-cmdfile',
            '-log', next(filter(lambda x: int(LOGGING_FLAGS[x], 16) == Config.logging_flags, LOGGING_FLAGS.keys())),
            *(('-quality', Config.quality) if Config.quality != DEFAULT_QUALITY and not Config.scenario else ()),
            *(('-utp', Config.utp) if Config.utp != DOWNLOAD_POLICY_DEFAULT and not Config.scenario else ()),
            *(('-minrating', Config.min_rating) if Config.min_rating else ()),
            *(('-minscore', Config.min_score) if Config.min_score else ()),
            *(('-naming', Config.naming_flags) if Config.naming_flags != NAMING_FLAGS_DEFAULT else ()),
            *(('-dmode', Config.download_mode) if Config.download_mode != DOWNLOAD_MODE_DEFAULT else ()),
            *(('-proxy', Config.proxy) if Config.proxy else ()),
            *(('-throttle', Config.throttle) if Config.throttle else ()),
            *(('-timeout', int(Config.timeout.connect)) if int(Config.timeout.connect) != CONNECT_TIMEOUT_BASE else ()),
            *(('-unfinish',) if Config.keep_unfinished else ()),
            *(('-tdump',) if Config.save_tags else ()),
            *(('-ddump',) if Config.save_descriptions else ()),
            *(('-cdump',) if Config.save_comments else ()),
            *(('-sdump',) if Config.save_screenshots else ()),
            *(('-session_id', Config.session_id,) if Config.session_id else ()),
            *Config.extra_tags,
            *(('-script', Config.scenario.fmt_str) if Config.scenario else ())
        ]
        base_sleep_time = calc_sleep_time(3.0)
        write_delay = DOWNLOAD_CONTINUE_FILE_CHECK_TIMER
        last_check_seconds = 0
        while len(self._seq) + self._queue.qsize() + len(self._downloads_active) > 0:
            elapsed_seconds = get_elapsed_time_i()
            if elapsed_seconds >= write_delay and elapsed_seconds - last_check_seconds >= write_delay:
                last_check_seconds = elapsed_seconds
                v_ids = sorted(vi.my_id for vi in self._seq + [qvi[0] for qvi in getattr(self._queue, '_queue')] + self._downloads_active)
                arglist = ['-seq', f'({"~".join(f"id={idi:d}" for idi in v_ids)})'] if len(v_ids) > 1 else ['-start', str(v_ids[0])]
                arglist.extend(arglist_base)
                try:
                    Log.trace(f'Storing continue file to \'{continue_file_path}\'...')
                    if not path.isdir(Config.dest_base):
                        makedirs(Config.dest_base)
                    with open(continue_file_path, 'wt', encoding=UTF8, buffering=1) as cfile:
                        cfile.write('\n'.join(str(e) for e in arglist))
                except (OSError, IOError):
                    Log.error(f'Unable to save continue file to {continue_file_path}!')
            await sleep(base_sleep_time)
        if path.isfile(continue_file_path):
            Log.trace(f'All files downloaded. Removing continue file \'{continue_file_path}\'...')
            remove(continue_file_path)

    async def _after_download(self) -> None:
        newline = '\n'
        Log.info(f'\nDone. {self._downloaded_count:d} / {self._orig_count:d}+{self._filtered_count_pre:d} file(s) downloaded, '
                 f'{self._filtered_count_after:d}+{self._filtered_count_pre:d} already existed, '
                 f'{self._skipped_count:d} skipped')
        if len(self._seq) > 0:
            Log.fatal(f'total queue is still at {len(self._seq):d} != 0!')
        if len(self._writes_active) > 0:
            Log.fatal(f'active writes count is still at {len(self._writes_active):d} != 0!')
        if len(self._failed_items) > 0:
            Log.fatal(f'Failed items:\n{newline.join(str(fi) for fi in sorted(self._failed_items))}')

    async def run(self) -> None:
        for cv in as_completed([self._prod(), self._state_reporter(), self._continue_file_checker(),
                               *(self._cons() for _ in range(MAX_VIDEOS_QUEUE_SIZE))]):
            await cv
        await self._after_download()

    def at_interrupt(self) -> None:
        if len(self._writes_active) > 0:
            if Config.keep_unfinished:
                unfinished_str = '\n '.join(f'{i + 1:d}) {s}' for i, s in enumerate(sorted(self._writes_active)))
                Log.debug(f'at_interrupt: keeping {len(self._writes_active):d} unfinished file(s):\n {unfinished_str}')
                return
            Log.debug(f'at_interrupt: cleaning {len(self._writes_active):d} unfinished file(s)...')
            for unfinished in sorted(self._writes_active):
                Log.debug(f'at_interrupt: trying to remove \'{unfinished}\'...')
                if path.isfile(unfinished):
                    remove(unfinished)
                else:
                    Log.debug(f'at_interrupt: file \'{unfinished}\' not found!')

    @property
    def session(self) -> ClientSession:
        return self._session

    def is_writing(self, videst: Union[VideoInfo, str]) -> bool:
        return (videst.my_fullpath if isinstance(videst, VideoInfo) else videst) in self._writes_active

    def add_to_writes(self, vi: VideoInfo) -> None:
        self._writes_active.append(vi.my_fullpath)

    def remove_from_writes(self, vi: VideoInfo) -> None:
        self._writes_active.remove(vi.my_fullpath)

#
#
#########################################
