# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations

from asyncio import CancelledError, Task, get_running_loop
from asyncio.tasks import sleep
from collections import deque
from collections.abc import Callable, Coroutine
from typing import Any, TypeAlias

from .config import Config
from .defs import (
    LOOKAHEAD_WATCH_RESCAN_DELAY_MAX,
    LOOKAHEAD_WATCH_RESCAN_DELAY_MIN,
    QUALITIES,
    RESCAN_DELAY_EMPTY,
    SCAN_CANCEL_KEYCOUNT,
    SCAN_CANCEL_KEYSTROKE,
    DownloadResult,
)
from .iinfo import VideoInfo, get_min_max_ids
from .input import wait_for_key
from .logger import Log
from .path_util import file_already_exists_arr
from .util import get_local_time_s

__all__ = ('VideoScanWorker',)

Func_T: TypeAlias = Callable[[VideoInfo], Coroutine[Any, Any, DownloadResult]]
Callback_T: TypeAlias = Callable[[VideoInfo, DownloadResult], Coroutine[Any, Any, None]]


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

    def __enter__(self) -> VideoScanWorker:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        VideoScanWorker._instance = None

    def __init__(self, sequence: list[VideoInfo], func: Func_T) -> None:
        assert VideoScanWorker._instance is None
        VideoScanWorker._instance = self

        self._original_sequence: list[VideoInfo] = sequence
        self._func: Func_T = func
        self._seq: deque[VideoInfo] = deque(sequence)

        self._orig_count: int = len(self._original_sequence)
        self._scan_count: int = 0
        self._404_counter: int = 0
        self._last_non404_id: int = self._original_sequence[0].id - 1
        self._extra_ids: list[int] = []
        self._scanned_items: deque[VideoInfo] = deque()
        self._task_finish_callback: Callback_T | None = None

        self._sleep_waiter: Task | None = None
        self._abort_waiter: Task | None = None

        self._id_gaps: list[tuple[int, int]] = []

    def _on_abort(self) -> None:
        Log.warn('[queue] scanner thread interrupted, finishing pending tasks...')
        Config.on_scan_abort()
        if self._sleep_waiter:
            self._sleep_waiter.cancel()
            self._sleep_waiter: Task | None = None
        self._abort_waiter: Task | None = None

    @staticmethod
    async def _sleep_task(sleep_time: int) -> None:
        try:
            await sleep(float(sleep_time))
        except CancelledError:
            pass

    async def _extend_with_extra(self) -> int:
        lookahead_abs = abs(Config.lookahead)
        watcher_mode = Config.lookahead < 0 and bool(self._extra_ids) and self._404_counter >= lookahead_abs
        last_id = self._last_non404_id + self._404_counter
        extra_cur = lookahead_abs - self._404_counter
        if watcher_mode:
            back_step = min(lookahead_abs, len(self._original_sequence) - 2)
            last_id = self._last_non404_id - back_step
            extra_cur = lookahead_abs + back_step
        if extra_cur > 0:
            extra_idseq = [(last_id + i + 1) for i in range(extra_cur)]
            extra_vis = [VideoInfo(idi) for idi in extra_idseq]
            minid, maxid = get_min_max_ids(extra_vis)
            self._seq.extend(extra_vis)
            self._original_sequence.extend(extra_vis)
            self._extra_ids.extend(extra_idseq)
            if not watcher_mode:
                Log.warn(f'[lookahead] extending queue after {last_id:d} with {extra_cur:d} extra ids: {minid:d}-{maxid:d}')
            else:
                rescan_delay = min(LOOKAHEAD_WATCH_RESCAN_DELAY_MAX, max(lookahead_abs * 10, LOOKAHEAD_WATCH_RESCAN_DELAY_MIN))
                Log.warn(f'[watcher] extending queue after {last_id:d} with {extra_cur:d} extra ids: {minid:d}-{maxid:d}'
                         f' (waiting {rescan_delay:d} seconds, next re-scan at [{get_local_time_s(offset=rescan_delay)}])')
                return rescan_delay
        return 0

    async def _at_scan_finish(self, vi: VideoInfo, result: DownloadResult) -> int:
        if result in (DownloadResult.FAIL_EMPTY_HTML,):
            return RESCAN_DELAY_EMPTY

        self._scan_count += 1
        self._seq.popleft()
        if result in (DownloadResult.FAIL_NOT_FOUND, DownloadResult.FAIL_RETRIES,
                      DownloadResult.FAIL_DELETED, DownloadResult.FAIL_FILTERED_OUTER, DownloadResult.FAIL_SKIPPED):
            founditems = list(filter(None, (file_already_exists_arr(vi.id, q) for q in QUALITIES)))
            if any(ffs for ffs in founditems):
                newline = '\n'
                Log.info(f'{vi.sname} scan returned {result!s} but it was already downloaded:'
                         f'\n - {f"{newline} - ".join(f"{newline} - ".join(ffs) for ffs in founditems)}')
        if result == DownloadResult.SUCCESS:
            self._scanned_items.append(vi)
        else:
            if result == DownloadResult.FAIL_NOT_FOUND:
                vi.set_flag(VideoInfo.Flags.RETURNED_404)
            assert self._task_finish_callback
            await self._task_finish_callback(vi, result)

        if Config.detect_id_gaps and not Config.is_pages and not Config.watcher_mode:
            if result != DownloadResult.FAIL_NOT_FOUND and self._404_counter:
                self._id_gaps.append((vi.id - self._404_counter, vi.id))

        self._404_counter = self._404_counter + 1 if result == DownloadResult.FAIL_NOT_FOUND else 0
        if result != DownloadResult.FAIL_NOT_FOUND:
            self._last_non404_id = vi.id
        if len(self._seq) == 0 and Config.lookahead:
            return await self._extend_with_extra()
        return 0

    async def run(self) -> None:
        Log.debug('[queue] scanner thread start')
        self._abort_waiter = get_running_loop().create_task(wait_for_key(SCAN_CANCEL_KEYSTROKE, SCAN_CANCEL_KEYCOUNT, self._on_abort))
        while self._seq:
            if Config.aborted:
                self._seq.clear()
                continue
            result = await self._func(self._seq[0])
            sleep_time = await self._at_scan_finish(self._seq[0], result)
            if sleep_time:
                self._sleep_waiter = get_running_loop().create_task(self._sleep_task(sleep_time))
                await self._sleep_waiter
                self._sleep_waiter = None
        if self._abort_waiter:
            self._abort_waiter.cancel()
            self._abort_waiter = None
        Log.debug('[queue] scanner thread stop: scan complete')
        if self._id_gaps:
            gap_strings: list[str] = []
            mod2_count = mod3_count = mod4_count = 0
            for gstart, gstop in self._id_gaps[1:]:
                is_mod2, is_mod3, is_mod4 = tuple((1 + gstop - gstart) % _ == 0 for _ in (2, 3, 4))
                mod2_count, mod3_count, mod4_count = tuple(map(sum, zip(
                    (mod2_count, mod3_count, mod4_count), (is_mod2, is_mod3, is_mod4), strict=True)))
                gstring = (f'({gstart:d} - {gstop:d})'
                           f'{"".join(f" %{modval:d}" for b, modval in zip((is_mod2, is_mod3, is_mod4), (2, 3, 4), strict=True) if b)}')
                gap_strings.append(gstring)
            n = '\n - '
            Log.debug(f'[gaps scanner] detected {len(self._id_gaps):d} id gaps:{n}{n.join(gap_strings)}')
            for modcount, modval in zip((mod2_count, mod3_count, mod4_count), (2, 3, 4), strict=True):
                if 0 < modcount == len(self._id_gaps) - 1:
                    Log.debug(f'[gaps scanner] all gaps are (%{modval:d})!')

    def done(self) -> bool:
        return self.get_workload_size() == 0

    def has_found_any(self) -> bool:
        return self._last_non404_id >= self._original_sequence[0].id

    def watcher_wait_active(self) -> bool:
        return self._sleep_waiter is not None

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

    def find_vinfo_pred(self, pred: Callable[[VideoInfo], bool]) -> VideoInfo | None:
        return next((vi for vi in self._original_sequence if pred(vi)), None)

    def find_vinfo_last(self, id_: int) -> VideoInfo | None:
        return next((vi for vi in reversed(self._original_sequence) if vi.id == id_), None)

#
#
#########################################
