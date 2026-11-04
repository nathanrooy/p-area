from __future__ import annotations

from pathlib import Path

import pytest

from parea import calculate_projected_area, main

DATA_DIR = Path(__file__).resolve().parent / "data"
CUBE_ASCII_PATH = DATA_DIR / "cube_ascii.stl"
CUBE_BINARY_PATH = DATA_DIR / "cube_binary.stl"
MULTI_STL_PATHS = sorted(DATA_DIR.glob("p*.stl"))


@pytest.mark.parametrize("axis", ["x", "y", "z"])
def test_ascii_xyz(axis: str) -> None:
    assert calculate_projected_area(CUBE_ASCII_PATH, axis) == pytest.approx(4.0, abs=1e-5)


@pytest.mark.parametrize("axis", ["x", "y", "z"])
def test_binary_xyz(axis: str) -> None:
    assert calculate_projected_area([CUBE_BINARY_PATH], axis, None) == pytest.approx(4.0, abs=1e-5)


@pytest.mark.parametrize("axis", ["x", "y", "z"])
def test_multi_stl_xyz(axis: str) -> None:
    assert calculate_projected_area(MULTI_STL_PATHS, axis, None) == pytest.approx(3.0, abs=1e-5)


@pytest.mark.parametrize(
    ("floor", "expected"),
    [
        (0.0, 2.0),
        (0.5, 1.0),
    ],
)
def test_floor_clipping_cube(floor: float, expected: float) -> None:
    assert calculate_projected_area([CUBE_ASCII_PATH], "x", floor) == pytest.approx(
        expected, abs=1e-5
    )


def test_floor_clipping_multi_stl() -> None:
    assert calculate_projected_area(MULTI_STL_PATHS, "x", 0.0) == pytest.approx(1.5, abs=1e-5)


def test_cli_main(capsys: pytest.CaptureFixture[str]) -> None:
    main(["-stl", str(CUBE_ASCII_PATH), "-x", "-floor", "0.0"])
    output = capsys.readouterr().out
    assert "floor height: 0.0" in output
    assert "projected area: 2.0" in output

    main(["-stl", str(CUBE_ASCII_PATH), "-yz"])
    output_no_floor = capsys.readouterr().out
    assert "floor height:" not in output_no_floor
    assert "projected area: 4.0" in output_no_floor

    with pytest.raises(SystemExit):
        main(["-stl", str(CUBE_ASCII_PATH)])

    with pytest.raises(SystemExit):
        main(["-stl", str(CUBE_ASCII_PATH), "-x", "-y"])
