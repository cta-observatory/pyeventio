import pytest


class Dummy:
    pass


def test_assert_max_version():
    from eventio.version_handling import assert_max_version

    fake_object = Dummy()
    fake_object.header = Dummy()

    for i in range(3):
        fake_object.header.version = i
        assert_max_version(fake_object, 2)

    with pytest.raises(NotImplementedError):
        assert_max_version(fake_object, 1)


def test_assert_exact_version():
    from eventio.version_handling import assert_exact_version

    fake_object = Dummy()
    fake_object.header = Dummy()
    fake_object.header.version = 1

    with pytest.raises(NotImplementedError):
        assert_exact_version(fake_object, 0)

    # But this works
    assert_exact_version(fake_object, 1)


def test_assert_version_in():
    from eventio.version_handling import assert_version_in

    fake_object = Dummy()
    fake_object.header = Dummy()
    fake_object.header.version = 1

    with pytest.raises(NotImplementedError):
        assert_version_in(fake_object, [0, 2])

    # But this works
    assert_version_in(fake_object, [1, 2])

