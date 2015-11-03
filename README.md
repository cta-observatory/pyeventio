# py_corsika_event_io #

This is a simple reader, for the special event_io data format invented by Konrad Bernloehr for the [Corsika](https://www.ikp.kit.edu/corsika/) IACT routines. 

# install with #
    
    pip install git+https://bitbucket.org/dneise/py_corsika_event_io

# 1st Example #

One may iterate over an instance of `EventIoFile` class in order to retrieve events. events have a small number of fields. the most important one is the `bunches` field, which is a simple structured np.array, containing the typical parameters Cherekov photons bunches in Corsika have, like:

 * `x, y` coordinate in the observation plane (in cm)
 * direction cosine `cx, cy` in x and y direction of the incident angle of the photon
 * wavelength `lambda` of the photon (in nm)
 * number of `photons` associated with this bunch
 * the `time` since the first interaction (in ns, I believe)
 * the production height of the photon bunch (called `zem`)

In addition an event knows the total number of bunches and photons in itself `n_bunches` and `n_photons`. Of course the numbers should match with the ones, we can retrieve from the array.

    import eventio
    f = eventio.EventIoFile('data/telescope.dat')
    for event in f:
        print event.n_photons, "should be (approximately) equal to", event.bunches['photons'].sum(), 
        print event.n_bunches, "should be (exactly) equal to", event.bunches.shape




# 2nd Example #

If you like to plot the origin of the Cherenkov photons of the first shower in file `data/telescope.dat` you can do:


    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    import eventio
    f = eventio.EventIoFile('data/telescope.dat')
    b = f.next().bunches

    cz = 1 - (b['cx']**2 + b['cy']**2)

    x = b['x'] + ((b['zem']-f.current_event_header['observation levels']) / cz)*b['cx']
    y = b['y'] + ((b['zem']-f.current_event_header['observation levels']) / cz)*b['cy']

    ax.plot(x/100., y/100., b['zem']/1e5, 'o')
    ax.set_xlabel('Xaxis [m]')
    ax.set_ylabel('Yaxis [m]')
    ax.set_zlabel('Zaxis [km]')
    plt.show()


It might look similar to this picture.

![an example shower](https://bitbucket.org/repo/ddng5E/images/4235100275-a_shower.png)