# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations
from asyncio import Lock as AsyncLock
from asyncio.queues import Queue as AsyncQueue
from asyncio.tasks import sleep, as_completed
from os import path, remove, makedirs, stat
from typing import List, Coroutine, Any, Callable, Optional, Iterable, Union

from aiohttp import ClientSession

from config import Config
from defs import (
    DownloadResult, Mem, MAX_VIDEOS_QUEUE_SIZE, DOWNLOAD_QUEUE_STALL_CHECK_TIMER, DOWNLOAD_CONTINUE_FILE_CHECK_TIMER, PREFIX,
    START_TIME, UTF8,
)
from dscanner import VideoScanWorker
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

        self._scn = VideoScanWorker.get()

        self._func = func
        self._seq = [vi for vi in sequence]  # form our own container to erase from
        self._queue = AsyncQueue(MAX_VIDEOS_QUEUE_SIZE)  # type: AsyncQueue[VideoInfo]
        self._session = session
        self._orig_count = len(self._seq)
        self._downloaded_count = 0
        self._filtered_count_pre = filtered_count
        self._filtered_count_after = 0
        self._skipped_count = 0
        self._404_count = 0
        self._minmax_id = get_min_max_ids(self._seq)

        self._downloads_active = list()  # type: List[VideoInfo]
        self._writes_active = list()  # type: List[str]
        self._failed_items = list()  # type: List[int]

        self._total_queue_size_last = 0
        self._download_queue_size_last = 0
        self._write_queue_size_last = 0
        self._lock = AsyncLock()

        if self._scn:
            self._seq.clear()
            self._scn.register_task_finish_callback(self._at_task_finish)

    async def _at_task_start(self, vi: VideoInfo) -> None:
        self._downloads_active.append(vi)
        Log.trace(f'[queue] {vi.sname} added to active')

    async def _at_task_finish(self, vi: VideoInfo, result: DownloadResult) -> None:
        if vi in self._downloads_active:
            self._downloads_active.remove(vi)
            Log.trace(f'[queue] {vi.sname} removed from active')
        if result == DownloadResult.FAIL_ALREADY_EXISTS:
            self._filtered_count_after += 1
        elif result == DownloadResult.FAIL_SKIPPED:
            self._skipped_count += 1
        elif result == DownloadResult.FAIL_NOT_FOUND:
            self._404_count += 1
        elif result == DownloadResult.FAIL_RETRIES:
            self._failed_items.append(vi.id)
        elif result == DownloadResult.SUCCESS:
            self._downloaded_count += 1

    async def _prod(self) -> None:
        while self.can_fetch_next():
            if self._queue.full() is False:
                async with self._lock:
                    vi = await self._try_fetch_next()
                    if vi:
                        vi.set_state(VideoInfo.State.QUEUED)
                        await self._queue.put(vi)
            else:
                await sleep(0.2)

    async def _cons(self) -> None:
        while True:
            async with self._lock:
                can_fetch = self.can_fetch_next()
                qsize = self._queue.qsize()
            if can_fetch is False and qsize == 0:
                break
            if qsize > 0 and len(self._downloads_active) < MAX_VIDEOS_QUEUE_SIZE:
                vi = await self._queue.get()
                await self._at_task_start(vi)
                result = await self._func(vi)
                await self._at_task_finish(vi, result)
                self._queue.task_done()
            else:
                await sleep(0.35)

    async def _state_reporter(self) -> None:
        base_sleep_time = calc_sleep_time(3.0)
        force_check_seconds = DOWNLOAD_QUEUE_STALL_CHECK_TIMER
        last_check_seconds = 0
        while self.get_workload_size() > 0 or self.waiting_for_scanner():
            await sleep(base_sleep_time if len(self._seq) + self._queue.qsize() > 0 or self.waiting_for_scanner() else 1.0)
            queue_size = len(self._seq) + self.get_scanner_workload_size()
            ready_size = self._queue.qsize()
            download_count = len(self._downloads_active)
            write_count = len(self._writes_active)
            queue_last = self._total_queue_size_last
            downloading_last = self._download_queue_size_last
            write_last = self._write_queue_size_last
            elapsed_seconds = get_elapsed_time_i()
            force_check = elapsed_seconds >= force_check_seconds and elapsed_seconds - last_check_seconds >= force_check_seconds
            if queue_last != queue_size or downloading_last != download_count or write_last != write_count or force_check:
                Log.info(f'[{get_elapsed_time_s()}] queue: {queue_size:d}, ready: {ready_size:d}, active: {download_count:d} '
                         f'(writing: {write_count:d}){f" + {self._scn.get_prescanned_count():d} prescanned" if self._scn else ""}')
                last_check_seconds = elapsed_seconds
                self._total_queue_size_last = queue_size
                self._download_queue_size_last = download_count
                self._write_queue_size_last = write_count
                wc_threshold = MAX_VIDEOS_QUEUE_SIZE // (2 - int(force_check))
                if force_check or (queue_size == 0 and download_count == write_count <= wc_threshold):
                    item_states = list()
                    for vi in self._downloads_active:
                        cursize = stat(vi.my_fullpath).st_size if path.isfile(vi.my_fullpath) else 0
                        remsize = vi.expected_size - cursize if cursize else 0
                        cursize_str = f'{cursize / Mem.MB:.2f}' if cursize else '???'
                        totalsize_str = f'{vi.expected_size / Mem.MB:.2f}' if vi.expected_size else '???'
                        size_pct = f'{cursize * 100 / vi.expected_size:.1f}' if cursize and vi.expected_size else '??.?'
                        dfull_seconds = max(0, elapsed_seconds - vi.start_time)
                        dfull_size_b = cursize - vi.start_size if vi.has_flag(VideoInfo.Flags.FILE_WAS_CREATED) else 0
                        dfull_speed_kb = ((dfull_size_b / Mem.KB) / dfull_seconds) if dfull_seconds and dfull_size_b >= Mem.KB else 0.0
                        dfull_speed_str = f'{dfull_speed_kb:.1f}' if dfull_speed_kb >= 0.1 else '???.?'
                        dfull_time_str = format_time(dfull_seconds) if dfull_speed_kb >= 0.1 else '??:??:??'
                        dfull_str = f'{dfull_size_b / Mem.MB:.2f} Mb in {dfull_time_str}, avg {dfull_speed_str} Kb/s'
                        d_seconds = max(0, elapsed_seconds - vi.last_check_time)
                        d_size_b = cursize - vi.last_check_size if vi.has_flag(VideoInfo.Flags.FILE_WAS_CREATED) else 0
                        d_speed_kb = ((d_size_b / Mem.KB) / d_seconds) if d_seconds and d_size_b >= Mem.KB else 0.0
                        speed_str = f'{d_speed_kb:.1f}' if d_speed_kb >= 0.1 else '???.?'
                        eta_str = (format_time(0) if vi.expected_size == cursize else
                                   format_time(int((remsize / Mem.KB) / d_speed_kb)) if remsize and d_speed_kb >= 0.1 else '??:??:??')
                        item_states.append(f' {vi.my_sfolder}{PREFIX}{vi.id:d}:'
                                           f' {cursize_str} / {totalsize_str} Mb ({size_pct}%),'
                                           f' {speed_str} Kb/s, ETA: {eta_str} ({dfull_str})')
                        vi.last_check_size = cursize
                        vi.last_check_time = elapsed_seconds
                    Log.debug('\n'.join(item_states))

    async def _continue_file_checker(self) -> None:
        if not Config.store_continue_cmdfile:
            return
        minmax_id = self._minmax_id
        continue_file_name = f'{PREFIX}{START_TIME.strftime("%Y-%m-%d_%H_%M_%S")}_{minmax_id[0]:d}-{minmax_id[1]:d}.continue.conf'
        continue_file_fullpath = f'{Config.dest_base}{continue_file_name}'
        arglist_base = Config.make_continue_arguments()
        base_sleep_time = calc_sleep_time(3.0)
        write_delay = DOWNLOAD_CONTINUE_FILE_CHECK_TIMER
        last_check_seconds = 0
        while self.get_workload_size() + self.get_scanner_workload_size() > 0:
            elapsed_seconds = get_elapsed_time_i()
            if elapsed_seconds >= write_delay and elapsed_seconds - last_check_seconds >= write_delay:
                last_check_seconds = elapsed_seconds
                v_ids = sorted(vi.id for vi in self._seq + [qvi for qvi in getattr(self._queue, '_queue')] + self._downloads_active
                               + self.get_scanner_workload())
                arglist = ['-seq', f'({"~".join(f"id={idi:d}" for idi in v_ids)})'] if len(v_ids) > 1 else ['-start', str(v_ids[0])]
                arglist.extend(arglist_base)
                try:
                    Log.trace(f'Storing continue file to \'{continue_file_name}\'...')
                    if not path.isdir(Config.dest_base):
                        makedirs(Config.dest_base)
                    with open(continue_file_fullpath, 'wt', encoding=UTF8, buffering=1) as cfile:
                        cfile.write('\n'.join(str(e) for e in arglist))
                except (OSError, IOError):
                    Log.error(f'Unable to save continue file to \'{continue_file_name}\'!')
            await sleep(base_sleep_time)
        if path.isfile(continue_file_fullpath):
            Log.trace(f'All files downloaded. Removing continue file \'{continue_file_name}\'...')
            remove(continue_file_fullpath)

    async def _after_download(self) -> None:
        newline = '\n'
        Log.info(f'\nDone. {self._downloaded_count:d} / {self._orig_count:d}+{self._filtered_count_pre:d}'
                 f'{f"+{self._scn.get_extra_count():d}" if Config.lookahead else ""} file(s) downloaded, '
                 f'{self._filtered_count_after:d}+{self._filtered_count_pre:d} already existed, '
                 f'{self._skipped_count:d} skipped, {self._404_count:d} not found')
        workload_size = len(self._seq) + self.get_scanner_workload_size()
        if workload_size > 0:
            Log.fatal(f'total queue is still at {workload_size:d} != 0!')
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
        if len(self._downloads_active) > 0:
            active_items = sorted([vi for vi in self._downloads_active if path.isfile(vi.my_fullpath)
                                   and vi.has_flag(VideoInfo.Flags.FILE_WAS_CREATED)], key=lambda vi: vi.id)
            if Config.keep_unfinished:
                unfinished_str = '\n '.join(f'{i + 1:d}) {vi.my_fullpath}' for i, vi in enumerate(active_items))
                Log.debug(f'at_interrupt: keeping {len(active_items):d} unfinished file(s):\n {unfinished_str}')
                return
            for vi in active_items:
                Log.debug(f'at_interrupt: trying to remove \'{vi.my_fullpath}\'...')
                remove(vi.my_fullpath)

    @property
    def session(self) -> ClientSession:
        return self._session

    def is_writing(self, videst: Union[VideoInfo, str]) -> bool:
        return (videst.my_fullpath if isinstance(videst, VideoInfo) else videst) in self._writes_active

    def add_to_writes(self, vi: VideoInfo) -> None:
        self._writes_active.append(vi.my_fullpath)

    def remove_from_writes(self, vi: VideoInfo) -> None:
        self._writes_active.remove(vi.my_fullpath)

    def waiting_for_scanner(self) -> bool:
        return self._scn and not self._scn.done()

    def get_scanner_workload_size(self) -> int:
        return self._scn.get_workload_size() if self.waiting_for_scanner() else 0

    def get_scanner_workload(self) -> List[VideoInfo]:
        return self._scn.get_workload() if self.waiting_for_scanner() else []

    def can_fetch_next(self) -> bool:
        return self.waiting_for_scanner() or not not self._seq

    def get_workload_size(self) -> int:
        return len(self._seq) + self._queue.qsize() + len(self._downloads_active)

    async def _try_fetch_next(self) -> Optional[VideoInfo]:
        if self._seq:
            vi = self._seq[0]
            del self._seq[0]
        else:
            assert self._scn
            vi = await self._scn.try_fetch_next()
        return vi

#
#
#########################################
