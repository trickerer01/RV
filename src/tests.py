# coding=UTF-8
"""
Author: trickerer (https://github.com/trickerer, https://github.com/trickerer01)
"""
#########################################
#
#

import sys
from asyncio import run as run_async
from io import StringIO
from os import path, remove as remove_file, stat
from tempfile import gettempdir
from unittest import main as run_tests, TestCase
from unittest.mock import patch

from cmdargs import prepare_arglist
# noinspection PyProtectedMember
from config import BaseConfig
from defs import (
    APP_NAME, APP_VERSION, DOWNLOAD_MODE_TOUCH, SEARCH_RULE_DEFAULT,
)
from downloader import DownloadWorker
# noinspection PyProtectedMember
from ids import main as ids_main, main_sync as ids_main_sync
from logger import Log
# noinspection PyProtectedMember
from pages import main as pages_main, main_sync as pages_main_sync
# noinspection PyProtectedMember
from path_util import found_filenames_dict
from util import normalize_path


def set_up_test() -> None:
    DownloadWorker._instance = None
    found_filenames_dict.clear()
    Log._disabled = True


class CmdTests(TestCase):
    def test_output_version_pages(self):
        set_up_test()
        with patch('sys.stdout', new_callable=StringIO) as stdout:
            run_async(pages_main(['--version']))
            self.assertEqual(f'{APP_NAME} {APP_VERSION}', stdout.getvalue().strip('\n'))
        print(f'{self._testMethodName} passed')

    def test_output_version_ids(self):
        set_up_test()
        with patch('sys.stdout', new_callable=StringIO) as stdout:
            run_async(ids_main(['--version']))
            self.assertEqual(f'{APP_NAME} {APP_VERSION}', stdout.getvalue().strip('\n'))
        print(f'{self._testMethodName} passed')

    # @mock_stderr
    # def test_cmd_base(self, stderr: StringIO):
    #     set_up_test()
    #     self.assertRaises(HelpPrintExitException, prepare_arglist, ['cmd', '--help'], True)
    #     self.assertRaises(HelpPrintExitException, prepare_arglist, ['cmd', '-start', '1'], True)
    #     self.assertRaises(HelpPrintExitException, prepare_arglist, ['cmd', '-start', '1', '-pages'], True)
    #     self.assertNotEqual('', stderr.getvalue().strip('\n'))

    def test_cmd_pages(self):
        set_up_test()
        parsed1 = prepare_arglist(['cmd', '-get_maxid'], True)
        c1 = BaseConfig()
        c1.read(parsed1, True)
        self.assertTrue(c1.get_maxid)
        parsed2 = prepare_arglist(['-start', '2', '-pages', '1', '-uploader', '1234', '(2d~3d)', '-script',
                                   'a: 2d; b: 3d; c: 4k -60fps; d: * -uvp always', '-naming', 'prefix|quality', '-log', 'warn'], True)
        c2 = BaseConfig()
        c2.read(parsed2, True)
        self.assertEqual(17, c2.naming_flags)
        self.assertEqual(8, c2.logging_flags)
        self.assertEqual(1, len(c2.extra_tags))
        self.assertEqual(4, len(c2.scenario))
        self.assertEqual(1234, c2.uploader)
        self.assertEqual('', c2.search)
        self.assertEqual(SEARCH_RULE_DEFAULT, c2.search_rule_art)
        self.assertIsNone(c2.use_id_sequence)
        print(f'{self._testMethodName} passed')

    def test_cmd_ids(self):
        set_up_test()
        parsed1 = prepare_arglist(['cmd', '-seq'], False)
        c1 = BaseConfig()
        c1.read(parsed1, False)
        self.assertTrue(c1.use_id_sequence)
        parsed2 = prepare_arglist(['-start', '1000', '-end', '999', '(a~b)', '(2d~3d)', '-dmode', 'touch', '-script',
                                   'a: 2d; b: 3d; c: 4k -60fps; d: * -uvp always', '-naming', '0x10', '-log', 'trace'], False)
        c2 = BaseConfig()
        c2.read(parsed2, False)
        self.assertEqual(16, c2.naming_flags)
        self.assertEqual(1, c2.logging_flags)
        self.assertEqual(2, len(c2.extra_tags))
        self.assertEqual(4, len(c2.scenario))
        self.assertEqual(DOWNLOAD_MODE_TOUCH, c2.download_mode)
        print(f'{self._testMethodName} passed')


class DownloadTests(TestCase):
    def test_ids_touch(self):
        set_up_test()
        tempdir = normalize_path(gettempdir())
        tempfile_id = '3146165'
        tempfile_ext = 'mp4'
        tempfile_fullpath = f'{tempdir}{tempfile_id}.{tempfile_ext}'
        arglist1 = ['-path', tempdir, '-start', tempfile_id, '-dmode', 'touch', '-naming', 'none', '-quality', '360p', '-log', 'trace']
        ids_main_sync(arglist1)
        self.assertTrue(path.isfile(tempfile_fullpath))
        st = stat(tempfile_fullpath)
        self.assertEqual(0, st.st_size)
        remove_file(tempfile_fullpath)
        print(f'{self._testMethodName} passed')

    def test_pages_touch(self):
        set_up_test()
        tempdir = normalize_path(gettempdir())
        tempfile_id = '3148098'
        tempfile_ext = 'mp4'
        tempfile_fullpath = f'{tempdir}{tempfile_id}.{tempfile_ext}'
        arglist1 = ['-path', tempdir, '-pages', '999', '-dmode', 'touch', '-naming', 'none', '-quality', '360p', '-log', 'trace',
                    '-begin_id', tempfile_id, '-stop_id', tempfile_id, '-search_tag', 'redhead', '-search_art', 'dragk']
        pages_main_sync(arglist1)
        self.assertTrue(path.isfile(tempfile_fullpath))
        st = stat(tempfile_fullpath)
        self.assertEqual(0, st.st_size)
        remove_file(tempfile_fullpath)
        print(f'{self._testMethodName} passed')

    def test_ids_full(self):
        set_up_test()
        tempdir = normalize_path(gettempdir())
        tempfile_id = '3055235'
        tempfile_ext = 'mp4'
        tempfile_fullpath = f'{tempdir}{tempfile_id}.{tempfile_ext}'
        arglist1 = ['-path', tempdir, '-start', tempfile_id, '-dmode', 'full', '-naming', 'none', '-quality', '360p', '-log', 'trace']
        ids_main_sync(arglist1)
        self.assertTrue(path.isfile(tempfile_fullpath))
        st = stat(tempfile_fullpath)
        self.assertGreater(st.st_size, 0)
        remove_file(tempfile_fullpath)
        print(f'{self._testMethodName} passed')

    def test_pages_full(self):
        set_up_test()
        tempdir = normalize_path(gettempdir())
        tempfile_id = '3144801'
        tempfile_ext = 'mp4'
        tempfile_fullpath = f'{tempdir}{tempfile_id}.{tempfile_ext}'
        arglist1 = ['-path', tempdir, '-pages', '999', '-dmode', 'full', '-naming', 'none', '-quality', '360p', '-log', 'trace',
                    '-begin_id', tempfile_id, '-stop_id', tempfile_id, '-search_tag', '4k', '-search_art', 'mikeymack']
        pages_main_sync(arglist1)
        self.assertTrue(path.isfile(tempfile_fullpath))
        st = stat(tempfile_fullpath)
        self.assertGreater(st.st_size, 0)
        remove_file(tempfile_fullpath)
        print(f'{self._testMethodName} passed')


def run_all_tests() -> None:
    res = run_tests(module='tests', exit=False)
    if not res.result.wasSuccessful():
        print('Fail')
        sys.exit()


if __name__ == '__main__':
    run_all_tests()

#
#
#########################################
