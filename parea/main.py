import argparse
import os
import struct

import numpy as np
import shapely
from shapely.geometry import Polygon

#--- constants ----------------------------------------------------------------+

PLANE_COLS = {
    'x': [1, 2],
    'y': [0, 2],
    'z': [0, 1],
}

BINARY_STL_DTYPE = np.dtype([
    ('normal', '<f4', (3,)),
    ('vertices', '<f4', (3, 3)),
    ('attr', '<u2'),
])

#--- functions ----------------------------------------------------------------+


def _area2(pts_2d):
    '''Calculate twice the signed area of 2D triangle(s).

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
    '''
    pts = np.asarray(pts_2d, dtype=np.float64)
    return (
        (pts[..., 1, 0] - pts[..., 0, 0]) * (pts[..., 2, 1] - pts[..., 0, 1]) -
        (pts[..., 2, 0] - pts[..., 0, 0]) * (pts[..., 1, 1] - pts[..., 0, 1])
    )


def _munge_triangle(pts_2d, min_area=0.0):
    '''Filter degenerate 2D triangles and enforce counter-clockwise (CCW) winding.

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
    '''
    pts = np.asarray(pts_2d, dtype=np.float64).reshape(-1, 3, 2)
    a2 = _area2(pts)
    valid = np.isfinite(a2) & (np.abs(a2) > 2.0 * min_area)
    pts = pts[valid]
    a2 = a2[valid]

    cw = a2 < 0.0
    if np.any(cw):
        pts[cw] = pts[cw][:, [0, 2, 1]]

    return pts


def _project_point_to_plane(v, vec):
    '''PROJECT POINT TO PLANE
    '''

    pass


def _project_triangle_to_plane(tris_3d, vec):
    '''Project 3D triangle vertices onto an axis-aligned 2D plane.

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
    '''
    if vec not in PLANE_COLS:
        raise ValueError(f"Unsupported projection vector: {vec!r}. Expected 'x', 'y', or 'z'.")
    tris = np.asarray(tris_3d, dtype=np.float64).reshape(-1, 3, 3)
    return tris[:, :, PLANE_COLS[vec]]


def _read_ascii(stl_path, n_tris=None):
    '''Read triangle vertices from an ASCII STL file.

    Parameters
    ----------
    stl_path : str or os.PathLike
    n_tris : int, optional

    Returns
    -------
    numpy.ndarray
        triangle vertices array with shape (n_tris, 3, 3) and dtype float64
    '''
    triangles = []
    with open(stl_path, 'r') as stl_file:
        triangle = []
        tblock = False

        for line in stl_file:
            if 'facet normal' in line:
                tblock = True
            if 'vertex' in line and tblock:
                xyz = line.replace('vertex', '').split()
                triangle.append([float(xyz[0]), float(xyz[1]), float(xyz[2])])
            if 'endfacet' in line:
                triangles.append(triangle)
                triangle = []
                tblock = False

    if not triangles:
        return np.empty((0, 3, 3), dtype=np.float64)
    return np.asarray(triangles, dtype=np.float64)


def _is_binary_stl(stl_path):
    '''Check whether an STL file is binary or not.

    Parameters
    ----------
    stl_path : str or os.PathLike

    Returns
    -------
    bool
    '''
    file_size = os.path.getsize(stl_path)
    if file_size < 84:
        return False

    with open(stl_path, 'rb') as f:
        f.seek(80)
        n_tris = struct.unpack('<I', f.read(4))[0]

    return 84 + n_tris * 50 == file_size


def _read_binary(stl_path, n_tris=None):
    '''Read triangle vertices from a binary STL file.

    Parameters
    ----------
    stl_path : str or os.PathLike
    n_tris : int, optional

    Returns
    -------
    numpy.ndarray
        triangle vertices array with shape (n_tris, 3, 3) and dtype float64
    '''
    count = -1 if n_tris is None else int(n_tris)
    data = np.fromfile(stl_path, dtype=BINARY_STL_DTYPE, count=count, offset=84)
    return data['vertices'].astype(np.float64)


def _load_stl(stl_path, pvec):
    '''LOAD STL

    Parameters
    ----------
    stl_path : str
    pvec : str

    Returns
    -------
    numpy.ndarray
        1D array of shapely polygon objects
    '''

    # first check if the file is binary
    is_binary = _is_binary_stl(stl_path)

    # read 3D triangles as (N, 3, 3) float64 array
    reader = _read_binary if is_binary else _read_ascii
    tris_3d = reader(stl_path)

    # project, filter, orient CCW, and construct shapely polygons in bulk
    pts_2d = _project_triangle_to_plane(tris_3d, pvec)
    verts_2d = _munge_triangle(pts_2d)
    return shapely.polygons(verts_2d)


def _calculate_projected_area(stl_paths, pvec, fheight):
    '''CALCULATE PROJECTED AREA

    Parameters
    ----------
    stl_paths : list
    pvec : str

    Returns
    -------
    float
    '''

    # cycle through all stls
    sub_polys = []
    for stl_file in stl_paths:

        # bulk load all triangles from stl
        triangles = _load_stl(stl_file, pvec)

        # merge triangles into single polygon
        sub_poly = shapely.union_all(triangles)

        # persist sub poly
        sub_polys.append(sub_poly)

    # clip using floor height if necessary
    if fheight:
        fheight = float(fheight)
        p_proj = shapely.union_all(sub_polys)
        u_min, v_min, u_max, v_max = p_proj.bounds
        p_floor = Polygon([
            (u_min-1, v_min-1),
            (u_max+1, v_min-1),
            (u_max+1, fheight),
            (u_min-1, fheight)])
        return p_proj.difference(p_floor).area
    
    # return just the projected area
    else: return shapely.union_all(sub_polys).area


#--- MAIN ---------------------------------------------------------------------+


def main():
    # parse arguments
    parser = argparse.ArgumentParser(description='--- pArea ---')
    parser.add_argument('-stl', nargs='+', dest='stl_paths', type=str, required=True, help='specify the path to the stl')
    parser.add_argument('-floor', dest='fheight', type=str, required=False, help='specify the floor height. everything below will be clipped.')

    # vectors
    parser.add_argument('-x', dest='pvec', required=False, action='store_const', const='x')
    parser.add_argument('-y', dest='pvec', required=False, action='store_const', const='y')
    parser.add_argument('-z', dest='pvec', required=False, action='store_const', const='z')

    # planes
    parser.add_argument('-xy', dest='pvec', required=False, action='store_const', const='z')
    parser.add_argument('-yz', dest='pvec', required=False, action='store_const', const='x')
    parser.add_argument('-zx', dest='pvec', required=False, action='store_const', const='y')

    # more planes
    parser.add_argument('-yx', dest='pvec', required=False, action='store_const', const='z')
    parser.add_argument('-zy', dest='pvec', required=False, action='store_const', const='x')
    parser.add_argument('-xz', dest='pvec', required=False, action='store_const', const='y')

    args = parser.parse_args()

    # basic checks
    if args.stl_paths is None: print('ERROR: must specify an stl path')

    # calculate projected area
    p_area = _calculate_projected_area(args.stl_paths, args.pvec, args.fheight)

    # display results
    if args.fheight: print('>   floor height:', args.fheight)
    print(f'> projected area: {p_area}')


if __name__ == '__main__':
    main()
