# Placeholder test file for basic functionality


def add(a, b):
    return a + b


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_add_negative():
    assert add(-2, -3) == -5
    assert add(-1, -1) == -2


def test_add_floats():
    assert add(2.5, 3.5) == 6.0
    assert add(-1.0, 1.0) == 0.0
