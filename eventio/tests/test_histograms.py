from eventio.search_utils import collect_toplevel_of_type
from pkg_resources import resource_filename


prod4b_sst1m_file = resource_filename(
    'eventio',
    'resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz'
)


def test_histograms():
    from eventio import Histograms, EventIOFile

    with EventIOFile(prod4b_sst1m_file) as f:
        objects = collect_toplevel_of_type(f, Histograms)

        for obj in objects:
            obj.parse_data_field()
            unread = obj.read()
            assert len(unread) == 0 or all(b == 0 for b in unread)
