from parse import Tree

class Transformer:
    def __init__(self):
        self.rules = {}
    def new_rule(self, name):
        def wrapper(fn):
            def impl(*args):
                return fn(args)
            self.rules[name] = fn
            return impl
        return wrapper
    def transform(self, tree, start=False):
        if start:
            return self.rules["#Start"](tree)
        if not isinstance(tree, Tree):
            return tree
        if not self.rules.get(tree.type):
            return tree
        return self.rules[tree.type](*[n for n in tree.nodes])
