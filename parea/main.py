import argparse
import os

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

#--- constants ----------------------------------------------------------------+

x, y = [0, 1]

#--- functions ----------------------------------------------------------------+


def _area2(a, b, c):
    '''Calculate twice the area of a 2D triangle
    
    Parameters
    ----------
    a, b, c : tuple
        vertex tuples containing two floats (x, y)
    
    Returns
    -------
    float
        twice the triangle area

    References
    ----------
    [1] Computational Geometry in C by Joseph O'Rourke    
    '''
    return (
        (b[x] - a[x]) * (c[y] - a[y]) -
        (c[x] - a[x]) * (b[y] - a[y]))


def _munge_triangle(v1, v2, v3, min_area=0):
    '''MUNGE TRIANGLE
    
    For every new triangle that get's added, it  needs to pass some basic 
    quality controls and if need be, fixed.
    
    1) Triangles with zero area are automatically rejected.
    
    2) Triangles must have three unique vertices.
    
    3) All triangles will be returned with a CCW winding regardless of the 
    winding upon input.
    
    4) Final output is a list of three edges, consisting of vertex master list 
    indices.
    
    Inputs
    ------
    v1, v2, v3 : tuples
    
    Returns
    -------
    t : a list consisting of three edge tuples
    '''
    
    # first check if the triangle has three unique vertices
    if v1==v2 or v2==v3 or v3==v1: return []

    a2 = _area2(v1, v2, v3)
    
    # if the triangle has cw winding, reverse the winding order 
    if a2 < 0: t_verts = [v1, v3, v2]
    
    # the winding order is correct, leave vertices alone
    if a2 > 0: t_verts = [v1, v2, v3]
        
    # minimum triangle area check
    if abs(a2 * 0.5)<=min_area: return []
        
    return t_verts


def _project_point_to_plane(v, vec):
    '''PROJECT POINT TO PLANE
    '''

    pass


def _project_triangle_to_plane(tri_3d, vec):
    '''PROJECT TRIANGLE TO PLANE

    Parameters
    ----------
    tri_3d : list
    
    Returns
    -------
    list
    '''
    if vec == 'x': return [(v[1], v[2]) for v in tri_3d]
    if vec == 'y': return [(v[0], v[2]) for v in tri_3d]
    if vec == 'z': return [(v[0], v[1]) for v in tri_3d]


def _read_ascii(stl_path, n_tris=None):
    '''
    '''

    with open(stl_path, 'r') as stl_file:

        # initialize
        triangle = []
        tblock = False

        # cycle through stl line by line
        for i, line in enumerate(stl_file.readlines()):

            # begin triangle
            if 'facet normal' in line: tblock = True
            if 'vertex' in line and tblock==True: 
                xyz = line.replace('vertex','').split()
                x, y, z = float(xyz[0]), float(xyz[1]), float(xyz[2])
                triangle.append([x, y, z])

            # end triangle block
            if 'endfacet' in line: 
                yield triangle
                triangle = []
                tblock = False


def _read_binary(stl_path, n_tris):
    '''TO DO
    '''
    pass


def _load_stl(stl_path, pvec):
    '''LOAD STL

    Parameters
    ----------
    stl_path : str
    pvec : str

    Returns
    -------
    list of shapely polygon objects
    '''

    # first check if the file is binary
    with open(stl_path, 'rb') as f:
        f.read(80)
        n_tris = np.fromfile(f, count=1, dtype=np.uint32)[0]
        is_binary = 84 + n_tris * 50 == os.path.getsize(stl_path)

    # if it's binary, use numpy
    if is_binary: triangle_generator = _read_binary
    else: triangle_generator = _read_ascii

    assert is_binary == False, 'currently supports ascii stls only..'

    # assemble stl
    triangles = []
    for i, t in enumerate(triangle_generator(stl_path, n_tris)):
        v1, v2, v3 = _project_triangle_to_plane(t, pvec)
        verts = _munge_triangle(v1, v2, v3)
        if len(verts) == 3: triangles.append(Polygon(verts))

    return triangles


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
        sub_poly = unary_union(triangles)

        # persist sub poly
        sub_polys.append(sub_poly)

    # clip using floor height if necessary
    if fheight:
        fheight = float(fheight)
        p_proj = unary_union(sub_polys)
        u_min, v_min, u_max, v_max = p_proj.bounds
        p_floor = Polygon([
            (u_min-1, v_min-1),
            (u_max+1, v_min-1),
            (u_max+1, fheight),
            (u_min-1, fheight)])
        return p_proj.difference(p_floor).area
    
    # return just the projected area
    else: return unary_union(sub_polys).area


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