import unittest
from parea.main import _area2
from parea.main import _project_triangle_to_plane


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


if __name__ == '__main__':
    unittest.main()
