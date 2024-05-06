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
from typing import List, Deque, Coroutine, Any, Callable, Optional, Iterable

from defs import DownloadResult
from vinfo import VideoInfo

__all__ = ('VideoScanWorker',)


class VideoScanWorker:
    """
    VideoInfo queue processor. Scans download queue and prepares VideoInfo objects for actual downloader\n
    The main purpose of it being separated from VideoDownloadWorker is to scan videos independently,
    being able to continue even if downloader's active queue is full
    """
    _instance = None  # type: Optional[VideoScanWorker]

    @staticmethod
    def get() -> Optional[VideoScanWorker]:
        return VideoScanWorker._instance

    def __init__(self, sequence: Iterable[VideoInfo], func: Callable[[VideoInfo], Coroutine[Any, Any, DownloadResult]]) -> None:
        assert VideoScanWorker._instance is None
        VideoScanWorker._instance = self

        self._func = func
        self._seq = deque(sequence)

        self._scanned_items = deque()  # type: Deque[VideoInfo]
        self._task_finish_callback = None  # type: Optional[Callable[[VideoInfo, DownloadResult], Coroutine[Any, Any, None]]]

    async def _at_scan_finish(self, vi: VideoInfo, result: DownloadResult) -> None:
        # Log.trace(f'[queue] {vi.sname} scan finished (result: {result})')
        if result == DownloadResult.SUCCESS:
            self._scanned_items.append(vi)
        else:
            assert self._task_finish_callback
            await self._task_finish_callback(vi, result)

    async def run(self) -> None:
        while self._seq:
            # Log.trace(f'[queue] {self._seq[0].sname} scan started...')
            result = await self._func(self._seq[0])
            await self._at_scan_finish(self._seq[0], result)
            self._seq.popleft()

    def done(self) -> bool:
        return self.get_workload_size() == 0

    def get_workload_size(self) -> int:
        return len(self._seq) + len(self._scanned_items)

    def get_workload(self) -> List[VideoInfo]:
        return list(self._seq) + list(self._scanned_items)

    def get_prescanned_count(self) -> int:
        return len(self._scanned_items)

    def register_task_finish_callback(self, callack: Callable[[VideoInfo, DownloadResult], Coroutine[Any, Any, None]]) -> None:
        self._task_finish_callback = callack

    async def try_fetch_next(self) -> Optional[VideoInfo]:
        while not self._scanned_items and not self.done():
            await sleep(0.1)
        return self._scanned_items.popleft() if self._scanned_items else None

#
#
#########################################
