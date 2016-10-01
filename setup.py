from setuptools import setup

setup(
    name='eventio',
    version='0.1.0',
    description='Python read-only implementation of the EventIO file format',
    url='https://github.com/fact-project/pyeventio',
    author='Dominik Neise',
    author_email='neised@phys.ethz.ch',
    license='MIT',
    packages=[
        'eventio',
        ],
    package_data={'eventio': ['resources/*']},
    install_requires=[
        'numpy'
    ],
)
