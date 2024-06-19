from src.lex import Lexer
from src.parse import Parser, alt, some, Tree, C
from src.transform import Transformer
from src.codegen import generate_c
from typing import Literal

lexer = Lexer()
lexer.add_token("INT", r"\d+")
lexer.add_token("+ or -", r"[+\-]")
lexer.add_token("* or /", r"[*/%]")
lexer.add_token(".")
lexer.add_token("print")
lexer.skip(r"\s+")

atom_parser = Parser(lambda: alt(
    "INT",
    "+ or -",
    "* or /",
    "print",
    ".",
))
expr_parser = some("Expr", atom_parser)

transformer = Transformer()

stack_top = 0
initialized_env: dict[int, Literal[True]] = {}

@transformer.new_rule("INT")
def transform_int(value: str):
    global stack_top, initialized_env
    new = C.Identifier(f"s{stack_top}")
    lit = C.IntLiteral(value)
    if initialized_env.get(stack_top):
        tree = C.Assignment(new, lit)
    else:
        initialized_env[stack_top] = True
        tree = C.VariableDeclaration(C.IntType(), new, lit)
    stack_top += 1
    return tree

@transformer.new_rule("+ or -")
@transformer.new_rule("* or /")
def transform_binary_op(op: str):
    global stack_top, initialized_env
    left = C.Identifier(f"s{stack_top-2}")
    right = C.Identifier(f"s{stack_top-1}")
    body = C.BinaryOperator(left, op, right)
    tree = C.VariableDeclaration(C.IntType(), left, body)
    if initialized_env.get(stack_top-2):
        tree = C.Assignment(left, body)
    else:
        initialized_env[stack_top-2] = True
    stack_top -= 1
    return tree

@transformer.new_rule("print")
def transform_print(_):
    global stack_top
    tree = C.Statement(C.Call(
        C.Identifier("printf"),
        C.StringLiteral(r"%d\n"),
        C.Identifier(f"s{stack_top-1}")
    ))
    stack_top -= 1
    return tree

@transformer.new_rule(".")
def transform_dup(_):
    global stack_top, initialized_env
    new = C.Identifier(f"s{stack_top}")
    old = C.Identifier(f"s{stack_top-1}")
    tree = C.VariableDeclaration(C.IntType(), new, old)
    if initialized_env.get(stack_top):
        tree = C.Assignment(new, old)
    stack_top += 1
    return tree

@transformer.new_rule("Expr")
def transform_expr(*atoms: Tree):
    atoms_list = [transformer.transform(a) for a in atoms]
    return C.Block(*atoms_list)

@transformer.new_rule("#Start")
def transform(tree: Tree):
    tree = transformer.transform(tree)
    return C.Program(
        C.Include("stdio.h"),
        C.FunctionDeclaration(
            C.IntType(),
            C.Identifier("main"),
            C.ParameterList(),
            tree,
        ),
    )

def compile(file: str, text: str, out_path: str = "out.c"):
    global stack_top, initialized_env
    stack_top = 0
    initialized_env = {}
    tokens = lexer.lex(file, text)
    tree = expr_parser.parse(tokens)
    c_tree = transformer.start(tree)
    c_code = generate_c(c_tree)
    with open(out_path, "w") as f:
        f.write(c_code)
