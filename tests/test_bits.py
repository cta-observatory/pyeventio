def test_bool_bit_from_pos():
    from eventio.header import bool_bit_from_pos

    word = 0b00000000000000000000000000100000

    assert bool_bit_from_pos(word, 5)
    assert not bool_bit_from_pos(word, 6)


def test_get_bits_from_word():
    from eventio.header import get_bits_from_word

    word = 0b00000000000000001010110000000000

    assert get_bits_from_word(word, n_bits=4, first=10) == 0b1011
