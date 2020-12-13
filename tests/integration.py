import os
import unittest
from parea.main import _calculate_projected_area


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
STL_PATH = os.path.join(THIS_DIR, 'cube_ascii.stl')


class dummy_args():
    def __init__(self, STL_PATH, vec):
        self._stl_path = STL_PATH
        self._vec = vec

    @property
    def stl_path(self): return self._stl_path

    @property
    def vec(self): return self._vec


class test_main(unittest.TestCase):
    def test_ascii_x(self):
        args = dummy_args(STL_PATH, 'x')
        self.assertLess(abs(_calculate_projected_area(args) - 4.0), 1e-5)

    def test_ascii_y(self):
        args = dummy_args(STL_PATH, 'y')
        self.assertLess(abs(_calculate_projected_area(args) - 4.0), 1e-5)

    def test_ascii_z(self):
        args = dummy_args(STL_PATH, 'z')
        self.assertLess(abs(_calculate_projected_area(args) - 4.0), 1e-5)
    

if __name__ == '__main__':
    unittest.main()
