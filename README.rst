pyeventio |Build Status|
========================

A Python (read-only) implementation of the EventIO data format invented
by Konrad Bernloehr as used for example by the IACT extension for
CORSIKA: https://www.ikp.kit.edu/corsika

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

One may iterate over an instance of ``IACTFile`` class in order to
retrieve events. Events have a small number of fields. The most
important one is the ``photon_bunches`` field, which is dictionary
mapping telescope ids to a simple structured ``np.array``, containing
the typical parameters Cherekov photons bunches in Corsika have, like:

-  ``x``, ``y`` coordinate in the observation plane (in cm)
-  direction cosine ``cx``, ``cy`` in x and y direction of the incident
   angle of the photon
-  wavelength ``lambda`` of the photon (in nm)
-  number of ``photons`` associated with this bunch
-  the ``time`` since the first interaction (in ns, I believe)
-  the production height of the photon bunch (called ``zem``)
-  a bool flag, whether the photon was scattered in the atmosphere

An event has the following attributes: \* ``header``: a dictionary
containing the Corsika Event Header data \* ``end_block``: a numpy array
containing the Corsika Event End data \* ``time_offset``, ``x_offset``,
``y_offsett``, the offset of the array

This prints the number of photons for the first telescope in every
event:

.. code:: {python}

    import eventio

    with eventio.IACTFile('data/telescope.dat') as f:
        for event in f:
            print(event.photon_buches[0]['photons'].sum())

Second Example
~~~~~~~~~~~~~~

If you like to plot the origin of the Cherenkov photons of the first
event in file ``data/telescope.dat`` for the first telescope, have a
look into `this
example <https://github.com/fact-project/pyeventio/blob/new_api/examples/plot_production_3d.py>`__

It might look similar to this picture:

.. figure:: https://raw.githubusercontent.com/fact-project/pyeventio/master/a_shower.png
   :alt: an example shower

   an example shower

Low level access
----------------

For more low level access to the items of an ``EventIO`` file (or to
implement a higher level abstraction like ``IACTFile``) one can use the
``EventIOFile`` class which gives access to the ``Objects`` and
``subitems`` in ``EventIO`` files.

This is how our test file looks like in the low level view:

::

    In [1]: import eventio

    In [2]: eventio.EventIOFile('eventio/resources/one_shower.dat')
    Out[2]: 
    EventIOFile(path=eventio/resources/one_shower.dat, objects=[
      CorsikaRunHeader(first=0, length=1096)
      CorsikaInputCard(first=1112, length=448)
      CorsikaTelescopeDefinition(first=1576, length=20)
      CorsikaEventHeader(first=1612, length=1096)
      CorsikaArrayOffsets(first=2724, length=16)
      CorsikaTelescopeData(first=2756, length=6136, subitems=1)
      CorsikaEventEndBlock(first=8908, length=1096)
      CorsikaRunEndBlock(first=10020, length=16)
    ])

And this is how a ``sim_telarray`` file looks like (sim\_telarray
objects are not implemted yet):

::

    In [3]: eventio.EventIOFile('gamma_test.simtel')
    Out[3]: 
    EventIOFile(path=../../CTA/ctapipe/ctapipe-extra/datasets/gamma_test.simtel, objects=[
      UnknownObject[70](first=0, length=11960, subitems=131)
      UnknownObject[70](first=11976, length=1744732, subitems=21526)
      UnknownObject[70](first=1756724, length=838000, subitems=11186)
      UnknownObject[2000](first=2594740, length=1876)
        ...
      UnknownObject[2010](first=50007852, length=1782080, subitems=19)
      UnknownObject[2021](first=51789948, length=12)
      UnknownObject[2026](first=51789976, length=3536)
      UnknownObject[2010](first=51793528, length=1560656, subitems=9)
    ])

.. |Build Status| image:: https://travis-ci.org/fact-project/pyeventio.svg?branch=master
   :target: https://travis-ci.org/fact-project/pyeventio
