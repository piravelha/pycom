from src.lex import Lexer
from src.parse import Parser, alt, seq, many, Tree, C
from src.transform import Transformer
from src.codegen import generate_c

# Lexing

lexer = Lexer()

lexer.add_token("+")
lexer.add_token("-")
lexer.add_token("!")
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

expr_parser = Parser(lambda: alt(
    plus_parser,
))

plus_parser = Parser(lambda: alt(
    seq("Plus",
        [minus_parser],
        "+",
        [minus_parser],
    ),
    minus_parser,
))

minus_parser = Parser(lambda: alt(
    seq("Minus",
        [mult_parser],
        "-",
        [mult_parser],
    ),
    mult_parser,
))

mult_parser = Parser(lambda: alt(
    seq("Mult",
        [unary_parser],
        "*",
        [unary_parser],
    ),
    unary_parser,
))

unary_parser = Parser(lambda: alt(
  seq("Unary",
    [alt(
      "+",
      "-",
      "!",
    )],
    [atom_parser],
  ),
  atom_parser,
))

atom_parser = Parser(lambda: alt(
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
def transform_int(n: str):
   return C.IntLiteral(n)

@transformer.new_rule("IDENTIFIER")
def transform_identifier(i: str):
    return C.Variable(i)

@transformer.new_rule("Call")
def transform_call(f: Tree, x: Tree):
    x = transformer.transform(x)
    if f.nodes[0] == "print":
        return C.Call(
            C.Identifier("printf"),
            C.StringLiteral(r"%d\n"),
            x,
        )
    f = transformer.transform(f)
    return C.Call(f, x)

@transformer.new_rule("Unary")
def transform_unary(op: Tree, r: Tree):
  r = transformer.transform(r)
  return C.UnaryOperator(op.nodes[0], r)

@transformer.new_rule("Mult")
def transform_mult(l: Tree, r: Tree):
    l = transformer.transform(l)
    r = transformer.transform(r)
    return C.BinaryOperator(l, "*", r)

@transformer.new_rule("Minus")
def transform_minus(l: Tree, r: Tree):
    l = transformer.transform(l)
    r = transformer.transform(r)
    return C.BinaryOperator(l, "-", r)

@transformer.new_rule("Plus")
def transform_plus(l: Tree, r: Tree):
    l = transformer.transform(l)
    r = transformer.transform(r)
    return C.BinaryOperator(l, "+", r)

@transformer.new_rule("Func")
def transform_func(n: Tree, p: Tree, b: Tree):
    n = transformer.transform(n)
    p = transformer.transform(p)
    b = transformer.transform(b)
    return C.FunctionDeclaration(
      C.Type("int"),
      n,
      C.ParameterList(
        C.Parameter(C.Type("int"), p),
      ),
      C.Block(
        C.Return(b)
      )
    )

@transformer.new_rule("Funcs")
def transform_funcs(*funcs: Tree):
    return C.DeclarationList(*[transformer.transform(f) for f in funcs])

@transformer.new_rule("Start")
def transform_start(funcs: Tree, body: Tree):
    funcs = transformer.transform(funcs)
    body = transformer.transform(body)
    return C.DeclarationList(
        funcs,
        C.FunctionDeclaration(C.Type("int"), C.Identifier("main"), C.ParameterList(), C.Block(
            C.Statement(body),
            C.Return(C.IntLiteral("0")),
        ))
    )

@transformer.new_rule("#Start")
def transform_start_(tree: Tree):
    tree = transformer.transform(tree)
    return C.Program(
        C.Include("stdio.h"),
        tree,
    )

# Codegen

if __name__ == "__main__":
    text = """
        fn negate(x) = -x;
        print(500 + negate(80))
    """
    tokens = lexer.lex("<stdin>", text)
    tree = start_parser.parse(tokens)
    tree = transformer.transform(tree, start=True)
    with open("out.c", "w") as f:
      f.write(generate_c(tree))
