import pytest

def test_assert_exact_version():
    from eventio.simtel.objects import assert_exact_version

    class Dummy:
        pass

    fake_object = Dummy()
    fake_object.header = Dummy()
    fake_object.header.version = 1

    with pytest.raises(NotImplementedError):
        assert_exact_version(fake_object, 0)

    # But this works
    assert_exact_version(fake_object, 1)


def test_assert_version_in():
    from eventio.simtel.objects import assert_version_in

    class Dummy:
        pass

    fake_object = Dummy()
    fake_object.header = Dummy()
    fake_object.header.version = 1

    with pytest.raises(NotImplementedError):
        assert_version_in(fake_object, [0, 2])

    # But this works
    assert_version_in(fake_object, [1, 2])

