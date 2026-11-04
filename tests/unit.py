import os
import struct
import tempfile
import unittest
import warnings

import numpy as np

from parea.main import _area2
from parea.main import _calculate_projected_area
from parea.main import _is_binary_stl
from parea.main import _project_triangle_to_plane
from parea.main import _read_binary


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
CUBE_ASCII_PATH = os.path.join(DATA_DIR, 'cube_ascii.stl')
CUBE_BINARY_PATH = os.path.join(DATA_DIR, 'cube_binary.stl')


class test_main(unittest.TestCase):
    def test_area2(self):
        a, b, c = (0,0), (1,0), (0,1)
        self.assertEqual(_area2(a,b,c), 1)
        self.assertEqual(_area2(a,c,b), -1)

    def test_project_triangle_to_plane(self):
        t = [(0,0,0), (1,1,1), (1,1,0)]
        self.assertListEqual(_project_triangle_to_plane(t, 'x'), [(0, 0), (1, 1), (1, 0)])
        self.assertListEqual(_project_triangle_to_plane(t, 'y'), [(0, 0), (1, 1), (1, 0)])
        self.assertListEqual(_project_triangle_to_plane(t, 'z'), [(0, 0), (1, 1), (1, 1)])

    def test_is_binary_stl_no_overflow_or_short_file_crash(self):
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            self.assertFalse(_is_binary_stl(CUBE_ASCII_PATH))
            self.assertTrue(_is_binary_stl(CUBE_BINARY_PATH))

        with tempfile.NamedTemporaryFile(suffix='.stl') as short_ascii:
            short_ascii.write(b'solid s\nendsolid s\n')
            short_ascii.flush()
            self.assertFalse(_is_binary_stl(short_ascii.name))

        with tempfile.NamedTemporaryFile(suffix='.stl') as empty_bin:
            empty_bin.write(b'solid_in_header'.ljust(80, b'\x00') + struct.pack('<I', 0))
            empty_bin.flush()
            self.assertTrue(_is_binary_stl(empty_bin.name))
            self.assertEqual(_read_binary(empty_bin.name).shape, (0, 3, 3))

    def test_read_binary_and_projected_area(self):
        tris = _read_binary(CUBE_BINARY_PATH)
        self.assertEqual(tris.shape, (12, 3, 3))
        self.assertEqual(tris.dtype, np.float64)

        for axis in ('x', 'y', 'z'):
            area = _calculate_projected_area([CUBE_BINARY_PATH], axis, None)
            self.assertAlmostEqual(area, 4.0, places=5)


if __name__ == '__main__':
    unittest.main()
