# type: ignore

import re

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        return f'{self.type}({self.value})'

class Lexer:
    def __init__(self):
        self.token_rules = []
        self.skip_patterns = []

    def add_token(self, type, regex):
        self.token_rules.append((type, re.compile(f'^({regex})')))

    def skip(self, regex):
        self.skip_patterns.append(re.compile(f'^({regex})'))

    def tokenize(self, input):
        tokens = []
        while input:
            matched = False
            for skip_pattern in self.skip_patterns:
                match = skip_pattern.match(input)
                if match:
                    input = input[match.end():]
                    matched = True
                    break
            if matched:
                continue

            for type, pattern in self.token_rules:
                match = pattern.match(input)
                if match:
                    tokens.append(Token(type, match.group(1)))
                    input = input[match.end():]
                    matched = True
                    break
            if not matched:
                raise ValueError(f"Unexpected character: {input[0]}")
        return tokens

class ParserException(Exception):
    pass

class Node:
    def __init__(self, type, value=None):
        self.type = type
        self.value = value
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def __str__(self):
        if self.value:
            return f'{self.type}({self.value})'
        else:
            children_str = ', '.join(str(child) for child in self.children)
            return f'{self.type}({children_str})'

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def match(self, type):
        if self.position < len(self.tokens) and self.tokens[self.position].type == type:
            token = self.tokens[self.position]
            self.position += 1
            return token
        raise ParserException(f"Expected token {type} at position {self.position}")

    def lookahead(self, type):
        return self.position < len(self.tokens) and self.tokens[self.position].type == type

    def expr(self):
        return self.plus()

    def plus(self):
        node = self.mult()
        if self.lookahead('+'):
            plus_node = Node('Plus')
            plus_node.add_child(node)
            self.match('+')
            plus_node.add_child(self.mult())
            return plus_node
        return node

    def mult(self):
        node = self.atom()
        if self.lookahead('*'):
            mult_node = Node('Mult')
            mult_node.add_child(node)
            self.match('*')
            mult_node.add_child(self.atom())
            return mult_node
        return node

    def atom(self):
        if self.lookahead('INT'):
            return Node('Int', self.match('INT').value)
        if self.lookahead('IDENTIFIER'):
            return self.call()
        raise ParserException(f"Expected INT or IDENTIFIER at position {self.position}")

    def call(self):
        call_node = Node('Call')
        call_node.add_child(Node('Identifier', self.match('IDENTIFIER').value))
        self.match('(')
        call_node.add_child(self.expr())
        self.match(')')
        return call_node

class Codegen:
    class CNode:
        def __init__(self, type, value=None):
            self.type = type
            self.value = value
            self.children = []

        def add_child(self, child):
            self.children.append(child)

        def __str__(self):
            if self.value:
                return f'{self.type}({self.value})'
            else:
                children_str = ', '.join(str(child) for child in self.children)
                return f'{self.type}({children_str})'

    def transform(self, node):
        if node.type == 'Plus':
            plus_node = self.CNode('Plus')
            for child in node.children:
                plus_node.add_child(self.transform(child))
            return plus_node
        if node.type == 'Mult':
            mult_node = self.CNode('Mult')
            for child in node.children:
                mult_node.add_child(self.transform(child))
            return mult_node
        if node.type == 'Int':
            return self.CNode('Int', node.value)
        if node.type == 'Call':
            call_node = self.CNode('Call')
            call_node.add_child(self.CNode('Identifier', node.children[0].value))
            call_node.add_child(self.transform(node.children[1]))
            return call_node
        raise ValueError(f"Unknown node type: {node.type}")

    def generate_code(self, node):
        if node.type == 'Plus':
            return f'{self.generate_code(node.children[0])} + {self.generate_code(node.children[1])}'
        if node.type == 'Mult':
            return f'{self.generate_code(node.children[0])} * {self.generate_code(node.children[1])}'
        if node.type == 'Int':
            return node.value
        if node.type == 'Call':
            function_name = node.children[0].value
            if function_name == 'print':
                return f'printf("%d\\n", {self.generate_code(node.children[1])})'
            else:
                return f'{function_name}({self.generate_code(node.children[1])})'
        raise ValueError(f"Unknown CNode type: {node.type}")

    def generate_main(self, node):
        return f'#include <stdio.h>\n\nint main() {{\n    {self.generate_code(node)};\n    return 0;\n}}'

if __name__ == '__main__':
    lexer = Lexer()
    lexer.add_token('INT', r'\d+')
    lexer.add_token('IDENTIFIER', r'[a-zA-Z_][a-zA-Z_0-9]*')
    lexer.add_token('+', r'\+')
    lexer.add_token('*', r'\*')
    lexer.add_token('(', r'\(')
    lexer.add_token(')', r'\)')
    lexer.skip(r'\s+')

    input = 'print(34 + 17 * foo(2))'
    tokens = lexer.tokenize(input)
    parser = Parser(tokens)
    parse_tree = parser.expr()
    print('Parse Tree:', parse_tree)

    codegen = Codegen()
    c_tree = codegen.transform(parse_tree)
    print('C Tree:', c_tree)

    code = codegen.generate_main(c_tree)
    print('Generated C Code:\n', code)
