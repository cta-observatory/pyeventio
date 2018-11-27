from eventio import EventIOFile
import pkg_resources

test_file = pkg_resources.resource_filename('eventio', 'resources/gamma_test.simtel.gz')


def test_run_heder():
    from eventio.simtel import SimTelRunHeader
    with EventIOFile(test_file) as f:
        o = next(f)
        while not isinstance(o, SimTelRunHeader):
            o = next(f)

        data = o.parse_data_field()
        data['observer'] = b'bernlohr@lfc371.mpi-hd.mpg.de'
        data['target'] = b'Monte Carlo beach'
