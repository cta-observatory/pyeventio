from eventio.search_utils import collect_toplevel_of_type
from pkg_resources import resource_filename


prod4b_sst1m_file = resource_filename(
    'eventio',
    'resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz'
)

titles = [
    'Events, without weights (Ra, log10(E))',
    'Array triggered, without weights (Ra, log10(E))',
    'Angle to observing position (all showers), n.w.',
    'Angle to observing position (triggered showers), n.w.',
    'Events, without weights (Ra3d, log10(E))',
    'Array triggered, without weights (Ra3d, log10(E))',
    'Photons per telescope sphere, n.w.',
    'Photons per telescope sphere (tel. triggered), n.w.',
    'Photo-electrons per telescope, n.w.',
    'Photo-electrons per telescope (tel. triggered), n.w.',
]


def test_histograms():
    from eventio import Histograms, EventIOFile

    with EventIOFile(prod4b_sst1m_file) as f:

        objects = collect_toplevel_of_type(f, Histograms)
        assert len(objects) > 0

        for obj in objects:
            hists = obj.parse_data_field()
            unread = obj.read()
            assert len(unread) == 0 or all(b == 0 for b in unread)

            for hist, title in zip(hists, titles):
                assert hist['title'] == title


