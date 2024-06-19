from example.stack_based import compile
from tests.util import run_test

def test_add():
    text = "1 2 + print"
    code, out = run_test(text, compile)
    with open("tests/001_0_add.c") as f:
        assert f.read() == code
    assert out == "3\r\n"

def test_sub():
    text = "1000 999 - print"
    code, out = run_test(text, compile)
    with open("tests/001_1_sub.c") as f:
        assert f.read() == code
    assert out == "1\r\n"

def test_mul():
    text = "400 200 * 3 * print"
    code, out = run_test(text, compile)
    with open("tests/001_2_mul.c") as f:
        assert f.read() == code
    assert out == "240000\r\n"

def test_div():
    text = "500 20 / print"
    code, out = run_test(text, compile)
    with open("tests/001_3_div.c") as f:
        assert f.read() == code
    assert out == "25\r\n"
