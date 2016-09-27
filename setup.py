from distutils.core import setup

setup(
    name='eventio',
    version='0.1',
    description='reader for Corsika(IACT) event_io format files.',
    url='https://github.com/fact-project/py_corsika_eventio',
    author='Dominik Neise',
    author_email='neised@phys.ethz.ch',
    license='MIT',
    packages=[ 
        'eventio',
        ],
    package_data={'eventio': [
                    'resources/input_card.txt',
                    'resources/one_shower.dat',
                    ]
                 },
    install_requires=[
        'numpy'
    ],
)