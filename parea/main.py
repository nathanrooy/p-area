import argparse

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


def _bulk_load_stl(stl_path, vec):
    '''BULK LOAD STL
    '''
    triangles = []
    for i, t in enumerate(_load_stl_generator(stl_path)):
        v1, v2, v3 = _project_triangle_to_plane(t, vec)
        verts = _munge_triangle(v1, v2, v3)
        if len(verts) == 3: triangles.append(Polygon(verts))
    return triangles


def _load_stl_generator(stl_path):
    '''
    '''
    with open(stl_path, 'r') as stl_file:
        
        # first, let's check if the file is ascii or binary

        # cycle through stl line by line
        for line in stl_file:
            triangle = []
            tblock = False
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


def _calculate_projected_area(args):
    # bulk load all triangles from stl
    triangles = _bulk_load_stl(args.stl_path, args.vec)

    # merge triangles into single polygon
    main_poly = unary_union(triangles)

    # return results
    return main_poly.area


#--- MAIN ---------------------------------------------------------------------+


def main():
    # parse arguments
    parser = argparse.ArgumentParser(description='--- pArea ---')
    parser.add_argument('-stl', dest='stl_path', type=str, required=True, help='specify the path to the stl')

    # vectors
    parser.add_argument('-x', dest='vec', required=False, action='store_const', const='x')
    parser.add_argument('-y', dest='vec', required=False, action='store_const', const='y')
    parser.add_argument('-z', dest='vec', required=False, action='store_const', const='z')

    # planes
    parser.add_argument('-xy', dest='vec', required=False, action='store_const', const='z')
    parser.add_argument('-yz', dest='vec', required=False, action='store_const', const='x')
    parser.add_argument('-zx', dest='vec', required=False, action='store_const', const='y')

    # more planes
    parser.add_argument('-yx', dest='vec', required=False, action='store_const', const='z')
    parser.add_argument('-zy', dest='vec', required=False, action='store_const', const='x')
    parser.add_argument('-xz', dest='vec', required=False, action='store_const', const='y')

    args = parser.parse_args()

    # basic checks
    if args.stl_path is None: print('ERROR: must specify an stl path')

    # calculate projected area
    p_area = _calculate_projected_area(args)

    # display results
    print(f'> projected area: {p_area}')


if __name__ == '__main__':
    main()