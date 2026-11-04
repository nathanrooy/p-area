from __future__ import annotations

import contextlib
import glob
import io
import os
import unittest

from parea import calculate_projected_area, main

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(THIS_DIR, "data")
CUBE_ASCII_PATH = os.path.join(DATA_DIR, "cube_ascii.stl")
CUBE_BINARY_PATH = os.path.join(DATA_DIR, "cube_binary.stl")
MULTI_STL_PATHS = sorted(glob.glob(os.path.join(DATA_DIR, "p*.stl")))


class test_main(unittest.TestCase):
    def test_ascii_x(self) -> None:
        self.assertLess(abs(calculate_projected_area(CUBE_ASCII_PATH, "x") - 4.0), 1e-5)

    def test_ascii_y(self) -> None:
        self.assertLess(abs(calculate_projected_area([CUBE_ASCII_PATH], "y", None) - 4.0), 1e-5)

    def test_ascii_z(self) -> None:
        self.assertLess(abs(calculate_projected_area([CUBE_ASCII_PATH], "z", None) - 4.0), 1e-5)

    def test_binary_xyz(self) -> None:
        for axis in ("x", "y", "z"):
            self.assertLess(
                abs(calculate_projected_area([CUBE_BINARY_PATH], axis, None) - 4.0), 1e-5
            )

    def test_multi_stl_xyz(self) -> None:
        for axis in ("x", "y", "z"):
            self.assertLess(abs(calculate_projected_area(MULTI_STL_PATHS, axis, None) - 3.0), 1e-5)

    def test_floor_clipping(self) -> None:
        self.assertLess(abs(calculate_projected_area([CUBE_ASCII_PATH], "x", 0.0) - 2.0), 1e-5)
        self.assertLess(abs(calculate_projected_area([CUBE_ASCII_PATH], "x", 0.5) - 1.0), 1e-5)
        self.assertLess(abs(calculate_projected_area(MULTI_STL_PATHS, "x", 0.0) - 1.5), 1e-5)

    def test_cli_main(self) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            main(["-stl", CUBE_ASCII_PATH, "-x", "-floor", "0.0"])
        output = buf.getvalue()
        self.assertIn("floor height: 0.0", output)
        self.assertIn("projected area: 2.0", output)

        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(["-stl", CUBE_ASCII_PATH])

        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(["-stl", CUBE_ASCII_PATH, "-x", "-y"])


if __name__ == "__main__":
    unittest.main()
