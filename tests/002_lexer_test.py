from src.lex import Lexer

def test_math_grammar():
    lexer = Lexer()
    lexer.add_token("INT", r"\d+")
    lexer.add_token("OPERATOR", r"[+\-*/^]")
    lexer.add_token("(")
    lexer.add_token(")")
    text = "(1+3(2/4)^2)/10"
    tokens = lexer.lex("<test>", text)
    with open("tests/002_math_grammar.txt") as f:
        expected = f.read()
    assert repr(tokens) == expected
    lexer.skip(r"\s+")
    text = "(1 + 3(2 / 4)^2) / 10"
    tokens = lexer.lex("<test>", text)
    assert repr(tokens) == expected