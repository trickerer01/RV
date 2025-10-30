# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import os
from asyncio import CancelledError, Task, get_running_loop, sleep
from collections import deque

from aiohttp import ClientResponse

from config import Config
from defs import DOWNLOAD_STATUS_CHECK_TIMER, Mem
from downloader import VideoDownloadWorker
from iinfo import VideoInfo
from logger import Log


class ThrottleChecker:
    def __init__(self, vi: VideoInfo) -> None:
        self._vi = vi
        self._init_size = 0
        self._slow_download_amount_threshold = ThrottleChecker._orig_threshold()
        self._interrupted_speeds = deque[float](maxlen=3)
        self._speeds = deque[str](maxlen=5)
        self._response: ClientResponse | None = None
        self._checker: Task | None = None

    def prepare(self, response: ClientResponse, init_size: int) -> None:
        self._init_size = init_size
        self._response = response

    def run(self) -> None:
        assert self._checker is None
        self._checker = get_running_loop().create_task(self._check_video_download_status())

    def reset(self) -> None:
        if self._checker is not None:
            self._checker.cancel()
            self._checker = None
        self._response = None
        self._speeds.clear()

    @staticmethod
    def _orig_threshold() -> int:
        return ThrottleChecker._calc_threshold(Config.throttle)

    @staticmethod
    def _calc_threshold(speed: int | float) -> int:
        return max(1, int(DOWNLOAD_STATUS_CHECK_TIMER * speed * Mem.KB))

    @staticmethod
    def _calc_speed(threshold: int) -> float:
        return threshold / Mem.KB / DOWNLOAD_STATUS_CHECK_TIMER

    def _recalculate_slow_download_amount_threshold(self) -> None:
        # Hyperbolic averaging with additional 2% off to prevent cycling interruptions in case of perfect connection stability
        all_speeds = [*self._interrupted_speeds, self._calc_speed(self._slow_download_amount_threshold)]
        avg_speed = 0.98 * sum(all_speeds) / len(all_speeds)
        Log.trace(f'[throttler] recalculation, speeds + threshold: {all_speeds!s}. New speed threshold: {avg_speed:.6f} KB/s')
        self._slow_download_amount_threshold = self._calc_threshold(avg_speed)

    async def _check_video_download_status(self) -> None:
        dwn = VideoDownloadWorker.get()
        dest = self._vi.my_fullpath
        last_size = self._init_size
        try:
            while True:
                await sleep(float(DOWNLOAD_STATUS_CHECK_TIMER))
                if not await dwn.is_writing(self._vi):  # finished already
                    Log.error(f'[throttler] {self._vi.sfsname} checker is still running for finished download!')
                    break
                if self._response is None:
                    Log.debug(f'[throttler] {self._vi.sfsname} self._response is None...')
                    continue
                file_size = os.stat(dest).st_size if os.path.isfile(dest) else 0
                last_speed = (file_size - last_size) / Mem.KB / DOWNLOAD_STATUS_CHECK_TIMER
                self._speeds.append(f'{last_speed:.2f} KB/s')
                if file_size < last_size + self._slow_download_amount_threshold:
                    Log.warn(f'[throttler] {self._vi.sfsname} check failed at {file_size:d} ({last_speed:.2f} KB/s)! '
                             f'Interrupting current try...')
                    self._vi.last_check_size = file_size
                    self._response.connection.transport.abort()  # abort download task (forcefully - close connection)
                    # calculate normalized threshold if needed
                    if Config.throttle_auto is True and self._orig_threshold() > 10 * Mem.KB:
                        self._interrupted_speeds.append(last_speed)
                        if len(self._interrupted_speeds) >= self._interrupted_speeds.maxlen:
                            self._recalculate_slow_download_amount_threshold()
                            self._interrupted_speeds.clear()
                    break
                else:
                    self._interrupted_speeds.clear()
                last_size = file_size
        except CancelledError:
            pass

    def __str__(self) -> str:
        return f'{self._vi.sfsname} (orig size {self._init_size / Mem.MB:.2f} MB): {", ".join(self._speeds)}'

    __repr__ = __str__

#
#
#########################################
