from setuptools import setup, find_packages
import os
import re

# make sure users without cython can install our extensions
try:
    from Cython.Distutils.extension import Extension
    from Cython.Distutils import build_ext as _build_ext
    USE_CYTHON = True
except ImportError:
    from setuptools import Extension
    from setuptools.command.build_ext import build_ext as _build_ext
    USE_CYTHON = False

print('using cython', USE_CYTHON)


# make sure numpy is installed before we try to build
# the extenion
class build_ext(_build_ext):
    def finalize_options(self):
        super().finalize_options()
        import numpy
        self.include_dirs.append(numpy.get_include())


# if we have cython, use the cython file if not the c file
ext = '.pyx' if USE_CYTHON else '.c'
extensions = [
    Extension('eventio.header', sources=['eventio/header' + ext]),
    Extension('eventio.var_int', sources=['eventio/var_int' + ext]),
    Extension(
        'eventio.simtel.parsing',
        sources=['eventio/simtel/parsing' + ext]
    ),
]
cmdclass = {'build_ext': build_ext}

# give a nice error message if people cloned the
# repository and do not have cython installed
if ext == '.c':
    sources = []
    for ext in extensions:
        sources.extend(ext.sources)
    if not all(os.path.isfile(s) for s in sources):
        raise ImportError('You need `Cython` to build this project locally')


with open('README.rst') as f:
    long_description = f.read()


with open('eventio/__init__.py') as f:
    m = re.search("__version__ = [\"']([0-9.]+)[\"']", f.read())
    version = m.groups()[0]

setup(
    name='eventio',
    version=version,
    description='Python read-only implementation of the EventIO file format',
    long_description=long_description,
    url='https://github.com/cta-observatory/pyeventio',
    author='Dominik Neise, Maximilian Noethe',
    author_email='maximilian.noethe@tu-dortmund.de',
    license='MIT',

    packages=find_packages(),

    ext_modules=extensions,
    cmdclass=cmdclass,

    package_data={
        'eventio': ['*.c'],
        'eventio.simtel': ['*.c'],
    },
    python_requires='>=3.5',
    install_requires=[
        'numpy',
        'corsikaio ~= 0.2.0',
    ],
    entry_points={
        'console_scripts': [
            'eventio_print_structure = eventio.scripts.print_structure:main',
            'eventio_print_simtel_history = eventio.scripts.print_simtel_history:main',
            'eventio_plot_histograms = eventio.scripts.plot_hists:main',
            'eventio_print_object_information = eventio.scripts.print_object_information:main',
            'eventio_cut_file = eventio.scripts.cut_eventio_file:main',
        ]
    },
    setup_requires=['pytest-runner', 'numpy'],
    tests_require=['pytest>=3.0.0'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Physics',
    ],
)
