from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np


kwargs = dict(
    include_dirs=[np.get_include()],
    define_macros=[
        # fixes a warning when compiling
        ("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION"),
        # defines the oldest numpy we want to be compatible with
        ("NPY_TARGET_VERSION", "NPY_1_21_API_VERSION"),
    ]
)

extensions = [
    Extension(
        'eventio.header',
        sources=['src/eventio/header.pyx'],
        **kwargs,
    ),
    Extension(
        'eventio.var_int',
        sources=['src/eventio/var_int.pyx'],
        **kwargs,
    ),
    Extension(
        'eventio.simtel.parsing',
        sources=['src/eventio/simtel/parsing.pyx'],
        **kwargs,
    ),
]

setup(
    ext_modules=cythonize(extensions),
)
