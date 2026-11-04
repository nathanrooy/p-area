from __future__ import annotations

import os
import struct
import tempfile
import unittest
import warnings

import numpy as np

from parea.main import (
    _area2,
    _calculate_projected_area,
    _is_binary_stl,
    _load_stl,
    _munge_triangle,
    _project_triangle_to_plane,
    _read_ascii,
    _read_binary,
)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CUBE_ASCII_PATH = os.path.join(DATA_DIR, "cube_ascii.stl")
CUBE_BINARY_PATH = os.path.join(DATA_DIR, "cube_binary.stl")


class test_main(unittest.TestCase):
    def test_area2(self) -> None:
        ccw = [(0, 0), (1, 0), (0, 1)]
        cw = [(0, 0), (0, 1), (1, 0)]
        self.assertEqual(_area2(ccw), 1.0)
        self.assertEqual(_area2(cw), -1.0)
        np.testing.assert_array_equal(_area2([ccw, cw]), [1.0, -1.0])

    def test_munge_triangle(self) -> None:
        tris = np.array(
            [
                [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]],  # valid CCW
                [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0]],  # valid CW -> flipped to CCW
                [[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]],  # collinear -> rejected
                [[0.0, 0.0], [0.0, 0.0], [1.0, 1.0]],  # duplicate vertex -> rejected
                [[0.0, 0.0], [np.nan, 0.0], [0.0, 1.0]],  # NaN vertex -> rejected
            ]
        )
        munged = _munge_triangle(tris)
        self.assertEqual(munged.shape, (2, 3, 2))
        np.testing.assert_array_equal(munged[0], [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
        np.testing.assert_array_equal(munged[1], [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
        self.assertTrue(np.all(np.asarray(_area2(munged)) > 0))

    def test_project_triangle_to_plane(self) -> None:
        t = [(0, 0, 0), (1, 1, 1), (1, 1, 0)]
        np.testing.assert_array_equal(
            _project_triangle_to_plane(t, "x"), [[(0, 0), (1, 1), (1, 0)]]
        )
        np.testing.assert_array_equal(
            _project_triangle_to_plane(t, "y"), [[(0, 0), (1, 1), (1, 0)]]
        )
        np.testing.assert_array_equal(
            _project_triangle_to_plane(t, "z"), [[(0, 0), (1, 1), (1, 1)]]
        )
        with self.assertRaises(ValueError):
            _project_triangle_to_plane(t, "invalid")

    def test_is_binary_stl_no_overflow_or_short_file_crash(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            self.assertFalse(_is_binary_stl(CUBE_ASCII_PATH))
            self.assertTrue(_is_binary_stl(CUBE_BINARY_PATH))

        with tempfile.NamedTemporaryFile(suffix=".stl") as short_ascii:
            short_ascii.write(b"solid s\nendsolid s\n")
            short_ascii.flush()
            self.assertFalse(_is_binary_stl(short_ascii.name))
            self.assertEqual(_read_ascii(short_ascii.name).shape, (0, 3, 3))
            self.assertEqual(_calculate_projected_area([short_ascii.name], "x", None), 0.0)

        with tempfile.NamedTemporaryFile(suffix=".stl") as empty_bin:
            empty_bin.write(b"solid_in_header".ljust(80, b"\x00") + struct.pack("<I", 0))
            empty_bin.flush()
            self.assertTrue(_is_binary_stl(empty_bin.name))
            self.assertEqual(_read_binary(empty_bin.name).shape, (0, 3, 3))

    def test_read_binary_and_projected_area(self) -> None:
        tris = _read_binary(CUBE_BINARY_PATH)
        self.assertEqual(tris.shape, (12, 3, 3))
        self.assertEqual(tris.dtype, np.float64)

        for axis in ("x", "y", "z"):
            area = _calculate_projected_area([CUBE_BINARY_PATH], axis, None)
            self.assertAlmostEqual(area, 4.0, places=5)

    def test_floor_precull_and_edge_cases(self) -> None:
        self.assertEqual(len(_load_stl(CUBE_ASCII_PATH, "x", fheight=1.0)), 0)
        self.assertLess(abs(_calculate_projected_area([CUBE_ASCII_PATH], "x", 0.0) - 2.0), 1e-5)
        self.assertLess(abs(_calculate_projected_area([CUBE_ASCII_PATH], "x", -2.0) - 4.0), 1e-5)
        self.assertEqual(_calculate_projected_area([CUBE_ASCII_PATH], "x", 1.0), 0.0)
        self.assertEqual(_calculate_projected_area([CUBE_ASCII_PATH], "x", 5.0), 0.0)


if __name__ == "__main__":
    unittest.main()
