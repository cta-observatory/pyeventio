from setuptools import setup, Extension
import os
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

# if we have cython, use the cython file if not the c file
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
    use_scm_version={"write_to": os.path.join("src", "eventio", "_version.py")},
    ext_modules=cythonize(extensions),
    python_requires='>=3.8',
    install_requires=[
        'numpy >= 1.21',
        'corsikaio ~= 0.3.3',
        'zstandard > 0.11.1', # memory leak in zstandard 0.11.1
        'setuptools_scm',
    ],
    entry_points={
        'console_scripts': [
            'eventio_print_structure = eventio.scripts.print_structure:main',
            'eventio_print_simtel_history = eventio.scripts.print_simtel_history:main',
            'eventio_print_simtel_metaparams = eventio.scripts.print_simtel_metaparams:main',
            'eventio_plot_histograms = eventio.scripts.plot_hists:main',
            'eventio_print_object_information = eventio.scripts.print_object_information:main',
            'eventio_cut_file = eventio.scripts.cut_eventio_file:main',
        ]
    },
    tests_require=['pytest>=3.0.0'],
)
