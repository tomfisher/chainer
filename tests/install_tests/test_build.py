from distutils import ccompiler
import unittest

from install import build


class TestCheckVersion(unittest.TestCase):

    def setUp(self):
        self.compiler = ccompiler.new_compiler()
        self.settings = build.get_compiler_setting()

    def test_check_cuda_version(self):
        self.assertTrue(build.check_cuda_version(
            self.compiler, self.settings))

    def test_check_cudnn_version(self):
        self.assertTrue(build.check_cudnn_version(
            self.compiler, self.settings))
