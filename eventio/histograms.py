import numpy as np
from .base import EventIOObject
from .version_handling import assert_version_in
from .tools import read_short, read_int, read_eventio_string, read_float, read_array


class Histograms(EventIOObject):
    eventio_type = 100

    def parse(self):
        assert_version_in(self, [1, 2])
        self.seek(0)

        n_histograms = read_short(self)

        histograms = []
        for i in range(n_histograms):
            hist = {}
            hist['type'] = self.read(1).decode('ascii')
            hist['title'] = read_eventio_string(self).decode('utf-8')
            if len(hist['title']) % 2 == 0:
                self.read(1)
            hist['id'] = read_int(self)
            hist['n_bins_x'] = read_short(self)
            hist['n_bins_y'] = read_short(self)
            hist['entries'] = read_int(self)
            hist['tentries'] = read_int(self)

            if hist['n_bins_y'] > 0:
                axes = 'xy'
                n_counts = hist['n_bins_x'] * hist['n_bins_y']
            else:
                axes = 'x'
                n_counts = hist['n_bins_x']

            for ax in axes:
                hist['underflow_' + ax] = read_int(self)
                hist['overflow_' + ax] = read_int(self)

                if hist['type'] in {'R', 'r', 'F', 'D'}:
                    hist['lower_' + ax] = read_float(self)
                    hist['upper_' + ax] = read_float(self)
                    hist['sum_' + ax] = read_float(self)
                    hist['tsum_' + ax] = read_float(self)
                else:
                    hist['lower_' + ax] = read_int(self)
                    hist['upper_' + ax] = read_int(self)
                    hist['sum_' + ax] = read_int(self)
                    hist['tsum_' + ax] = read_int(self)

            if hist['type'] in 'FD':
                hist['content_all'] = read_float(self)
                hist['content_inside'] = read_float(self)
                hist['content_outside'] = read_array(self, dtype='<f4', count=8)

                if hist['tentries'] > 0:
                    hist['data'] = read_array(self, dtype='<f4', count=n_counts)
                else:
                    hist['data'] = np.zeros(n_counts)
            else:
                if hist['tentries'] > 0:
                    hist['data'] = read_array(self, dtype='<i4', counts=n_counts)
                else:
                    hist['data'] = np.zeros(n_counts)

            if hist['n_bins_y'] > 0:
                hist['data'] = hist['data'].reshape((hist['n_bins_y'], hist['n_bins_x']))

            histograms.append(hist)

        return histograms
