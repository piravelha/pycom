from parse import Tree

var_counter = 0
def new_var():
    global var_counter
    var = f"v{var_counter}"
    var_counter += 1
    return var

def get_indents_c(code: str) -> list[int]:
    lines = code.splitlines()
    indent = 0
    indent_guides: list[int] = []
    for line in lines:
        if line.count("}"):
            indent -= line.count("}")
        indent_guides.append(indent)
        if line.count("{"):
            indent += line.count("{")
    return indent_guides

def generate_c(tree: Tree, env: dict[str, str] = {}) -> str:
    if tree.type == "C_IntLiteral":
        return str(tree.nodes[0])
    if tree.type == "C_CharLiteral":
        return f"'{tree.nodes[0]}'"
    if tree.type == "C_StringLiteral":
      return f"\"{tree.nodes[0]}\""
    if tree.type == "C_Identifier":
        return str(tree.nodes[0])
    if tree.type == "C_Variable":
        if env.get(tree.nodes[0]):
            return env[tree.nodes[0]]
        else:
            env[tree.nodes[0]] = new_var()
            return env[tree.nodes[0]]
    if tree.type == "C_ArgumentList":
        args = [generate_c(a) for a in tree.nodes]
        return ", ".join(args)
    if tree.type == "C_BinaryOperator":
        left, op, right = tree.nodes
        left = generate_c(left)
        right = generate_c(right)
        return f"({left} {op} {right})"
    if tree.type == "C_UnaryOperator":
      op, right = tree.nodes
      right = generate_c(right)
      return f"({op}{right})"
    if tree.type == "C_Call":
        name = generate_c(tree.nodes[0])
        nodes = ", ".join([generate_c(node) for node in tree.nodes[1:]])
        return f"{name}({nodes})"
    if tree.type == "C_Statement":
        expr = generate_c(tree.nodes[0])
        return f"{expr};\n"
    if tree.type == "C_Return":
        value = generate_c(tree.nodes[0])
        return f"return {value};\n"
    if tree.type == "C_While":
      cond, body = tree.nodes
      return f"while ({cond}) {body}"
    if tree.type == "C_If":
      cond, body = tree.nodes
      return f"if ({cond}) {body}"
    if tree.type == "C_IfElse":
      cond, body, elbody = tree.nodes
      return f"if ({cond}) {body} else {elbody}"
    if tree.type == "C_StatementList":
      statements = [generate_c(s) for s in tree.nodes]
      return "\n".join(statements) + "\n"
    if tree.type == "C_Block":
        code = "{\n"
        for node in tree.nodes:
            code += generate_c(node)
        return code + "}\n"
    if tree.type == "C_Type":
        return str(tree.nodes[0])
    if tree.type == "C_Parameter":
      type, name = tree.nodes
      return f"{type} {name}"
    if tree.type == "C_ParameterList":
      return f", ".join([generate_c(p) for p in tree.nodes])
    if tree.type == "C_VariableDeclaration":
      type, name, value = tree.nodes
      type = generate_c(type)
      name = generate_c(name)
      value = generate_c(value)
      return f"{type} {name} = {value};\n"
    if tree.type == "C_Assignment":
      name, value = tree.nodes
      name = generate_c(name)
      value = generate_c(value)
      return f"{name} = {value};\n"
    if tree.type == "C_FunctionDeclaration":
        ret, name, params, body = tree.nodes
        ret = generate_c(ret)
        name = generate_c(name)
        params = [f"{generate_c(p.nodes[0])} {generate_c(p.nodes[1])}" for p in params.nodes]
        body = generate_c(body)
        code = f"{ret} {name}("
        for i, param in enumerate(params):
            if i > 0:
                code += ", "
            code += param
        code += ") "
        code += body
        return code
    if tree.type == "C_Include":
        file = tree.nodes[0]
        return f"#include <{file}>\n"
    if tree.type == "C_DeclarationList":
      return "\n".join([generate_c(d) for d in tree.nodes])
    if tree.type == "C_Program":
        decls = "\n".join([generate_c(d) for d in tree.nodes])
        indents = get_indents_c(decls)
        formatted = ""
        for indent, line in zip(indents, decls.splitlines()):
            formatted += indent * "    " + line.lstrip() + "\n"
        return formatted
    assert False, f"Not implemented: '{tree.type}'"
