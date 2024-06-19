from lex import Lexer
from parse import Parser, seq, inline_alt, some, C
from transform import Transformer
from codegen import generate_c

lexer = Lexer()

lexer.add_token("INT", r"\d+")
lexer.add_token("+")
lexer.add_token("print")

lexer.skip(r"\s+")

atom_parser = Parser(lambda: inline_alt(
  "INT",
  "+",
  "print"
))

expr_parser = some("Expr", atom_parser)

transformer = Transformer()

stack_top = 0
id_counts = {}

@transformer.new_rule("INT")
def transform_int(value):
  global stack_top, id_count
  a = id_counts.get(stack_top, 0)
  tree = C.VariableDeclaration(
    C.Type("int"),
    C.Identifier(f"s{a}_{stack_top}"),
    C.IntLiteral(value),
  )
  stack_top += 1
  return tree

@transformer.new_rule("+")
def transform_plus(_):
  global stack_top, id_counts
  a = id_counts.get(stack_top-2, 0)
  b = id_counts.get(stack_top-1, 0)
  tree = C.VariableDeclaration(
    C.Type("int"),
    C.Identifier(f"s{a+1}_{stack_top-2}"),
    C.BinaryOperator(
      C.Identifier(f"s{a}_{stack_top-2}"),
      "+",
      C.Identifier(f"s{b}_{stack_top-1}"),
    ),
  )
  stack_top -= 1
  return tree

@transformer.new_rule("print")
def transform_print(_):
  global stack_top, id_counts
  a = id_counts.get(stack_top, 0)
  tree = C.Statement(C.Call(
    C.Identifier("printf"),
    C.StringLiteral(r"%d\n"),
    C.Identifier(f"s{a}_{stack_top-1}")
  ))
  return tree

@transformer.new_rule("Expr")
def transform_expr(*atoms):
  atoms = [transformer.transform(a) for a in atoms]
  return C.Block(*atoms)

@transformer.new_rule("#Start")
def transform(tree):
  tree = transformer.transform(tree)
  return C.Program(
    C.Include("stdio.h"),
    C.FunctionDeclaration(
      C.Type("int"),
      C.Identifier("main"),
      C.ParameterList(),
      tree,
    ),
  )

if __name__ == "__main__":
  text = """
    1 2 + print
  """
  tokens = lexer.lex("<stdin>", text)
  tree = expr_parser.parse(tokens)
  c_tree = transformer.start(tree)
  c_code = generate_c(c_tree)
  with open("out.c", "w") as f:
    f.write(c_code)
