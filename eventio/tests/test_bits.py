def test_bool_bit_from_pos():
    from eventio.bits import bool_bit_from_pos

    word = 0b0000_0000_0000_0000_0000_0000_0010_0000

    assert bool_bit_from_pos(word, 5)
    assert not bool_bit_from_pos(word, 6)


def test_get_bits_from_word():
    from eventio.bits import get_bits_from_word

    word = 0b0000_0000_0000_0000_1010_1100_0000_0000

    assert get_bits_from_word(word, num_bits=4, first=10) == 0b1011
