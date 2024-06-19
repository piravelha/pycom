
import re

class Location:
    def __init__(self, file, line, column) -> None:
        self.file = file
        self.line = line
        self.column = column
    def __repr__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}:"

class Token:
    def __init__(self, name, value, location) -> None:
        self.name = name
        self.value = value
        self.location = location
    def __repr__(self) -> str:
        if self.value is None:
            return f"[{self.name}]"
        return f"[{self.name}:{self.value}]"

class Lexer:
    def __init__(self) -> None:
        self.patterns: list[tuple[str, str]] = []
        self.skips = []
    def add_token(self, name: str, regex: str = None) -> None:
        if not regex:
            regex = name
        self.patterns.append((name, regex))
    def skip(self, regex: str) -> None:
        self.skips.append(regex)
    def convert_regexes(self) -> None:
        new_patterns = []
        for (name, regex) in self.patterns:
            if regex.startswith("^") or name == regex:
                new_patterns.append((name, regex))
            else:
                new_patterns.append((name, "^" + regex))
        self.patterns = new_patterns
        new_skips = []
        for skip in self.skips:
            if skip.startswith("^"):
                new_skips.append(skip)
            else:
                new_skips.append("^" + skip)
        self.skips = new_skips
    def lex(self, file: str, code: str) -> list[Token]:
        tokens = []
        line = 1
        column = 1
        self.convert_regexes()
        while len(code) > 0:
            matched = False
            for skip in self.skips:
                location = Location(file, line, column)
                if not re.match(skip, code): continue
                m = re.match(skip, code)
                matched = True
                for char in m.group(0):
                    if char == "\n":
                        line += 1
                        column = 1
                        continue
                    column += 1
                    code = code[1:]
            for (name, pattern) in self.patterns:
                location = Location(file, line, column)
                if name == pattern:
                    if not code.startswith(pattern): continue
                    m = pattern
                else:
                    if not re.match(pattern, code): continue
                    m = re.match(pattern, code).group(0)
                matched = True
                for char in m:
                    if char == "\n":
                        line += 1
                        column = 1
                        continue
                    column += 1
                    code = code[1:]
                tokens.append(Token(name, m, location))
            location = Location(file, line, column)
            if not matched:
                print(f"{location} SYNTAX ERROR: Unknown character: '{code[0]}'")
                exit(1)
        return tokens