from src.lex import Token, Location
from typing import Any, Callable


class Tree:
    def __init__(
            self,
            type: str,
            nodes: list[Any],
            location: Location = Location("?", -1, -1),
            rest: list[Token] = []):
        self.type = type
        self.nodes = nodes
        self.location = location
        self.rest = rest
    def __repr__(self):
        nodes = ", ".join([str(n) for n in self.nodes])
        return f"{self.type}({nodes})"

class ParseError:
    def __init__(self, expected: list[str], got: str, location: Location):
        self.expected = expected
        self.got = got
        self.location = location
    def filter_expected(self):
        unique: list[str] = []
        for exp in self.expected:
            if exp not in unique:
                unique.append(exp)
        self.expected = unique
    def format(self):
        self.filter_expected()
        message = f"{str(self.location)} SYNTAX ERROR: Expected "
        for i, exp in enumerate(self.expected):
            if i > 0 and i < len(self.expected) - 1:
                message += ", "
            message += f"'{exp}'"
            if i == len(self.expected) - 2:
                message += " or "
        message += f", but got '{self.got}' instead"
        return message

class Parser:
    def __init__(
            self,
            parse: Callable[[], Callable[[list[Token]], Tree | ParseError] | 'Parser']):
        self.parse_fn = parse
    def raw_parse(self, tokens: list[Token]) -> Tree | ParseError:
        parse = self.parse_fn()
        if isinstance(parse, Parser):
            return parse.raw_parse(tokens)
        return parse(tokens)
    def parse_error(self, tokens: list[Token]) -> str: 
        result = self.raw_parse(tokens)
        if isinstance(result, ParseError):
            return result.format()
        if result.rest:
            return f"{result.rest[0].location} SYNTAX ERROR: Expected EOF, but got '{result.rest[0].value}'"
        return "No Errors Found (parse.py)"
    def parse(self, tokens: list[Token]) -> Tree:
        result = self.raw_parse(tokens)
        if isinstance(result, ParseError):
            print(result.format())
            exit(1)
        if result.rest:
            print(f"{result.rest[0].location} SYNTAX ERROR: Expected EOF, but got '{result.rest[0].value}'")
            exit(1)
        return result

class C:
    @staticmethod
    def IntLiteral(value: str):
        return Tree("C_IntLiteral", [value])
    @staticmethod
    def CharLiteral(value: str):
        return Tree("C_CharLiteral", [value])
    @staticmethod
    def StringLiteral(value: str):
        return Tree("C_StringLiteral", [value])
    @staticmethod
    def Identifier(value: str):
        return Tree("C_Identifier", [value])
    @staticmethod
    def Variable(value: str):
        return Tree("C_Variable", [value])
    @staticmethod
    def ArgumentList(*args: Tree):
      return Tree("C_ArgumentList", [*args])
    @staticmethod
    def Call(func: Tree, *values: Tree):
        return Tree("C_Call", [func, *values])
    @staticmethod
    def UnaryOperator(op: str, value: Tree):
      return Tree("C_UnaryOperator", [op, value])
    @staticmethod
    def BinaryOperator(left: Tree, op: str, right: Tree):
        return Tree("C_BinaryOperator", [left, op, right])
    @staticmethod
    def Statement(expr: Tree):
        return Tree("C_Statement", [expr])
    @staticmethod
    def Return(value: Tree):
        return Tree("C_Return", [value])
    @staticmethod
    def While(cond: Tree, body: Tree):
        return Tree("C_While", [cond, body])
    @staticmethod
    def If(cond: Tree, body: Tree):
        return Tree("C_If", [cond, body])
    @staticmethod
    def IfElse(cond: Tree, body: Tree, elbody: Tree):
        return Tree("C_IfElse", [cond, body, elbody])
    @staticmethod
    def StatementList(*statements: Tree):
        return Tree("C_StatementList", [*statements])
    @staticmethod
    def Block(*statements: Tree):
      return Tree("C_Block", [*statements])
    @staticmethod
    def Parameter(type: Tree, name: Tree):
        return Tree("C_Parameter", [type, name])
    @staticmethod
    def ParameterList(*params: Tree):
        return Tree("C_ParameterList", [*params])
    @staticmethod
    def VariableDeclaration(type: Tree, name: Tree, value: Tree):
        return Tree("C_VariableDeclaration", [type, name, value])
    @staticmethod
    def Assignment(name: Tree, value: Tree):
        return Tree("C_Assignment", [name, value])
    @staticmethod
    def Type(value: str):
        return Tree("C_Type", [value])
    @staticmethod
    def FunctionDeclaration(ret: Tree, name: Tree, params: Tree, body: Tree):
        return Tree("C_FunctionDeclaration", [ret, name, params, body])
    @staticmethod
    def Include(file: str):
        return Tree("C_Include", [file])
    @staticmethod
    def DeclarationList(*decls: Tree):
        return Tree("C_DeclarationList", [*decls])
    @staticmethod
    def Program(*declarations: Tree):
        return Tree("C_Program", [*declarations])
    @staticmethod
    def IntType():
        return C.Type("int")
    @staticmethod
    def CharType():
        return C.Type("char")

def token(name: str):
    def parse(tokens: list[Token]):
        if len(tokens) == 0:
            return ParseError([name], "EOF", Location("?", -1, -1))
        if tokens[0].name != name:
            return ParseError([name], tokens[0].value, tokens[0].location)
        return Tree(name, [tokens[0].value], tokens[0].location, tokens[1:])
    return Parser(lambda: parse)

def some(name: str, parser: Parser) -> Parser:
    def parse(tokens: list[Token]):
        head = parser.raw_parse(tokens)
        if isinstance(head, ParseError):
            return head
        tokens = head.rest
        tail = some(name, parser).raw_parse(tokens)
        if isinstance(tail, ParseError):
            return Tree(name, [head], head.location, head.rest)
        return Tree(name, [head] + tail.nodes, tail.location)
    return Parser(lambda: parse)

def many(name: str, parser: Parser) -> Parser:
    def parse(tokens: list[Token]):
        result = some(name, parser).raw_parse(tokens)
        if isinstance(result, ParseError):
            return Tree(name, [], Location("?", -1, -1), tokens)
        return result
    return Parser(lambda: parse)

type SeqElem = str | Parser | list[SeqElem]

def seq(type: str, *parsers: SeqElem) -> Parser:
    def parse(tokens: list[Token]):
        last: Token = tokens[-1] if tokens else Token("", "", Location("?", -1, -1))
        first: Token = tokens[0] if tokens else Token("", "", Location("?", -1, -1))
        bindings: list[Tree] = []
        for parser in parsers:
            binding = False
            p: Parser
            def get_parser(s: SeqElem, binding: bool) -> tuple[Parser, bool]:
                p: Parser
                if isinstance(s, list):
                    p, binding = get_parser(s[0], binding)
                    binding = True
                elif isinstance(s, str):
                    p = token(s)
                else:
                    p = s
                return p, binding
            p, binding = get_parser(parser, binding)
            tree = p.raw_parse(tokens)
            if isinstance(tree, ParseError):
                if not tokens and last.value:
                    return ParseError(tree.expected, tree.got, last.location)
                return tree
            if binding:
                bindings.append(tree)
            tokens = tree.rest
        return Tree(type, bindings, first.location, tokens)
    return Parser(lambda: parse)

def alt(*parsers: Parser | str):
    def parse(tokens: list[Token]):
        expected = []
        got = tokens[0].name if tokens else "EOF"
        location = tokens[0].location if tokens else Location("?", -1, -1)
        for parser in parsers:
            if isinstance(parser, str):
                parser = token(parser)
            tree = parser.raw_parse(tokens)
            if isinstance(tree, Tree):
                return tree
            if tree.location.line == location.line and tree.location.column == location.column:
                expected.extend(tree.expected)
            elif len(tree.expected) > len(expected):
                expected = tree.expected
                location = tree.location if tree.location.line != -1 else location
                got = tree.got
            else:
                expected = tree.expected
                location = tree.location if tree.location.line != -1 else location
                got = tree.got
        return ParseError(expected, got, location)
    return Parser(lambda: parse)
