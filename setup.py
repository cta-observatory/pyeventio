from setuptools import setup, find_packages
import numpy as np

# make sure users without cython can install our extensions
try:
    from Cython.Distutils.extension import Extension
    from Cython.Distutils import build_ext
    USE_CYTHON = True
except ImportError:
    from setuptools import Extension
    USE_CYTHON = False


# if we have cython, use the cython file if not the c file
ext = '.pyx' if USE_CYTHON else '.c'
extensions = [
    Extension('eventio.var_int', sources=['eventio/var_int' + ext])
]
cmdclass = {'build_ext': build_ext} if USE_CYTHON else {}


with open('README.rst') as f:
    long_description = f.read()

setup(
    name='eventio',
    version='0.6.0',
    description='Python read-only implementation of the EventIO file format',
    long_description=long_description,
    url='https://github.com/fact-project/pyeventio',
    author='Dominik Neise, Maximilian Noethe',
    author_email='neised@phys.ethz.ch',
    license='MIT',

    packages=find_packages(),

    ext_modules=extensions,
    cmdclass=cmdclass,
    include_dirs=[np.get_include()],

    package_data={'eventio': ['resources/*']},
    install_requires=[
        'numpy',
        'Cython',
    ],
    setup_requires=['pytest-runner', 'Cython', 'numpy'],
    tests_require=['pytest>=3.0.0'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS 9',
        'Operating System :: MacOS :: MacOS X',
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
