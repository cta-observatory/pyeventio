# pyeventio [![Build Status](https://travis-ci.org/fact-project/pyeventio.svg?branch=master)](https://travis-ci.org/fact-project/pyeventio)

A Python (read-only) implementation of the EventIO data format invented by Konrad Bernloehr as used for example
by the IACT extension for CORSIKA: https://www.ikp.kit.edu/corsika

The following EventIO object types are currently supported:

| Code | Description                 |
| ---- | --------------------------- |
| 1200 | CORSIKA Run Header          |
| 1201 | CORSIKA Telescope Positions |
| 1202 | CORSIKA Event Header        |
| 1203 | CORSIKA Telescope Offsets   |
| 1204 ||
| 1209 ||
| 1210 ||
| 1212 | CORSIKA Input Card          |


# install with
    
    pip install git+https://github.com/fact-project/pyeventio

# Open a file produced by the IACT CORSIKA extension

## First Example
One may iterate over an instance of `EventIoFile` class in order to retrieve events. 
Events have a small number of fields. 
The most important one is the `bunches` field, which is a simple structured np.array, containing the typical parameters Cherekov photons bunches in Corsika have, like:

 * `x, y` coordinate in the observation plane (in cm)
 * direction cosine `cx, cy` in x and y direction of the incident angle of the photon
 * wavelength `lambda` of the photon (in nm)
 * number of `photons` associated with this bunch
 * the `time` since the first interaction (in ns, I believe)
 * the production height of the photon bunch (called `zem`)

In addition an event knows the total number of bunches and photons in itself `n_bunches` and `n_photons`. Of course the numbers should match with the ones, we can retrieve from the array.

```{python}
import eventio
f = eventio.EventIOFile('data/telescope.dat')
for event in f:
    print(event.n_photons, "should be (approximately) equal to", event.bunches['photons'].sum()) 
    print(event.n_bunches, "should be (exactly) equal to", event.bunches.shape)
```
## Second Example

If you like to plot the origin of the Cherenkov photons of the first shower in file `data/telescope.dat` you can do:
```{python}
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

import eventio
f = eventio.EventIOFile('data/telescope.dat')
b = f.next().bunches

cz = 1 - (b['cx']**2 + b['cy']**2)

x = b['x'] + ((b['zem']-f.current_event_header['observation levels']) / cz)*b['cx']
y = b['y'] + ((b['zem']-f.current_event_header['observation levels']) / cz)*b['cy']

ax.plot(x/100., y/100., b['zem']/1e5, 'o')
ax.set_xlabel('Xaxis [m]')
ax.set_ylabel('Yaxis [m]')
ax.set_zlabel('Zaxis [km]')
plt.show()
```

It might look similar to this picture.

![an example shower](https://raw.githubusercontent.com/fact-project/pyeventio/master/a_shower.png)
