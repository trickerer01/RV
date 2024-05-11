# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from asyncio import CancelledError, Task, sleep, get_running_loop
from collections import deque
from os import path, stat
from typing import Optional, Deque

from aiohttp import ClientResponse

from config import Config
from defs import Mem, DOWNLOAD_STATUS_CHECK_TIMER
from downloader import VideoDownloadWorker
from logger import Log
from vinfo import VideoInfo


class ThrottleChecker:
    def __init__(self, vi: VideoInfo) -> None:
        self._vi = vi
        self._init_size = 0
        self._speeds = deque(maxlen=10)  # type: Deque[str]
        self._response = None  # type: Optional[ClientResponse]
        self._cheker = None  # type: Optional[Task]

    def prepare(self, response: ClientResponse, init_size: int) -> None:
        self._init_size = init_size
        self._response = response

    def run(self) -> None:
        assert self._cheker is None
        self._cheker = get_running_loop().create_task(self._check_video_download_status())

    def reset(self) -> None:
        if self._cheker is not None:
            self._cheker.cancel()
            self._cheker = None
        self._response = None
        self._speeds.clear()

    async def _check_video_download_status(self) -> None:
        dwn = VideoDownloadWorker.get()
        dest = self._vi.my_fullpath
        check_timer = float(DOWNLOAD_STATUS_CHECK_TIMER)
        slow_con_dwn_threshold = max(1, DOWNLOAD_STATUS_CHECK_TIMER * Config.throttle * Mem.KB)
        last_size = self._init_size
        try:
            while True:
                await sleep(check_timer)
                if not dwn.is_writing(dest):  # finished already
                    Log.error(f'ThrottleChecker: {self._vi.sfsname} checker is still running for finished download!')
                    break
                if self._response is None:
                    Log.debug(f'ThrottleChecker: {self._vi.sfsname} self._response is None...')
                    continue
                file_size = stat(dest).st_size if path.isfile(dest) else 0
                last_speed = (file_size - last_size) / Mem.KB / DOWNLOAD_STATUS_CHECK_TIMER
                self._speeds.appendleft(f'{last_speed:.2f} KB/s')
                if file_size < last_size + slow_con_dwn_threshold:
                    Log.warn(f'ThrottleChecker: {self._vi.sfsname} check failed at {file_size:d} ({last_speed:.2f} KB/s)! '
                             f'Interrupting current try...')
                    self._response.connection.transport.abort()  # abort download task (forcefully - close connection)
                    break
                last_size = file_size
        except CancelledError:
            pass

    def __str__(self) -> str:
        return f'{self._vi.sfsname} (orig size {self._init_size}): {", ".join(self._speeds)}'

    __repr__ = __str__

#
#
#########################################
