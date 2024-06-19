from lex import Lexer
from parse import Parser, inline_alt, seq, many, C
from transform import Transformer
from codegen import generate_c

# Lexing

lexer = Lexer()

lexer.add_token("+")
lexer.add_token("-")
lexer.add_token("*")
lexer.add_token("=")
lexer.add_token("(")
lexer.add_token(")")
lexer.add_token("fn")
lexer.add_token(";")
lexer.add_token("IDENTIFIER", r"[a-zA-Z_][a-zA-Z_0-9]*")
lexer.add_token("INT", r"\d+")
lexer.skip(r"\s+")

# Parsing

start_parser = Parser(lambda: seq("Start",
    [many("Funcs", func_parser)],
    [expr_parser],
))

func_parser = Parser(lambda: seq("Func",
    "fn",
    ["IDENTIFIER"],
    "(",
    ["IDENTIFIER"],
    ")",
    "=",
    [expr_parser],
    ";"
))

expr_parser = Parser(lambda: inline_alt(
    plus_parser,
))

plus_parser = Parser(lambda: inline_alt(
    seq("Plus",
        [minus_parser],
        "+",
        [minus_parser],
    ),
    minus_parser,
))

minus_parser = Parser(lambda: inline_alt(
    seq("Minus",
        [mult_parser],
        "-",
        [mult_parser],
    ),
    mult_parser,
))

mult_parser = Parser(lambda: inline_alt(
    seq("Mult",
        [atom_parser],
        "*",
        [atom_parser],
    ),
    atom_parser,
))

atom_parser = Parser(lambda: inline_alt(
    call_parser,
    "IDENTIFIER",
    "INT",
))

call_parser = Parser(lambda: seq("Call",
    ["IDENTIFIER"],
    "(",
    [expr_parser],
    ")",
))

# Transforming

transformer = Transformer()

@transformer.new_rule("INT")
def transform_int(n):
   return C.IntLiteral(n)

@transformer.new_rule("IDENTIFIER")
def transform_identifier(i):
    return C.Variable(i)

@transformer.new_rule("Call")
def transform_call(f, x):
    x = transformer.transform(x)
    if f.nodes[0] == "print":
        return C.Call(C.Identifier("printf"), C.StringLiteral(r"%d\n"), x)
    f = transformer.transform(f)
    return C.Call(f, x)

@transformer.new_rule("Mult")
def transform_mult(l, r):
    l = transformer.transform(l)
    r = transformer.transform(r)
    return C.BinaryOp(l, "*", r)

@transformer.new_rule("Minus")
def transform_plus(l, r):
    l = transformer.transform(l)
    r = transformer.transform(r)
    return C.BinaryOp(l, "-", r)

@transformer.new_rule("Plus")
def transform_plus(l, r):
    l = transformer.transform(l)
    r = transformer.transform(r)
    return C.BinaryOp(l, "+", r)

@transformer.new_rule("Func")
def transform_func(n, p, b):
    n = transformer.transform(n)
    p = transformer.transform(p)
    b = transformer.transform(b)
    return C.Function(C.Type("int"), n, [(C.Type("int"), p)], C.Block(
        C.Return(b)
    ))

@transformer.new_rule("Funcs")
def transform_func(*funcs):
    return C.Block(*[transformer.transform(f) for f in funcs])

@transformer.new_rule("Start")
def transform_start(funcs, body):
    funcs = transformer.transform(funcs)
    body = transformer.transform(body)
    return C.Block(
        funcs,
        C.Function(C.Type("int"), C.Identifier("main"), [], C.Block(
            C.Statement(body),
            C.Return(C.IntLiteral("0")),
        ))
    )

@transformer.new_rule("#Start")
def transform_start_(tree):
    tree = transformer.transform(tree)
    return C.Program(
        [C.IncludeStd("stdio.h")],
        tree,
    )

# Codegen

if __name__ == "__main__":
    text = """
        fn negate(x) = 0 - x;
        print(negate(2))
    """
    tokens = lexer.lex("<stdin>", text)
    tree = start_parser.parse(tokens)
    tree = transformer.transform(tree, start=True)
    print(generate_c(tree))
