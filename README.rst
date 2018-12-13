pyeventio |PyPI| |Build| |LoC|  
=====================================


A Python (read-only) implementation of the EventIO data format invented
by Konrad Bernloehr as used for example by the IACT extension for
CORSIKA: https://www.ikp.kit.edu/corsika

Documentation of the file format: https://www.mpi-hd.mpg.de/hfm/~bernlohr/sim_telarray/Documentation/eventio_en.pdf

Most blocks of the IACT extension and SimTel are implemented.
The following blocks are known, but reading their data is not (yet)
implemented:

+--------+-------------------------------+
| Code   | Description                   |
+========+===============================+
| 1206   | IACT Layout                   |
+--------+-------------------------------+
| 1207   | IACT Trigger Time             |
+--------+-------------------------------+
| 2017   | SimTel PixelCalib             |
+--------+-------------------------------+
| 2024   | SimTel RunStat                |
+--------+-------------------------------+
| 2025   | SimTel MC_RunStat             |
+--------+-------------------------------+
| 2028   | SimTel CalibEvent             |
+--------+-------------------------------+
| 2029   | SimTel AuxiliaryDigitalTraces |
+--------+-------------------------------+
| 2030   | SimTel AuxiliaryAnalogTraces  |
+--------+-------------------------------+
| 2031   | SimTel FSPhot                 |
+--------+-------------------------------+
| 2032   | SimTel PixelTriggerTimes      |
+--------+-------------------------------+


install with
------------

::

    pip install eventio

Open a file produced by the IACT CORSIKA extension
--------------------------------------------------

First Example
~~~~~~~~~~~~~

One may iterate over an instance of ``IACTFile`` class in order to retrieve events.
Events have a small number of fields.
The most important one is the ``photon_bunches`` field,
which is dictionary mapping telescope ids to a simple structured ``np.array``,
containing the typical parameters Cherenkov photon bunches in CORSIKA have, like:

-  ``x``, ``y`` coordinate in the observation plane (in cm)
-  direction cosine ``cx``, ``cy`` in x and y direction of the incident
   angle of the photon
-  wavelength ``lambda`` of the photon (in nm)
-  number of ``photons`` associated with this bunch
-  the ``time`` since the first interaction (in ns, I believe)
-  the production height of the photon bunch (called ``zem``)
-  a bool flag, whether the photon was scattered in the atmosphere

An event has the following attributes: \* ``header``: a ``namedtuple``
containing the Corsika Event Header data \* ``end_block``: a numpy array
containing the Corsika Event End data \* ``time_offset``, ``x_offset``,
``y_offsett``, the offset of the array

This prints energy and the number of photons for the first telescope in every
event:

.. code:: python

    import eventio

    with eventio.IACTFile('eventio/resources/one_shower.dat') as f:
        for event in f:
            print(event.header.total_energy)
            print(event.photon_bunches[0]['photons'].sum())


Second Example
~~~~~~~~~~~~~~

If you like to plot the origin of the Cherenkov photons of the first
event in file ``eventio/resources/one_shower.data`` for the first telescope,
have a look into
`this example <https://github.com/cta-observatory/pyeventio/blob/master/examples/plot_production_3d.py>`__

It might look similar to this picture:

.. figure:: https://raw.githubusercontent.com/cta-observatory/pyeventio/master/shower.png
   :alt: an example shower

   an example shower


Open a file produced by simtel_array
------------------------------------

.. code:: python

    import eventio

    with eventio.SimTelFile('eventio/resources/gamma_test.simtel.gz') as f:

        print(len(f.telescope_descriptions))
        for array_event in f:
            print(array_event['mc_shower']['energy'])


Commandline Tools
-----------------

We provide three commandline tools, to look into eventio files.

To get an overview over the structure of a file, use ``eventio_print_structure``,
for larger files, you might want to pipe its output into e.g. ``less``:

.. code:: shell
    
    $ eventio_print_structure eventio/resources/gamma_test.simtel.gz
    History[70](size=11960, only_subobjects=True, first_byte=16)
        HistoryCommandLine[71](size=668, only_subobjects=False, first_byte=12)
        HistoryConfig[72](size=120, only_subobjects=False, first_byte=692)
        HistoryConfig[72](size=172, only_subobjects=False, first_byte=824)
        HistoryConfig[72](size=180, only_subobjects=False, first_byte=1008)
        HistoryConfig[72](size=176, only_subobjects=False, first_byte=1200)
        HistoryConfig[72](size=72, only_subobjects=False, first_byte=1388)
        And 124 objects more of the same type
        .
        .
        .


To get table of all object versions and counts in a file,
use ``eventio_print_object_information``, it can also print json if given the 
``--json`` option

.. code:: shell
    
    $ eventio_print_object_information eventio/resources/gamma_test.simtel.gz
     Type | Version | #Objects
    --------------------------
       70 |       1 |        3
       71 |       1 |        3
       72 |       1 |    32840
     1212 |       0 |        2
     2000 |       2 |        1
     2001 |       4 |        2
     2002 |       2 |       98
     2002 |       3 |       28
     2003 |       1 |      126
     2004 |       2 |      126
     2005 |       0 |      126
     2006 |       0 |      126
     2007 |       0 |      126
     2008 |       0 |      126
     2009 |       2 |       10
    .
    .
    .


To plot histograms stored in an eventio file (Type 100),
use ``eventio_plot_histograms``.

.. code:: shell
    
    $ eventio_plot_histograms gamma_20deg_180deg_run99___cta-prod3_desert-2150m-Paranal-merged_cone10.simtel.gz


.. figure:: https://raw.githubusercontent.com/cta-observatory/pyeventio/master/first_hist.png
   :alt: First histogram of a prod3b file

   Histogram of Impact distance vs log10(E / TeV)


Low level access
----------------

For more low level access to the items of an ``EventIO`` file (or to
implement a higher level abstraction like ``IACTFile``) one can use the
``EventIOFile`` class which gives access to the ``objects`` and
``subobjects`` in ``EventIO`` files.

This is how our test file looks like in the low level view:

::

    In [3]: with EventIOFile('eventio/resources/one_shower.dat') as f: 
       ...:     for obj in f: 
       ...:         print(obj) 
       ...:         if obj.header.only_subobjects: 
       ...:             for subobj in obj: 
       ...:                 print('   ', subobj)                                   
    CORSIKARunHeader[1200](size=1096, only_subobjects=False, first_byte=16)
    CORSIKAInputCard[1212](size=448, only_subobjects=False, first_byte=1128)
    CORSIKATelescopeDefinition[1201](size=20, only_subobjects=False, first_byte=1592)
    CORSIKAEventHeader[1202](size=1096, only_subobjects=False, first_byte=1628)
    CORSIKAArrayOffsets[1203](size=16, only_subobjects=False, first_byte=2740)
    CORSIKATelescopeData[1204](size=6136, only_subobjects=True, first_byte=2772)
        IACTPhotons(length=6124, n_bunches=382)
    CORSIKAEventEndBlock[1209](size=1096, only_subobjects=False, first_byte=8924)
    CORSIKARunEndBlock[1210](size=16, only_subobjects=False, first_byte=10036)


.. |PyPI| image:: https://badge.fury.io/py/eventio.svg
    :target: https://pypi.org/project/eventio/
.. |Build| image:: https://travis-ci.org/cta-observatory/pyeventio.svg?branch=master
   :target: https://travis-ci.org/cta-observatory/pyeventio
.. |LoC| image:: https://tokei.rs/b1/github/cta-observatory/pyeventio
    :target: https://github.com/cta-observatory/pyeventio
