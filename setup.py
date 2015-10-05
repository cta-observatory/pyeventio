from distutils.core import setup

setup(
    name='eventio',
    version='0.1',
    description='reader for Corsika(IACT) event_io format files.',
    url='https://bitbucket.org/dneise/py_corsika_event_io',
    author='Dominik Neise',
    author_email='neised@phys.ethz.ch',
    license='MIT',
    packages=[ 
        'eventio',
        ],
    install_requires=[
        'numpy'
    ],
    #scripts=['scripts/shift_helper.py'],
    #package_data={'fact_shift_helper.tools': ['config.gpg']},
    #zip_safe=False
)