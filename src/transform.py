from src.parse import Tree
from typing import Any, Callable

class Transformer:
    def __init__(self):
        self.rules: dict[str, Callable[..., Any]] = {}
    def new_rule(self, name: str):
        def wrapper(fn: Callable[..., Any]):
            def impl(*args: Any):
                return fn(*args)
            self.rules[name] = fn
            return impl
        return wrapper
    def transform(self, tree: Tree | str, start: bool = False) -> Tree:
        if start:
            return self.rules["#Start"](tree)
        if isinstance(tree, Tree) and not self.rules.get(tree.type):
            assert False, f"Not implemented: '{tree.type}'"
        if not isinstance(tree, Tree):
            test: Any = tree
            any: Tree = test
            return any
        return self.rules[tree.type](*[n for n in tree.nodes])
    def start(self, tree: Tree | str):
        return self.transform(tree, True)
