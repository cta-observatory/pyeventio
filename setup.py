from setuptools import setup, find_packages

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='eventio',
    version='0.5.1',
    description='Python read-only implementation of the EventIO file format',
    long_description=long_description,
    url='https://github.com/fact-project/pyeventio',
    author='Dominik Neise, Maximilian Noethe',
    author_email='neised@phys.ethz.ch',
    license='MIT',
    packages=find_packages(),
    package_data={'eventio': ['resources/*']},
    install_requires=[
        'numpy'
    ],
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
    setup_requires=['pytest-runner'],
    tests_require=['pytest>=3.0.0'],
)
