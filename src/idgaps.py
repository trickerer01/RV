# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

from __future__ import annotations

import itertools

from config import Config
from defs import IDGAP_PREDICTION_AUTO, IDGAP_PREDICTION_OFF, IntPair
from dscanner import VideoScanWorker
from iinfo import VideoInfo
from logger import Log

__all__ = ('IdGapsPredictor',)

ID_SKIPS = (
    (IntPair(3400000, 3638827), 3),
    (IntPair(3638828, 3639245), 2),
    (IntPair(3639246, 3670051), 3),
    (IntPair(3670052, 9999999), 4),
)


class IdGapsPredictor:
    _instance: IdGapsPredictor | None = None

    def __init__(self) -> None:
        assert IdGapsPredictor._instance is None
        IdGapsPredictor._instance = self

        self._enabled = Config.predict_id_gaps != IDGAP_PREDICTION_OFF
        self._streak = 0
        self._streaks_count = 0

    @staticmethod
    def get() -> IdGapsPredictor:
        if IdGapsPredictor._instance is None:
            IdGapsPredictor._instance = IdGapsPredictor()
        return IdGapsPredictor._instance

    @staticmethod
    def _get_skip_num(vi: VideoInfo) -> int:
        for idpair, num_skip in reversed(ID_SKIPS):
            if idpair.first <= vi.id <= idpair.second:
                return num_skip
        return 0

    def need_skip(self, vi: VideoInfo) -> int:
        if num_skip := (self._get_skip_num(vi) if self._enabled else 0):
            prevs = tuple(VideoScanWorker.get().find_vinfo_last(vi.id - (_ + 1)) for _ in range(num_skip - 1))
            prev_stats = tuple((bool(prevs[i]), prevs[i] and prevs[i].has_flag(VideoInfo.Flags.RETURNED_404)) for i in range(num_skip - 1))
            f_404s: tuple[bool, ...] = ()
            for i in range(1, num_skip):
                if all(prev_stats[_][0] for _ in range(num_skip - i)):
                    f_404s: tuple[bool, ...] = tuple(prev_stats[_][1] for _ in range(num_skip - i))
                    break
            found_one = len(f_404s) == 1 and prev_stats[0][0] is not prev_stats[0][1]
            found_any = not all(_[0] is _[1] for _ in itertools.pairwise(f_404s))
            if found_one or found_any:
                return num_skip
        return 0

    def count_nonexisting(self) -> None:
        self._streak += 1

    def count_existing(self, vi: VideoInfo) -> None:
        if self._streak:
            skip_num = self._get_skip_num(vi)
            streak = self._streak
            self._streak = 0
            self._streaks_count = (self._streaks_count + 1) if streak + 1 == skip_num else 0
            if self._enabled:
                streak_valid = skip_num == 0 or (streak + 1) % skip_num == 0
                if streak_valid is False:
                    Log.error(f'Error: id gap predictor encountered unexpected valid post offset != {skip_num:d}. Disabling prediction!')
                    self._enabled = False
            elif self._streaks_count and Config.predict_id_gaps == IDGAP_PREDICTION_AUTO:
                Log.warn(f'Warning: id gap predictor encountered another gap with post offset == {skip_num:d} re-enabling prediction!')
                self._enabled = True

#
#
#########################################
