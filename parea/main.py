from __future__ import annotations

import argparse
import os
import struct
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import shapely
from numpy.typing import ArrayLike, NDArray

from parea.__about__ import __version__

# --- constants ---------------------------------------------------------------+

PLANE_COLS: dict[str, list[int]] = {
    "x": [1, 2],
    "y": [0, 2],
    "z": [0, 1],
}

BINARY_STL_DTYPE = np.dtype(
    [
        ("normal", "<f4", (3,)),
        ("vertices", "<f4", (3, 3)),
        ("attr", "<u2"),
    ]
)

PathLikeStr = str | os.PathLike[str]

# --- functions ---------------------------------------------------------------+


def _area2(pts_2d: ArrayLike) -> NDArray[np.float64] | np.float64:
    """Calculate twice the signed area of 2D triangle(s).

    Parameters
    ----------
    pts_2d : array_like
        2D triangle vertices of shape (N, 3, 2) or (3, 2)

    Returns
    -------
    numpy.ndarray or float
        twice the signed triangle area(s)

    References
    ----------
    [1] Computational Geometry in C by Joseph O'Rourke
    """
    pts = np.asarray(pts_2d, dtype=np.float64)
    return (pts[..., 1, 0] - pts[..., 0, 0]) * (pts[..., 2, 1] - pts[..., 0, 1]) - (
        pts[..., 2, 0] - pts[..., 0, 0]
    ) * (pts[..., 1, 1] - pts[..., 0, 1])


def _munge_triangle(pts_2d: ArrayLike, min_area: float = 0.0) -> NDArray[np.float64]:
    """Filter degenerate 2D triangles and enforce counter-clockwise (CCW) winding.

    1) Triangles with area <= min_area (including collinear or duplicate vertices)
       or non-finite coordinates are rejected.
    2) Clockwise (CW) triangles have their vertex winding reversed to CCW.

    Parameters
    ----------
    pts_2d : array_like
        2D triangle vertices of shape (N, 3, 2) or (3, 2)
    min_area : float, optional

    Returns
    -------
    numpy.ndarray
        valid CCW 2D triangles of shape (M, 3, 2)
    """
    pts = np.asarray(pts_2d, dtype=np.float64).reshape(-1, 3, 2)
    a2 = np.asarray(_area2(pts), dtype=np.float64)
    valid = np.isfinite(a2) & (np.abs(a2) > 2.0 * min_area)
    pts = pts[valid]
    a2 = a2[valid]

    cw = a2 < 0.0
    if np.any(cw):
        pts[cw] = pts[cw][:, [0, 2, 1]]

    return pts


def _project_triangle_to_plane(tris_3d: ArrayLike, vec: str) -> NDArray[np.float64]:
    """Project 3D triangle vertices onto an axis-aligned 2D plane.

    Parameters
    ----------
    tris_3d : array_like
        3D triangle vertices of shape (N, 3, 3) or (3, 3)
    vec : str
        projection axis ('x', 'y', or 'z')

    Returns
    -------
    numpy.ndarray
        projected 2D triangle vertices of shape (N, 3, 2)
    """
    if vec not in PLANE_COLS:
        raise ValueError(f"Unsupported projection vector: {vec!r}. Expected 'x', 'y', or 'z'.")
    tris = np.asarray(tris_3d, dtype=np.float64).reshape(-1, 3, 3)
    return tris[:, :, PLANE_COLS[vec]]


def _read_ascii(stl_path: PathLikeStr, n_tris: int | None = None) -> NDArray[np.float64]:
    """Read triangle vertices from an ASCII STL file.

    Parameters
    ----------
    stl_path : str or os.PathLike
    n_tris : int, optional

    Returns
    -------
    numpy.ndarray
        triangle vertices array with shape (n_tris, 3, 3) and dtype float64
    """
    triangles: list[list[list[float]]] = []
    with Path(stl_path).open("r", encoding="utf-8", errors="replace") as stl_file:
        triangle: list[list[float]] = []
        tblock = False

        for line in stl_file:
            if "facet normal" in line:
                tblock = True
            if "vertex" in line and tblock:
                xyz = line.replace("vertex", "").split()
                triangle.append([float(xyz[0]), float(xyz[1]), float(xyz[2])])
            if "endfacet" in line:
                triangles.append(triangle)
                triangle = []
                tblock = False

    if not triangles:
        return np.empty((0, 3, 3), dtype=np.float64)
    return np.asarray(triangles, dtype=np.float64)


def _is_binary_stl(stl_path: PathLikeStr) -> bool:
    """Check whether an STL file is binary or not.

    Parameters
    ----------
    stl_path : str or os.PathLike

    Returns
    -------
    bool
    """
    path = Path(stl_path)
    file_size = path.stat().st_size
    if file_size < 84:
        return False

    with path.open("rb") as f:
        f.seek(80)
        n_tris: int = struct.unpack("<I", f.read(4))[0]

    return 84 + n_tris * 50 == file_size


def _read_binary(stl_path: PathLikeStr, n_tris: int | None = None) -> NDArray[np.float64]:
    """Read triangle vertices from a binary STL file.

    Parameters
    ----------
    stl_path : str or os.PathLike
    n_tris : int, optional

    Returns
    -------
    numpy.ndarray
        triangle vertices array with shape (n_tris, 3, 3) and dtype float64
    """
    count = -1 if n_tris is None else int(n_tris)
    data = np.fromfile(stl_path, dtype=BINARY_STL_DTYPE, count=count, offset=84)
    return np.asarray(data["vertices"], dtype=np.float64)


def _load_stl(
    stl_path: PathLikeStr,
    pvec: str,
    fheight: float | None = None,
) -> NDArray[np.object_]:
    """LOAD STL

    Parameters
    ----------
    stl_path : str
    pvec : str
    fheight : float, optional

    Returns
    -------
    numpy.ndarray
        1D array of shapely polygon objects
    """
    # first check if the file is binary
    is_binary = _is_binary_stl(stl_path)

    # read 3D triangles as (N, 3, 3) float64 array
    reader = _read_binary if is_binary else _read_ascii
    tris_3d = reader(stl_path)

    # project, pre-cull submerged triangles, filter, orient CCW, and construct polygons
    pts_2d = _project_triangle_to_plane(tris_3d, pvec)
    if fheight is not None:
        pts_2d = pts_2d[pts_2d[:, :, 1].max(axis=1) > fheight]
    verts_2d = _munge_triangle(pts_2d)
    return np.asarray(shapely.polygons(verts_2d), dtype=object)


def calculate_projected_area(
    stl_paths: Sequence[PathLikeStr] | PathLikeStr,
    pvec: str,
    fheight: float | str | None = None,
) -> float:
    """Calculate the projected/frontal area of one or more STL files.

    Parameters
    ----------
    stl_paths : str, os.PathLike, or sequence of (str or os.PathLike)
    pvec : str
    fheight : float or str, optional

    Returns
    -------
    float
    """
    paths = [stl_paths] if isinstance(stl_paths, (str, os.PathLike)) else list(stl_paths)
    floor_val = float(fheight) if fheight is not None else None

    # cycle through all stls
    sub_polys = []
    for stl_file in paths:
        # bulk load all triangles from stl
        triangles = _load_stl(stl_file, pvec, floor_val)

        # merge triangles into single polygon
        sub_poly = shapely.union_all(triangles)

        # persist sub poly
        sub_polys.append(sub_poly)

    p_proj = shapely.union_all(sub_polys)
    if p_proj.is_empty:
        return 0.0

    # clip using floor height if necessary
    if floor_val is not None:
        u_min, v_min, u_max, v_max = p_proj.bounds
        if floor_val >= v_max:
            return 0.0
        if floor_val > v_min:
            p_proj = shapely.clip_by_rect(p_proj, u_min, floor_val, u_max, v_max)

    return float(p_proj.area)


# --- MAIN --------------------------------------------------------------------+


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point for pArea."""
    parser = argparse.ArgumentParser(description="--- pArea ---")
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-stl",
        "--stl",
        nargs="+",
        dest="stl_paths",
        type=str,
        required=True,
        help="specify the path to the stl",
    )
    parser.add_argument(
        "-floor",
        "--floor",
        dest="fheight",
        type=float,
        required=False,
        help="specify the floor height. everything below will be clipped.",
    )

    direction = parser.add_mutually_exclusive_group(required=True)

    # vectors
    direction.add_argument("-x", dest="pvec", action="store_const", const="x")
    direction.add_argument("-y", dest="pvec", action="store_const", const="y")
    direction.add_argument("-z", dest="pvec", action="store_const", const="z")

    # planes
    direction.add_argument("-xy", "--xy", dest="pvec", action="store_const", const="z")
    direction.add_argument("-yz", "--yz", dest="pvec", action="store_const", const="x")
    direction.add_argument("-zx", "--zx", dest="pvec", action="store_const", const="y")

    # more planes
    direction.add_argument("-yx", "--yx", dest="pvec", action="store_const", const="z")
    direction.add_argument("-zy", "--zy", dest="pvec", action="store_const", const="x")
    direction.add_argument("-xz", "--xz", dest="pvec", action="store_const", const="y")

    args = parser.parse_args(argv)

    # calculate projected area
    p_area = calculate_projected_area(args.stl_paths, args.pvec, args.fheight)

    # display results
    if args.fheight is not None:
        print(">   floor height:", args.fheight)
    print(f"> projected area: {p_area}")


if __name__ == "__main__":
    main()
