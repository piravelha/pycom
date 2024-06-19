from parse import Tree
import re

var_counter = 0
def new_var():
    global var_counter
    var = f"v{var_counter}"
    var_counter += 1
    return var

def get_indents_c(code: str):
    lines = code.splitlines()
    indent = 0
    indent_guides = []
    for line in lines:
        if line.count("}"):
            indent -= line.count("}")
        indent_guides.append(indent)
        if line.count("{"):
            indent += line.count("{")
    return indent_guides

def generate_c(tree, env={}, obsfuscate_strings=False):
    if tree.type == "C_IntLiteral":
        return str(tree.nodes[0])
    if tree.type == "C_StringLiteral":
        if obsfuscate_strings:
            return f"%STRING%"
        return f"\"{tree.nodes[0]}\""
    if tree.type == "C_Identifier":
        return str(tree.nodes[0])
    if tree.type == "C_Variable":
        if env.get(tree.nodes[0]):
            return env[tree.nodes[0]]
        else:
            env[tree.nodes[0]] = new_var()
            return env[tree.nodes[0]]
    if tree.type == "C_BinaryOp":
        left, op, right = tree.nodes
        left = generate_c(left)
        right = generate_c(right)
        return f"({left} {op} {right})"
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
    if tree.type == "C_Block":
        code = ""
        for node in tree.nodes:
            code += generate_c(node)
        return code
    if tree.type == "C_Type":
        return str(tree.nodes[0])
    if tree.type == "C_Function":
        ret, name, params, body = tree.nodes
        ret = generate_c(ret)
        name = generate_c(name)
        params = [f"{generate_c(t)} {generate_c(p)}" for (t, p) in params]
        body = generate_c(body)
        code = f"{ret} {name}("
        for i, param in enumerate(params):
            if i > 0:
                code += ", "
            code += param
        code += ") {\n"
        code += body
        code += "}\n"
        return code
    if tree.type == "C_IncludeStd":
        file = tree.nodes[0]
        return f"#include <{file}>\n"
    if tree.type == "C_Program":
        macros, body = tree.nodes
        macro_code = ""
        for mac in macros:
            macro_code += generate_c(mac)
        no_strs = generate_c(body, obsfuscate_strings=True)
        indents = get_indents_c(no_strs)
        code = generate_c(body)
        formatted = ""
        for indent, line in zip(indents, code.splitlines()):
            formatted += indent * "    " + line.lstrip() + "\n"
        return "\n" + macro_code + "\n" + formatted
    assert False, f"Not implemented: '{tree.type}'"