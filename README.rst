pyeventio |Build Status| |LoC|
==============================


A Python (read-only) implementation of the EventIO data format invented
by Konrad Bernloehr as used for example by the IACT extension for
CORSIKA: https://www.ikp.kit.edu/corsika

Documentation of the file format: https://www.mpi-hd.mpg.de/hfm/~bernlohr/sim_telarray/Documentation/eventio_en.pdf

Reading the data of the following Objects is currently supported:

+--------+-------------------------------+
| Code   | Description                   |
+========+===============================+
| 1200   | CORSIKA Run Header            |
+--------+-------------------------------+
| 1201   | CORSIKA Telescope Positions   |
+--------+-------------------------------+
| 1202   | CORSIKA Event Header          |
+--------+-------------------------------+
| 1203   | CORSIKA Array Offsets         |
+--------+-------------------------------+
| 1204   | CORSIKA Telescope Data        |
+--------+-------------------------------+
| 1205   | IACT Photons                  |
+--------+-------------------------------+
| 1209   | CORSIKA Event End Block       |
+--------+-------------------------------+
| 1210   | CORSIKA Run End Block         |
+--------+-------------------------------+
| 1211   | CORSIKA Longitudinal Block    |
+--------+-------------------------------+
| 1212   | CORSIKA Input Card            |
+--------+-------------------------------+

The following blocks are known, but reading their data is not (yet)
implemented:

+--------+-----------------------+
| Code   | Description           |
+========+=======================+
| 1206   | IACT Layout           |
+--------+-----------------------+
| 1207   | IACT Trigger Time     |
+--------+-----------------------+
| 1208   | IACT PhotoElectrons   |
+--------+-----------------------+

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
`this example <https://github.com/fact-project/pyeventio/blob/new_api/examples/plot_production_3d.py>`__

It might look similar to this picture:

.. figure:: https://raw.githubusercontent.com/fact-project/pyeventio/master/a_shower.png
   :alt: an example shower

   an example shower

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


And this is how a ``sim_telarray`` file looks like (sim\_telarray
objects are not implemted yet):

:: 

    In [4]: with EventIOFile('../../CTA/ctapipe-extra/ctapipe_resources/gamma_test.simtel.gz') as f: 
       ...:     for obj in f: 
       ...:         print(obj)                                                                                                                                     
    EventIOObject[70](size=11960, only_subobjects=True, first_byte=16)
    EventIOObject[70](size=1744732, only_subobjects=True, first_byte=11992)
    EventIOObject[70](size=838000, only_subobjects=True, first_byte=1756740)
    EventIOObject[2000](size=1876, only_subobjects=False, first_byte=2594756)
    EventIOObject[2001](size=140, only_subobjects=False, first_byte=2596648)
    EventIOObject[2001](size=140, only_subobjects=False, first_byte=2596804)
    ...




.. |Build Status| image:: https://travis-ci.org/fact-project/pyeventio.svg?branch=master
   :target: https://travis-ci.org/fact-project/pyeventio
.. |LoC| image:: https://tokei.rs/b1/github/fact-project/pyeventio
    :target: https://github.com/fact-project/pyeventio
