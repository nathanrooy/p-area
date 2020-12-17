<p align="center"><img src="https://raw.githubusercontent.com/nathanrooy/p-area/main/logo/logo.png" width="50%"></p>

[![gh-actions-ci](https://img.shields.io/github/workflow/status/nathanrooy/p-area/ci?style=flat-square)](https://github.com/nathanrooy/p-area/actions?query=workflow%3Aci)
[![GitHub license](https://img.shields.io/github/license/nathanrooy/p-area?style=flat-square)](https://github.com/nathanrooy/p-area/blob/master/LICENSE)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/parea.svg?style=flat-square)](https://pypi.org/pypi/parea/)
[![PyPi Version](https://img.shields.io/pypi/v/parea.svg?style=flat-square)](https://pypi.org/project/parea)

Most <a target="_blank" href="https://en.wikipedia.org/wiki/Lift_coefficient">lift</a> and <a target="_blank" href="https://en.wikipedia.org/wiki/Drag_coefficient">drag</a> calculations require the use of a frontal/projected area. This is normally not that big of a deal, especially when dealing with nice clean CAD files. Unfortunately, in fast-paced design environments (motorsport especially), you'll often get a collection of <a target="_blank" href="https://en.wikipedia.org/wiki/STL_(file_format)">STL</a> geometry files instead. This is annoying for a number of reasons, but mainly because there are several methods for computing the frontal area of an STL and all of them involve a fairly tedious/lengthy process. pArea aims to solve this with a single command.


### Installation
```
pip install parea
```

### Usage
As a simple example, the <a target="_blank" href="https://github.com/nathanrooy/p-area/blob/main/tests/data/cube_ascii.stl">cube</a> STL located within the `tests` directory has a projected area of 4.0 along all three coordinate axes. To validate this, simply run the following (assuming you've downloaded cube_ascii.stl into your current working directory):

```
parea -stl cube_ascii.stl -x
```

For models comprised of multiple STL files, simply separate the file names with a space:

```
parea -stl file_1.stl file_2.stl file_3.stl -x
```

Or use shell-style wildcards:

```
parea -stl file_*.stl  -x
```

When simulating ground vehicles with non-rigid wheels, you will need to account for the tire deformation and subsequent ride height drop. This can be facilitated using the `-floor` flag followed by a floor height float value. Note that floor height is in reference to the vertical axis of the specified projection plane.

```
parea -stl file_*.stl  -x -floor 0.0125
```
Since the projection vector is `x`, our projection plane is therefore `yz` yielding a projected area based off all geometry above z=0.0125.

### Options
vectors: `-x`, `-y`, `-z`

planes: `-yz`/`-zy`, `-xz`/`-zx`, `-xy`/`-yx`

### References
- Computational Geometry: Algorithms and Applications (3rd Edition) by Mike de Borg, Otfried Cheong, Mark van Kreveld, and Mark Overmars
- Computational Geometry in C (2nd Edition) by Joseph O'Rourke
- Finite Element Mesh Generation by Daniel S.H. Lo

