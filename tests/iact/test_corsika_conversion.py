from eventio.iact.parse_corsika_data import float_to_date
import datetime


def test_float_to_date():

    date_float = 160101.0
    date = datetime.date(year=2016, month=1, day=1)
    assert float_to_date(date_float) == date
