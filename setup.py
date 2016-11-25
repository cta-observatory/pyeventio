from setuptools import setup

setup(
    name='eventio',
    version='0.3.0',
    description='Python read-only implementation of the EventIO file format',
    url='https://github.com/fact-project/pyeventio',
    author='Dominik Neise, Maximilian Noethe',
    author_email='neised@phys.ethz.ch',
    license='MIT',
    packages=[
        'eventio',
        'eventio.iact',
        ],
    package_data={'eventio': ['resources/*']},
    install_requires=[
        'numpy'
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest>=3.0.0'],
)
