from setuptools import setup, find_packages

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
        'eventio.simtel.camorgan',
        sources=['eventio/simtel/camorgan' + ext]
    ),
]
cmdclass = {'build_ext': build_ext}


with open('README.rst') as f:
    long_description = f.read()

setup(
    name='eventio',
    version='0.9.0',
    description='Python read-only implementation of the EventIO file format',
    long_description=long_description,
    url='https://github.com/fact-project/pyeventio',
    author='Dominik Neise, Maximilian Noethe',
    author_email='neised@phys.ethz.ch',
    license='MIT',

    packages=find_packages(),

    ext_modules=extensions,
    cmdclass=cmdclass,

    package_data={'eventio': ['resources/*']},
    install_requires=[
        'numpy',
    ],
    entry_points={
        'console_scripts': [
            'eventio_print_structure = eventio.scripts.print_structure:main',
            'eventio_plot_histograms = eventio.scripts.plot_hists:main',
            'eventio_print_object_information = eventio.scripts.print_object_information:main',
        ]
    },
    setup_requires=['pytest-runner', 'numpy'],
    tests_require=['pytest>=3.0.0'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Physics',
    ],
)
