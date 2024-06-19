
import re

class Location:
    def __init__(self, file: str, line: int, column: int) -> None:
        self.file = file
        self.line = line
        self.column = column
    def __repr__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}:"

class Token:
    def __init__(self, name: str, value: str, location: Location) -> None:
        self.name = name
        self.value = value
        self.location = location
    def __repr__(self) -> str:
        if not self.value or self.value == self.name:
            return f"[{self.name}]"
        return f"[{self.name}:{self.value}]"

class Lexer:
    def __init__(self) -> None:
        self.patterns: list[tuple[str, str]] = []
        self.skips: list[str] = []
    def add_token(self, name: str, regex: str = "") -> None:
        if not regex:
            regex = name
        self.patterns.append((name, regex))
    def skip(self, regex: str) -> None:
        self.skips.append(regex)
    def convert_regexes(self) -> None:
        new_patterns: list[tuple[str, str]] = []
        for (name, regex) in self.patterns:
            if regex.startswith("^") or name == regex:
                new_patterns.append((name, regex))
            else:
                new_patterns.append((name, "^" + regex))
        self.patterns = new_patterns
        new_skips: list[str] = []
        for skip in self.skips:
            if skip.startswith("^"):
                new_skips.append(skip)
            else:
                new_skips.append("^" + skip)
        self.skips = new_skips
    def lex_error(self, file: str, code: str) -> str:
        tokens: list[Token] = []
        line = 1
        column = 1
        self.convert_regexes()
        while len(code) > 0:
            matched = False
            for skip in self.skips:
                location = Location(file, line, column)
                if not re.match(skip, code): continue
                m = re.match(skip, code)
                assert m is not None
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
                m_str: str
                if name == pattern:
                    if not code.startswith(pattern): continue
                    m_str = pattern
                else:
                    match = re.match(pattern, code)
                    if match is None: continue
                    m_str = match.group(0)
                matched = True
                for char in m_str:
                    if char == "\n":
                        line += 1
                        column = 1
                        continue
                    column += 1
                    code = code[1:]
                tokens.append(Token(name, m_str, location))
            location = Location(file, line, column)
            if not matched:
                return f"{location} SYNTAX ERROR: Unknown character: '{code[0]}'"
        return "No Errors Found (lex.py)"

    def lex(self, file: str, code: str) -> list[Token]:
        tokens: list[Token] = []
        line = 1
        column = 1
        self.convert_regexes()
        while len(code) > 0:
            matched = False
            for skip in self.skips:
                location = Location(file, line, column)
                if not re.match(skip, code): continue
                m = re.match(skip, code)
                assert m is not None
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
                m_str: str
                if name == pattern:
                    if not code.startswith(pattern): continue
                    m_str = pattern
                else:
                    match = re.match(pattern, code)
                    if match is None: continue
                    m_str = match.group(0)
                matched = True
                for char in m_str:
                    if char == "\n":
                        line += 1
                        column = 1
                        continue
                    column += 1
                    code = code[1:]
                tokens.append(Token(name, m_str, location))
            location = Location(file, line, column)
            if not matched:
                print(f"{location} SYNTAX ERROR: Unknown character: '{code[0]}'")
                exit(1)
        return tokens