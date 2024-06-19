from src.parse import Parser, seq, alt
from src.lex import Lexer

lexer = Lexer()
lexer.add_token("INT", r"\d+")
lexer.add_token("+")
lexer.add_token("*")
lexer.add_token("(")
lexer.add_token(")")
lexer.skip(r"\s+")

atom_parser = Parser(lambda: alt(
    "INT",
    seq("Expr",
        "(",
        [expr_parser],
        ")"
    )
))
term_parser = Parser(lambda: alt(
    seq("Term",
        [atom_parser],
        "*",
        [atom_parser],    
    ),
    atom_parser,
))
expr_parser = Parser(lambda: alt(
    seq("Expr",
        [term_parser],
        "+",
        [term_parser],    
    ),
    term_parser
))

def test_math_1():
    text = "(1 + 2) * 3"
    tokens = lexer.lex("<test>", text)
    tree = expr_parser.parse(tokens)
    assert repr(tree) == "Term(Expr(Expr(INT(1), INT(2))), INT(3))"

def test_math_2():
    text = "(4 + 1) * 2)"
    tokens = lexer.lex("<test>", text)
    tree = expr_parser.parse_error(tokens)
    assert tree == "<test>:1:12: SYNTAX ERROR: Expected EOF, but got ')'"

def test_math_3():
    text = "(10 *)"
    tokens = lexer.lex("<test>", text)
    tree = expr_parser.parse_error(tokens)
    assert tree == "<test>:1:5: SYNTAX ERROR: Expected ')', but got '*' instead"

def test_math_4():
    text = "(10 * 2 3)"
    tokens = lexer.lex("<test>", text)
    tree = expr_parser.parse_error(tokens)
    assert tree == "<test>:1:9: SYNTAX ERROR: Expected ')', but got '3' instead"

def test_math_5():
    text = "(7 - 2"
    tokens = lexer.lex_error("<test>", text)
    assert tokens == "<test>:1:4: SYNTAX ERROR: Unknown character: '-'"

def test_math_6():
    text = "(1 * 1"
    tokens = lexer.lex("<test>", text)
    tree = expr_parser.parse_error(tokens)
    assert tree == "<test>:1:6: SYNTAX ERROR: Expected ')', but got 'EOF' instead"
