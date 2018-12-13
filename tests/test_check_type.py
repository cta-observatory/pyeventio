from eventio.exceptions import check_type, WrongType
from eventio import EventIOFile
from eventio.simtel import History, ArrayEvent, TelescopeEvent
import pytest


prod4b_sst1m_file = 'tests/resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz'


def test_single():

    with EventIOFile(prod4b_sst1m_file) as f:

        o = next(f)

        check_type(o, History)

        with pytest.raises(WrongType):
            check_type(o, ArrayEvent)


def test_multiple():

    with EventIOFile(prod4b_sst1m_file) as f:
        o = next(f)

        check_type(o, (History, ArrayEvent))

        with pytest.raises(WrongType):
            check_type(o, (TelescopeEvent, ArrayEvent))
