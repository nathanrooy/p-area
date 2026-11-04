from __future__ import annotations

import struct
import warnings
from pathlib import Path

import numpy as np
import pytest

from parea.main import (
    _area2,
    _is_binary_stl,
    _load_stl,
    _munge_triangle,
    _project_triangle_to_plane,
    _read_ascii,
    _read_binary,
    calculate_projected_area,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
CUBE_ASCII_PATH = DATA_DIR / "cube_ascii.stl"
CUBE_BINARY_PATH = DATA_DIR / "cube_binary.stl"


def test_area2() -> None:
    ccw = [(0, 0), (1, 0), (0, 1)]
    cw = [(0, 0), (0, 1), (1, 0)]
    assert _area2(ccw) == 1.0
    assert _area2(cw) == -1.0
    np.testing.assert_array_equal(_area2([ccw, cw]), [1.0, -1.0])


def test_munge_triangle() -> None:
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
    assert munged.shape == (2, 3, 2)
    np.testing.assert_array_equal(munged[0], [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    np.testing.assert_array_equal(munged[1], [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    assert np.all(np.asarray(_area2(munged)) > 0)


@pytest.mark.parametrize(
    ("axis", "expected"),
    [
        ("x", [[(0, 0), (1, 1), (1, 0)]]),
        ("y", [[(0, 0), (1, 1), (1, 0)]]),
        ("z", [[(0, 0), (1, 1), (1, 1)]]),
    ],
)
def test_project_triangle_to_plane(axis: str, expected: list[list[tuple[int, int]]]) -> None:
    t = [(0, 0, 0), (1, 1, 1), (1, 1, 0)]
    np.testing.assert_array_equal(_project_triangle_to_plane(t, axis), expected)


def test_project_triangle_to_plane_invalid_axis() -> None:
    t = [(0, 0, 0), (1, 1, 1), (1, 1, 0)]
    with pytest.raises(ValueError, match="Unsupported projection vector"):
        _project_triangle_to_plane(t, "invalid")


def test_is_binary_stl_no_overflow_or_short_file_crash(tmp_path: Path) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert not _is_binary_stl(CUBE_ASCII_PATH)
        assert _is_binary_stl(CUBE_BINARY_PATH)

    short_ascii = tmp_path / "short.stl"
    short_ascii.write_bytes(b"solid s\nendsolid s\n")
    assert not _is_binary_stl(short_ascii)
    assert _read_ascii(short_ascii).shape == (0, 3, 3)
    assert calculate_projected_area([short_ascii], "x", None) == 0.0

    empty_bin = tmp_path / "empty.stl"
    empty_bin.write_bytes(b"solid_in_header".ljust(80, b"\x00") + struct.pack("<I", 0))
    assert _is_binary_stl(empty_bin)
    assert _read_binary(empty_bin).shape == (0, 3, 3)


@pytest.mark.parametrize("axis", ["x", "y", "z"])
def test_read_binary_and_projected_area(axis: str) -> None:
    tris = _read_binary(CUBE_BINARY_PATH)
    assert tris.shape == (12, 3, 3)
    assert tris.dtype == np.float64
    assert calculate_projected_area([CUBE_BINARY_PATH], axis, None) == pytest.approx(4.0, abs=1e-5)


def test_floor_precull_and_edge_cases() -> None:
    assert len(_load_stl(CUBE_ASCII_PATH, "x", fheight=1.0)) == 0
    assert calculate_projected_area([CUBE_ASCII_PATH], "x", 0.0) == pytest.approx(2.0, abs=1e-5)
    assert calculate_projected_area([CUBE_ASCII_PATH], "x", -2.0) == pytest.approx(4.0, abs=1e-5)
    assert calculate_projected_area([CUBE_ASCII_PATH], "x", 1.0) == 0.0
    assert calculate_projected_area([CUBE_ASCII_PATH], "x", 5.0) == 0.0
