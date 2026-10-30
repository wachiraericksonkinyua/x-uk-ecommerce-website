from app.utils.pagination import page_range


def test_first_page():
    assert page_range(1, 20) == (0, 19)


def test_second_page():
    assert page_range(2, 20) == (20, 39)


def test_page_size_is_clamped_to_max():
    # asked for 1000 rows -> clamped to the 100 max
    assert page_range(1, 1000) == (0, 99)


def test_page_number_is_clamped_to_minimum():
    assert page_range(0, 10) == (0, 9)
    assert page_range(-5, 10) == (0, 9)
