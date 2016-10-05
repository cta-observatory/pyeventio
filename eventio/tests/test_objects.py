import pkg_resources
import eventio
from os import path

testfile = pkg_resources.resource_filename(
    'eventio', path.join('resources', 'one_shower.dat')
)

