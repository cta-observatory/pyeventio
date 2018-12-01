# coding: utf-8
import eventio

from eventio.simtel.objects import (
    History,
    SimTelLasCal,
    SimTelTelMoni,
    SimTelCamSettings,
    SimTelCamOrgan,
    SimTelPixelset,
    SimTelPixelDisable,
    SimTelCamsoftset,
    SimTelTrackSet,
    SimTelPointingCor,

)

url = 'eventio/resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz'
f = eventio.EventIOFile(url)

def print_object_indented(obj, indent, remove_simtel=True):
    s = str(obj)
    if remove_simtel:
        s = s.replace("SimTel", "")
    lines = s.split('\n')
    print(indent + lines[0])
    for line in lines[1:]:
        print(' ' + indent + line)

filter_objects = [
    History,
    SimTelCamSettings,
    SimTelCamOrgan,
    SimTelPixelset,
    SimTelPixelDisable,
    SimTelCamsoftset,
    SimTelTrackSet,
    SimTelPointingCor,
    #SimTelLasCal,
    #SimTelTelMoni,
]

def p_file(file_, indent='', level=0):
    for object_ in file_:
        skip = False
        for crap in filter_objects:
            if isinstance(object_, crap):
                skip = True
                break
        if skip:
            continue
        print_object_indented(object_, indent=level * indent)
        if object_.header.only_subobjects:
            p_file(object_, indent, level + 1)


p_file(f, indent='    ')
