from .base import EventIOFile, KNOWN_OBJECTS
from .iact import IACTFile
from .simtel import SimTelFile
from . import simtel
from .histograms import Histograms

__all__ = ['EventIOFile', 'IACTFile', 'SimTelFile', 'simtel']


KNOWN_OBJECTS[Histograms.eventio_type] = Histograms
