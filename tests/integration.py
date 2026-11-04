import glob
import os
import unittest
from parea.main import _calculate_projected_area


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(THIS_DIR, 'data')
CUBE_ASCII_PATH = os.path.join(DATA_DIR, 'cube_ascii.stl')
CUBE_BINARY_PATH = os.path.join(DATA_DIR, 'cube_binary.stl')
MULTI_STL_PATHS = sorted(glob.glob(os.path.join(DATA_DIR, 'p*.stl')))


class test_main(unittest.TestCase):
    def test_ascii_x(self):
        self.assertLess(abs(_calculate_projected_area([CUBE_ASCII_PATH], 'x', None) - 4.0), 1e-5)

    def test_ascii_y(self):
        self.assertLess(abs(_calculate_projected_area([CUBE_ASCII_PATH], 'y', None) - 4.0), 1e-5)

    def test_ascii_z(self):
        self.assertLess(abs(_calculate_projected_area([CUBE_ASCII_PATH], 'z', None) - 4.0), 1e-5)

    def test_binary_xyz(self):
        for axis in ('x', 'y', 'z'):
            self.assertLess(abs(_calculate_projected_area([CUBE_BINARY_PATH], axis, None) - 4.0), 1e-5)

    def test_multi_stl_xyz(self):
        for axis in ('x', 'y', 'z'):
            self.assertLess(abs(_calculate_projected_area(MULTI_STL_PATHS, axis, None) - 3.0), 1e-5)

    def test_floor_clipping(self):
        self.assertLess(abs(_calculate_projected_area([CUBE_ASCII_PATH], 'x', '0.0') - 2.0), 1e-5)
        self.assertLess(abs(_calculate_projected_area([CUBE_ASCII_PATH], 'x', '0.5') - 1.0), 1e-5)


if __name__ == '__main__':
    unittest.main()
