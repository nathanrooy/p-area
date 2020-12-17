 
from setuptools import setup
import parea

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='parea',
    version=parea.__version__,
    author=parea.__author__,
    author_email='nathanrooy@gmail.com',
    url='https://github.com/nathanrooy/p-area',
    description='The easiest way to calculate the projected/frontal area of an STL.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['parea'],
    python_requires='>=3.5',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ],
    install_requires=[
	'shapely',
	'numpy'
    ],
    entry_points={
        'console_scripts': [
            'parea = parea:main'
        ]
    }
)
