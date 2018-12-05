from .base import EventIOFile, KNOWN_OBJECTS
from .iact import IACTFile
from . import simtel
from .histograms import Histograms

__all__ = ['EventIOFile', 'IACTFile', 'simtel']


KNOWN_OBJECTS[Histograms.eventio_type] = Histograms
