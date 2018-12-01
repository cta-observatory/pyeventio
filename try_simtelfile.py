# coding: utf-8
from pprint import pprint
from eventio.simtel import simtelfile

url = 'eventio/resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz'

for x in simtelfile.SimTelFile(url):
    pprint(x)
    print()
