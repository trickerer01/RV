# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio.queues import Queue as AsyncQueue
from asyncio.tasks import sleep, as_completed
from typing import List, Tuple, Coroutine, Any, Callable, MutableSequence

from aiohttp import ClientSession

from defs import (
    MAX_VIDEOS_QUEUE_SIZE, VideoInfo, Log, ExtraConfig, DownloadResult, prefixp, calc_sleep_time, get_elapsed_time_i, get_elapsed_time_s,
)
from fetch_html import make_session
from tagger import dump_item_tags

__all__ = ('DownloadWorker',)


class DownloadWorker:
    """
    Async queue wrapper which binds list of lists of arguments to a download function call and processes them
    asynchronously with a limit of simulteneous downloads defined by MAX_VIDEOS_QUEUE_SIZE
    """
    def __init__(self, my_sequence: MutableSequence[VideoInfo], func: Callable[[VideoInfo], Coroutine[Any, Any, DownloadResult]],
                 filtered_count: int, session: ClientSession = None) -> None:
        self._func = func
        self._seq = my_sequence
        self._queue = AsyncQueue(MAX_VIDEOS_QUEUE_SIZE)  # type: AsyncQueue[Tuple[int, Coroutine[Any, Any, DownloadResult]]]
        self.session = session
        self.orig_count = len(self._seq)
        self.downloaded_count = 0
        self.filtered_count_pre = filtered_count
        self.filtered_count_after = 0
        self.skipped_count = 0

        self._downloads_active = list()  # type: List[int]
        self.writes_active = list()  # type: List[str]
        self.failed_items = list()  # type: List[int]

        self._total_queue_size_last = 0
        self._download_queue_size_last = 0
        self._write_queue_size_last = 0

    async def _at_task_start(self, idi: int) -> None:
        self._downloads_active.append(idi)
        Log.trace(f'[queue] {prefixp()}{idi:d}.mp4 added to queue')

    async def _at_task_finish(self, idi: int, result: DownloadResult) -> None:
        self._downloads_active.remove(idi)
        Log.trace(f'[queue] {prefixp()}{idi:d}.mp4 removed from queue')
        if result == DownloadResult.DOWNLOAD_FAIL_ALREADY_EXISTS:
            self.filtered_count_after += 1
        elif result == DownloadResult.DOWNLOAD_FAIL_SKIPPED:
            self.skipped_count += 1
        elif result == DownloadResult.DOWNLOAD_FAIL_RETRIES:
            self.failed_items.append(idi)
        elif result == DownloadResult.DOWNLOAD_SUCCESS:
            self.downloaded_count += 1

    async def _prod(self) -> None:
        while len(self._seq) > 0:
            if self._queue.full() is False:
                await self._queue.put((self._seq[0].my_id, self._func(self._seq[0])))
                del self._seq[0]
            else:
                await sleep(0.1)

    async def _cons(self) -> None:
        while len(self._seq) + self._queue.qsize() > 0:
            if self._queue.empty() is False and len(self._downloads_active) < MAX_VIDEOS_QUEUE_SIZE:
                idi, task = await self._queue.get()
                await self._at_task_start(idi)
                result = await task
                await self._at_task_finish(idi, result)
                self._queue.task_done()
            else:
                await sleep(0.35)

    async def _state_reporter(self) -> None:
        base_sleep_time = calc_sleep_time(3.0)
        last_check_seconds = 0
        while len(self._seq) + self._queue.qsize() + len(self._downloads_active) > 0:
            await sleep(base_sleep_time if len(self._seq) + self._queue.qsize() > 0 else 1.0)
            queue_size = len(self._seq) + self._queue.qsize()
            download_count = len(self._downloads_active)
            write_count = len(self.writes_active)
            queue_last = self._total_queue_size_last
            downloading_last = self._download_queue_size_last
            write_last = self._write_queue_size_last
            elapsed_seconds = get_elapsed_time_i()
            force_check = elapsed_seconds >= 60 and elapsed_seconds - last_check_seconds >= 60
            if queue_last != queue_size or downloading_last != download_count or write_last != write_count or force_check:
                Log.info(f'[{get_elapsed_time_s()}] queue: {queue_size:d}, downloading: {download_count:d} (writing: {write_count:d})')
                last_check_seconds = elapsed_seconds
                self._total_queue_size_last = queue_size
                self._download_queue_size_last = download_count
                self._write_queue_size_last = write_count

    async def _after_download(self) -> None:
        newline = '\n'
        Log.info(f'\nDone. {self.downloaded_count:d} / {self.orig_count:d}+{self.filtered_count_pre:d} files downloaded, '
                 f'{self.filtered_count_after:d}+{self.filtered_count_pre:d} already existed, '
                 f'{self.skipped_count:d} skipped')
        if len(self._seq) > 0:
            Log.fatal(f'total queue is still at {len(self._seq):d} != 0!')
        if len(self.writes_active) > 0:
            Log.fatal(f'active writes count is still at {len(self.writes_active):d} != 0!')
        if len(self.failed_items) > 0:
            Log.fatal(f'Failed items:\n{newline.join(str(fi) for fi in sorted(self.failed_items))}')

    async def run(self) -> None:
        async with self.session or await make_session() as self.session:
            for cv in as_completed([self._prod(), self._state_reporter()] + [self._cons() for _ in range(MAX_VIDEOS_QUEUE_SIZE)]):
                await cv
        if ExtraConfig.save_tags is True:
            dump_item_tags()
        await self._after_download()

#
#
#########################################
