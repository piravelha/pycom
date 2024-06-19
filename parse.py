from lex import Token, Location, Lexer


class Parser:
    def __init__(self, parse):
        self.parse_fn = parse
    def raw_parse(self, tokens):
        parse = self.parse_fn()
        if isinstance(parse, Parser):
            return parse.raw_parse(tokens)
        return parse(tokens)
    def parse(self, tokens):
        result = self.raw_parse(tokens)
        if isinstance(result, ParseError):
            print(result.format())
            exit(1)
        return result

class ParseError:
    def __init__(self, expected, got, location):
        self.expected = expected
        self.got = got
        self.location = location
    def filter_expected(self):
        unique = []
        for exp in self.expected:
            if exp not in unique:
                unique.append(exp)
        self.expected = unique
    def format(self):
        self.filter_expected()
        message = f"{str(self.location)} PARSE ERROR: Expected "
        for i, exp in enumerate(self.expected):
            if i > 0 and i < len(self.expected) - 1:
                message += ", "
            message += f"'{exp}'"
            if i == len(self.expected) - 2:
                message += " or "
        message += f", but got '{self.got}' instead"
        return message

class Tree:
    def __init__(self, type, nodes, location, rest):
        self.type = type
        self.nodes = nodes
        self.location = location
        self.rest = rest
    def __repr__(self):
        nodes = ", ".join([str(n) for n in self.nodes])
        return f"{self.type}({nodes})"
    
_default_parser_config = [Location("?", -1, -1), []]

class C:
    @staticmethod
    def IntLiteral(value):
        return Tree("C_IntLiteral", [value], *_default_parser_config)
    @staticmethod
    def StringLiteral(value):
        return Tree("C_StringLiteral", [value], *_default_parser_config)
    @staticmethod
    def Identifier(value):
        return Tree("C_Identifier", [value], *_default_parser_config)
    @staticmethod
    def Variable(value):
        return Tree("C_Variable", [value], *_default_parser_config)
    @staticmethod
    def BinaryOp(left, op, right):
        return Tree("C_BinaryOp", [left, op, right], *_default_parser_config)
    @staticmethod
    def Call(func, *values):
        return Tree("C_Call", [func, *values], *_default_parser_config)
    @staticmethod
    def Statement(expr):
        return Tree("C_Statement", [expr], *_default_parser_config)
    @staticmethod
    def Return(value):
        return Tree("C_Return", [value], *_default_parser_config)
    @staticmethod
    def Block(*statements):
        return Tree("C_Block", statements, *_default_parser_config)
    @staticmethod
    def Type(value):
        return Tree("C_Type", [value], *_default_parser_config)
    @staticmethod
    def Function(ret, name, params, body):
        return Tree("C_Function", [ret, name, params, body], *_default_parser_config)
    @staticmethod
    def IncludeStd(file):
        return Tree("C_IncludeStd", [file], *_default_parser_config)
    @staticmethod
    def Program(macros, body):
        return Tree("C_Program", [macros, body], *_default_parser_config)

def token(name: str):
    def parse(tokens):
        if len(tokens) == 0:
            return ParseError([name], "EOF", Location("?", -1, -1))
        if tokens[0].name != name:
            return ParseError([name], tokens[0].value, tokens[0].location)
        return Tree(name, [tokens[0].value], tokens[0].location, tokens[1:])
    return Parser(lambda: parse)

def some(name, parser):
    def parse(tokens):
        head = parser.raw_parse(tokens)
        if isinstance(head, ParseError):
            return head
        tokens = head.rest
        tail = some(name, parser).raw_parse(tokens)
        if isinstance(tail, ParseError):
            return Tree(name, [head], head.location, head.rest)
        return Tree(name, [head] + tail.nodes, tail.location)
    return Parser(lambda: parse)

def many(name, parser):
    def parse(tokens):
        result = some(name, parser).raw_parse(tokens)
        if isinstance(result, ParseError):
            return Tree(name, [], Location("?", -1, -1), tokens)
        return result
    return Parser(lambda: parse)

def seq(type: str, *parsers):
    def parse(tokens):
        last = tokens[-1] if tokens else None
        first = tokens[0] if tokens else None
        bindings = []
        for parser in parsers:
            binding = False
            if isinstance(parser, list):
                parser = parser[0]
                binding = True
            if isinstance(parser, str):
                parser = token(parser)
            tree = parser.raw_parse(tokens)
            if isinstance(tree, ParseError):
                if not tokens and last:
                    return ParseError(tree.expected, tree.got, last.location)
                return tree
            if binding:
                bindings.append(tree)
            tokens = tree.rest
        return Tree(type, bindings, first.location, tokens)
    return Parser(lambda: parse)

def alt(name, *parsers):
    def parse(tokens: list[Token]):
        expected = []
        got = tokens[0].name if tokens else "EOF"
        location = tokens[0].location if tokens else Location("?", -1, -1)
        for parser in parsers:
            if isinstance(parser, str):
                parser = token(parser)
            tree = parser.raw_parse(tokens)
            if isinstance(tree, Tree):
                return Tree(name, [tree], tree.location)
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


def inline_alt(*parsers):
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
