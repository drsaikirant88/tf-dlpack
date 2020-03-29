import os
import re
import sys
import shutil
import platform
import subprocess

from setuptools import find_packages
from setuptools import setup, Extension
from setuptools.dist import Distribution
from setuptools.command.build_ext import build_ext
from distutils.version import LooseVersion

class BinaryDistribution(Distribution):
    def has_ext_modules(self):
        return True

CURRENT_DIR = os.path.dirname(__file__)

def get_lib_path():
    """Get library path, name and version"""
     # We can not import `libinfo.py` in setup.py directly since __init__.py
    # Will be invoked which introduces dependences
    libinfo_py = os.path.join(CURRENT_DIR, 'tfdlpack', 'libinfo.py')
    libinfo = {'__file__': libinfo_py}
    exec(compile(open(libinfo_py, "rb").read(), libinfo_py, 'exec'), libinfo, libinfo)
    version = libinfo['__version__']
    tf_version_map = libinfo['__tf_version_map__']
    tf_versions = list(set(tf_version_map.values()))
    libname = ['libtfdlpack-tf-{}.so'.format(tfv) for tfv in tf_versions]

    lib_path = libinfo['find_lib_path'](libname)
    libs = [lib_path[0]]

    return libs, version

LIBS, VERSION = get_lib_path()

include_libs = False
wheel_include_libs = False
if "bdist_wheel" in sys.argv or os.getenv('CONDA_BUILD'):
    wheel_include_libs = True
else:
    include_libs = True

setup_kwargs = {}

# For bdist_wheel only
if wheel_include_libs:
    with open("MANIFEST.in", "w") as fo:
        for path in LIBS:
            shutil.copy(path, os.path.join(CURRENT_DIR, 'tfdlpack'))
            _, libname = os.path.split(path)
            fo.write("include tfdlpack/%s\n" % libname)
    setup_kwargs = {
        "include_package_data": True
    }

# For source tree setup
# Conda build also includes the binary library
if include_libs:
    rpath = [os.path.relpath(path, CURRENT_DIR) for path in LIBS]
    setup_kwargs = {
        "include_package_data": True,
        "data_files": [('tfdlpack', rpath)]
    }

setup(
    name='tfdlpack' + os.getenv('TFDLPACK_PACKAGE_SUFFIX', ''),
    version=VERSION,
    author='Jinjing Zhou',
    author_email='allen.zhou@nyu.edu',
    description='Tensorflow plugin for DLPack',
    packages=find_packages(),
    long_description="""
The package adds interoperability of DLPack to Tensorflow. It contains straightforward
and easy-to-use APIs to convert Tensorflow tensors from/to DLPack format.
    """,
    distclass=BinaryDistribution,
    zip_safe=False,
    license='APACHE',
    **setup_kwargs
)

if wheel_include_libs:
    # Wheel cleanup
    os.remove("MANIFEST.in")
    for path in LIBS:
        _, libname = os.path.split(path)
        os.remove(os.path.join(CURRENT_DIR, 'tfdlpack', libname))
