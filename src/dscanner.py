# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations
from asyncio.tasks import sleep
from collections import deque
from collections.abc import Callable, Coroutine
from contextlib import suppress
from typing import Any

from config import Config
from defs import DownloadResult, QUALITIES
from logger import Log
from path_util import file_already_exists_arr
from vinfo import VideoInfo, get_min_max_ids

__all__ = ('VideoScanWorker',)


class VideoScanWorker:
    """
    VideoInfo queue processor. Scans download queue and prepares VideoInfo objects for actual downloader\n
    The main purpose of it being separated from VideoDownloadWorker is to scan videos independently,
    being able to continue even if downloader's active queue is full
    """
    _instance: VideoScanWorker | None = None

    @staticmethod
    def get() -> VideoScanWorker | None:
        return VideoScanWorker._instance

    def __init__(self, sequence: list[VideoInfo], func: Callable[[VideoInfo], Coroutine[Any, Any, DownloadResult]]) -> None:
        assert VideoScanWorker._instance is None
        VideoScanWorker._instance = self

        self._original_sequence = sequence
        self._func = func
        self._seq = deque(sequence)

        self._orig_count = len(self._seq)
        self._scan_count = 0
        self._404_counter = 0
        self._extra_ids: list[int] = list()
        self._scanned_items = deque[VideoInfo]()
        self._task_finish_callback: Callable[[VideoInfo, DownloadResult], Coroutine[Any, Any, None]] | None = None

        self._id_gaps: list[tuple[int, int]] = list()

    def _extend_with_extra(self) -> None:
        extra_cur = Config.lookahead - self._404_counter
        if extra_cur > 0:
            last_id = Config.end_id + len(self._extra_ids)
            extra_idseq = [(last_id + i + 1) for i in range(extra_cur)]
            extra_vis = [VideoInfo(idi) for idi in extra_idseq]
            minid, maxid = get_min_max_ids(extra_vis)
            Log.warn(f'[lookahead] extending queue after {last_id:d} with {extra_cur:d} extra ids: {minid:d}-{maxid:d}')
            self._seq.extend(extra_vis)
            self._original_sequence.extend(extra_vis)
            self._extra_ids.extend(extra_idseq)

    async def _at_scan_finish(self, vi: VideoInfo, result: DownloadResult) -> None:
        self._scan_count += 1
        if result in (DownloadResult.FAIL_NOT_FOUND, DownloadResult.FAIL_RETRIES,
                      DownloadResult.FAIL_DELETED, DownloadResult.FAIL_FILTERED_OUTER, DownloadResult.FAIL_SKIPPED):
            founditems = list(filter(None, [file_already_exists_arr(vi.id, q) for q in QUALITIES]))
            if any(ffs for ffs in founditems):
                newline = '\n'
                Log.info(f'{vi.sname} scan returned {str(result)} but it was already downloaded:'
                         f'\n - {f"{newline} - ".join(f"{newline} - ".join(ffs) for ffs in founditems)}')
        if result == DownloadResult.SUCCESS:
            self._scanned_items.append(vi)
        else:
            if result == DownloadResult.FAIL_NOT_FOUND:
                vi.set_flag(VideoInfo.Flags.RETURNED_404)
            assert self._task_finish_callback
            await self._task_finish_callback(vi, result)

        if Config.detect_id_gaps and Config.is_pages is False and result != DownloadResult.FAIL_NOT_FOUND and self._404_counter:
            self._id_gaps.append((vi.id - self._404_counter, vi.id))

        self._404_counter = self._404_counter + 1 if result == DownloadResult.FAIL_NOT_FOUND else 0
        if len(self._seq) == 1 and not not Config.lookahead:
            self._extend_with_extra()

    async def run(self) -> None:
        Log.debug('[queue] scanner thread start')
        while self._seq:
            result = await self._func(self._seq[0])
            await self._at_scan_finish(self._seq[0], result)
            self._seq.popleft()
        Log.debug('[queue] scanner thread stop: scan complete')
        if self._id_gaps:
            gap_strings = list()
            mod3_count = 0
            for gstart, gstop in self._id_gaps[1:]:
                is_mod3 = (gstop + 1 - gstart) % 3 == 0
                mod3_count += 1 if is_mod3 else 0
                gstring = f'({gstart:d} - {gstop:d}) {"(%3)!" if is_mod3 else ""}'
                gap_strings.append(gstring)
            n = '\n - '
            Log.debug(f'[gaps scanner] detected {len(self._id_gaps):d} id gaps:{n}{n.join(gap_strings)}')
            if mod3_count > 0 and mod3_count + 1 == len(self._id_gaps):
                Log.debug('[gaps scanner] all gaps are (%3)!')

    def done(self) -> bool:
        return self.get_workload_size() == 0

    def get_done_count(self) -> int:
        return self._scan_count

    def get_workload_size(self) -> int:
        return len(self._seq) + len(self._scanned_items)

    def get_workload(self) -> list[VideoInfo]:
        return list(self._seq) + list(self._scanned_items)

    def get_prescanned_count(self) -> int:
        return len(self._scanned_items)

    def get_extra_count(self) -> int:
        return len(self._extra_ids)

    def get_extra_ids(self) -> list[int]:
        return self._extra_ids

    def register_task_finish_callback(self, callack: Callable[[VideoInfo, DownloadResult], Coroutine[Any, Any, None]]) -> None:
        self._task_finish_callback = callack

    async def try_fetch_next(self) -> VideoInfo | None:
        while not self._scanned_items and not self.done():
            await sleep(0.1)
        return self._scanned_items.popleft() if self._scanned_items else None

    def find_vinfo(self, id_: int) -> VideoInfo | None:
        with suppress(StopIteration):
            return next(filter(lambda vi: vi.id == id_, self._original_sequence))

#
#
#########################################
