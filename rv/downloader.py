# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations

import itertools
import os
from asyncio import Lock as AsyncLock
from asyncio.queues import Queue as AsyncQueue
from asyncio.tasks import as_completed, sleep
from collections import deque
from collections.abc import Callable, Coroutine
from typing import Any, TypeAlias

from .config import Config
from .defs import (
    DOWNLOAD_CONTINUE_FILE_CHECK_TIMER,
    DOWNLOAD_QUEUE_STALL_CHECK_TIMER,
    MAX_VIDEOS_QUEUE_SIZE,
    PREFIX,
    START_TIME,
    UTF8,
    DownloadResult,
    Mem,
)
from .dscanner import VideoScanWorker
from .iinfo import VideoInfo, get_min_max_ids
from .logger import Log
from .util import calc_sleep_time, format_time, get_elapsed_time_i, get_elapsed_time_s

__all__ = ('VideoDownloadWorker',)

Func_T: TypeAlias = Callable[[VideoInfo], Coroutine[Any, Any, DownloadResult]]


class VideoDownloadWorker:
    """
    Async queue wrapper which binds list of lists of arguments to a download function call and processes them
    asynchronously with a limit of simulteneous downloads defined by MAX_VIDEOS_QUEUE_SIZE
    """
    _instance: VideoDownloadWorker | None = None

    @staticmethod
    def get() -> VideoDownloadWorker | None:
        return VideoDownloadWorker._instance

    def __enter__(self) -> VideoDownloadWorker:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        VideoDownloadWorker._instance = None

    def __init__(self, sequence: list[VideoInfo], func: Func_T, filtered_count: int) -> None:
        assert VideoDownloadWorker._instance is None
        VideoDownloadWorker._instance = self

        self._scn: VideoScanWorker | None = VideoScanWorker.get()

        self._func: Func_T = func
        self._seq: deque[VideoInfo] = deque()
        self._queue: AsyncQueue[VideoInfo] = AsyncQueue(MAX_VIDEOS_QUEUE_SIZE)
        self._orig_count: int = len(sequence)
        self._downloaded_count: int = 0
        self._prefiltered_count: int = filtered_count
        self._already_exist_count: int = 0
        self._skipped_count: int = 0
        self._404_count: int = 0
        self._minmax_id: tuple[int, int] = get_min_max_ids(sequence)

        self._downloads_active: list[VideoInfo] = []
        self._writes_active: list[VideoInfo] = []
        self._failed_items: list[int] = []

        self._total_queue_size_last: int = 0
        self._download_queue_size_last: int = 0
        self._write_queue_size_last: int = 0

        self._sequence_lock: AsyncLock = AsyncLock()
        self._active_downloads_lock: AsyncLock = AsyncLock()
        self._active_writes_lock: AsyncLock = AsyncLock()

        if self._scn:
            self._scn.register_task_finish_callback(self._at_task_finish)
        else:
            self._seq.extend(sequence)  # form our own container to erase from

    async def _at_task_start(self, vi: VideoInfo) -> None:
        async with self._active_downloads_lock:
            self._downloads_active.append(vi)
        vi.set_state(VideoInfo.State.ACTIVE)
        Log.trace(f'[queue] {vi.sname} added to active')

    async def _at_task_finish(self, vi: VideoInfo, result: DownloadResult) -> None:
        if vi in self._downloads_active and not (Config.watcher_mode and vi in self._writes_active):
            async with self._active_downloads_lock:
                self._downloads_active.remove(vi)
            Log.trace(f'[queue] {vi.sname} removed from active')
        if result == DownloadResult.FAIL_ALREADY_EXISTS:
            self._already_exist_count += 1
        elif result in (DownloadResult.FAIL_SKIPPED, DownloadResult.FAIL_FILTERED_OUTER):
            self._skipped_count += 1
        elif result in (DownloadResult.FAIL_NOT_FOUND, DownloadResult.FAIL_DELETED):
            self._404_count += 1
        elif result == DownloadResult.FAIL_RETRIES:
            self._failed_items.append(vi.id)
        elif result == DownloadResult.SUCCESS:
            self._downloaded_count += 1

    async def _prod(self) -> None:
        while True:
            async with self._sequence_lock:
                if self.can_fetch_next() is False:
                    break
                qfull = self._queue.full()
            if qfull is False:
                vi = await self._try_fetch_next()
                if vi:
                    vi.set_state(VideoInfo.State.QUEUED)
                    await self._queue.put(vi)
            else:
                await sleep(0.2)

    async def _cons(self) -> None:
        while True:
            async with self._sequence_lock:
                can_fetch = self.can_fetch_next()
                qsize = self._queue.qsize()
            if can_fetch is False and qsize == 0:
                break
            async with self._active_downloads_lock:
                dsize = len(self._downloads_active)
            if qsize > 0 and dsize < MAX_VIDEOS_QUEUE_SIZE:
                vi = await self._queue.get()
                await self._at_task_start(vi)
                result = await self._func(vi)
                await self._at_task_finish(vi, result)
                self._queue.task_done()
            else:
                await sleep(0.35)

    async def _state_reporter(self) -> None:
        force_check_secs = DOWNLOAD_QUEUE_STALL_CHECK_TIMER
        last_check_secs = 0
        while self.get_workload_size() > 0 or self.waiting_for_scanner():
            await sleep(calc_sleep_time(3.0) if len(self._seq) + self._queue.qsize() > 0 or self.waiting_for_scanner() else 1.0)
            queue_size = len(self._seq) + self.get_scanner_workload_size()
            ready_size = self._queue.qsize()
            scan_count = self.get_scanned_count()
            extra_count = max(0, scan_count - self._orig_count)
            download_count = len(self._downloads_active)
            write_count = len(self._writes_active)
            queue_last = self._total_queue_size_last
            downloading_last = self._download_queue_size_last
            write_last = self._write_queue_size_last
            elapsed_seconds = get_elapsed_time_i()
            force_check = elapsed_seconds - last_check_secs >= force_check_secs and bool(write_count or not self.waiting_for_watcher())
            if queue_last != queue_size or downloading_last != download_count or write_last != write_count or force_check:
                scan_msg = f'scanned: {f"{min(scan_count, self._orig_count)}+{extra_count:d}" if Config.lookahead else str(scan_count)}'
                prescan_msg = f' (prescanned: {self._scn.get_prescanned_count():d})' if self._scn else ''
                Log.info(f'[{get_elapsed_time_s()}] {scan_msg}, queue: {queue_size:d}{prescan_msg}, ready: {ready_size:d}, '
                         f'active: {download_count:d} (writing: {write_count:d})')
                last_check_secs = elapsed_seconds
                self._total_queue_size_last = queue_size
                self._download_queue_size_last = download_count
                self._write_queue_size_last = write_count
                wc_threshold = MAX_VIDEOS_QUEUE_SIZE // (2 - int(force_check))
                if force_check or (queue_size == 0 and download_count == write_count <= wc_threshold):
                    item_states: list[str] = []
                    for vi in self._downloads_active:
                        cursize = os.stat(vi.my_fullpath).st_size if os.path.isfile(vi.my_fullpath) else 0
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
                        eta_str = (format_time(0) if cursize and vi.expected_size == cursize else
                                   format_time(int((remsize / Mem.KB) / d_speed_kb)) if remsize and d_speed_kb >= 0.1 else '??:??:??')
                        item_states.append(f' {vi.my_sfolder}{PREFIX}{vi.id:d}:'
                                           f' {cursize_str} / {totalsize_str} Mb ({size_pct}%),'
                                           f' {speed_str} Kb/s, ETA: {eta_str} ({dfull_str})')
                        vi.last_check_size = cursize
                        vi.last_check_time = elapsed_seconds
                    if item_states:
                        Log.debug('\n'.join(item_states))

    async def _continue_file_checker(self) -> None:
        if not Config.store_continue_cmdfile:
            return
        minmax_id = self._minmax_id
        continue_file_name = f'{PREFIX}{START_TIME.strftime("%Y-%m-%d_%H_%M_%S")}_{minmax_id[0]:d}-{minmax_id[1]:d}.continue.conf'
        continue_file_fullpath = f'{Config.dest_base}{continue_file_name}'
        arglist_base = Config.make_continue_arguments()
        write_delay = DOWNLOAD_CONTINUE_FILE_CHECK_TIMER
        last_check_seconds = 0
        while self.get_workload_size() + self.get_scanner_workload_size() > 0:
            elapsed_seconds = get_elapsed_time_i()
            if elapsed_seconds >= write_delay and elapsed_seconds - last_check_seconds >= write_delay:
                last_check_seconds = elapsed_seconds
                v_ids: list[int] = sorted(
                    vi.id for vi in itertools.chain(
                        self._seq, getattr(self._queue, '_queue'), self._downloads_active, self.get_scanner_workload()))
                arglist = ['-seq', f'({"~".join(f"id={idi:d}" for idi in v_ids)})'] if len(v_ids) > 1 else ['-start', str(v_ids[0])]
                arglist.extend(arglist_base)
                try:
                    Log.trace(f'Storing continue file to \'{continue_file_name}\'...')
                    if not os.path.isdir(Config.dest_base):
                        os.makedirs(Config.dest_base)
                    with open(continue_file_fullpath, 'wt', encoding=UTF8, buffering=1) as cfile:
                        cfile.write('\n'.join(str(e) for e in arglist))
                except OSError:
                    Log.error(f'Unable to save continue file to \'{continue_file_name}\'!')
            await sleep(calc_sleep_time(3.0))
        if not Config.aborted and os.path.isfile(continue_file_fullpath):
            Log.trace(f'All files downloaded. Removing continue file \'{continue_file_name}\'...')
            os.remove(continue_file_fullpath)

    async def _after_download(self) -> None:
        newline = '\n'
        Log.info(f'\nDone. {self._downloaded_count:d} / {self._orig_count:d}+{self._prefiltered_count:d}'
                 f'{f"+{self._scn.get_extra_count():d}" if Config.lookahead else ""} file(s) downloaded, '
                 f'{self._already_exist_count:d}+{self._prefiltered_count:d} already existed, '
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
        await self._queue.join()

    def at_interrupt(self) -> None:
        if len(self._downloads_active) > 0:
            active_items = sorted([vi for vi in self._downloads_active if os.path.isfile(vi.my_fullpath)
                                   and vi.has_flag(VideoInfo.Flags.FILE_WAS_CREATED)], key=lambda vi: vi.id)
            if Config.keep_unfinished:
                unfinished_str = '\n '.join(f'{i + 1:d}) {vi.my_fullpath}' for i, vi in enumerate(active_items))
                Log.debug(f'at_interrupt: keeping {len(active_items):d} unfinished file(s):\n {unfinished_str}')
                return
            for vi in active_items:
                Log.debug(f'at_interrupt: trying to remove \'{vi.my_fullpath}\'...')
                os.remove(vi.my_fullpath)

    async def is_writing(self, vi: VideoInfo) -> bool:
        async with self._active_writes_lock:
            return vi in self._writes_active

    async def add_to_writes(self, vi: VideoInfo) -> None:
        async with self._active_writes_lock:
            self._writes_active.append(vi)

    async def remove_from_writes(self, vi: VideoInfo, safe=False) -> None:
        async with self._active_writes_lock:
            if safe is False or vi in self._writes_active:
                self._writes_active.remove(vi)

    def waiting_for_scanner(self) -> bool:
        return self._scn and not self._scn.done()

    def get_scanned_count(self) -> int:
        return self._scn.get_done_count() if self._scn else 0

    def get_scanner_workload_size(self) -> int:
        return self._scn.get_workload_size() if self.waiting_for_scanner() else 0

    def get_scanner_workload(self) -> list[VideoInfo]:
        return self._scn.get_workload() if self.waiting_for_scanner() else []

    def can_fetch_next(self) -> bool:
        return self.waiting_for_scanner() or bool(self._seq)

    def get_workload_size(self) -> int:
        return len(self._seq) + self._queue.qsize() + len(self._downloads_active)

    def waiting_for_watcher(self) -> bool:
        return self._scn and self._scn.watcher_wait_active()

    async def _try_fetch_next(self) -> VideoInfo | None:
        async with self._sequence_lock:
            if self._seq:
                vi = self._seq.popleft()
            else:
                assert self._scn
                vi = await self._scn.try_fetch_next()
            return vi

#
#
#########################################
