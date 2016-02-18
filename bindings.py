import sys

class Node(object):
    __id = 0

    def __init__(self):
        self.func = None
        self.binding = None
        self.id = Node.__id
        Node.__id += 1

    @property
    def is_final(self):
        return self.func is not None

class NodeTraversal(object):
    def __init__(self, node, parent_traversal = None):
        self.node = node
        if parent_traversal:
            self.args = parent_traversal.args + []
        else:
            self.args = []

class NFA(object):
    def __init__(self):
        self.delta = {}
        self.init_state = Node()

    def connections(self, state, symbol):
        try:
            return self.delta[state][symbol]
        except KeyError:
            return []

    def connect(self, state1, state2, symbol):
        if state1 not in self.delta:
            self.delta[state1] = {}
        if symbol not in self.delta[state1]:
            self.delta[state1][symbol] = set()
        self.delta[state1][symbol].add(state2)

    def traverse(self, state, path):
        for symbol in path:
            state = self.delta[state][symbol]
        return state

class NFATraverser(object):
    def __init__(self, nfa):
        self._nfa = nfa
        self.reset()

    def reset(self):
        self.current_traversals = [NodeTraversal(self._nfa.init_state)]

    def consume(self, symbol):
        target_traversals = []
        for traversal in self.current_traversals:
            for neighbour_node in self._nfa.connections(traversal.node, symbol):
                new_traversal = NodeTraversal(neighbour_node, traversal)
                if neighbour_node.binding:
                    if traversal.node.id != neighbour_node.id:
                        new_traversal.args.append('')
                    new_traversal.args[-1] += symbol
                elif traversal.node.binding:
                    new_traversal.args[-1] = traversal.node.binding.postprocessor(new_traversal.args[-1])
                target_traversals += [new_traversal]
        self.current_traversals = target_traversals
        return target_traversals

class ArgumentBinding(object):
    def __init__(self, name, keys, postprocessor=lambda x: x, loop=False):
        self.name = name
        self.keys = keys
        self.postprocessor = postprocessor
        self.loop = loop

class BindingCollection(object):
    def __init__(self):
        arg_bindings = [
            ArgumentBinding('<number>', list('0123456789'), lambda x: int(x), loop=True),
            ArgumentBinding('<hex>', list('0123456789abcdefABCDEF'), lambda x: int(x, 16), loop=True),
        ]
        self._arg_bindings = {b.name: b for b in arg_bindings}
        self._nfa = NFA()

    def add(self, path, func):
        state = self._nfa.init_state
        for i, symbol in enumerate(path):
            next_state = Node()
            if symbol in self._arg_bindings:
                next_state.binding = self._arg_bindings[symbol]
                for arg_symbol in next_state.binding.keys:
                    self._nfa.connect(state, next_state, arg_symbol)
                    if next_state.binding.loop:
                        self._nfa.connect(next_state, next_state, arg_symbol)
            else:
                if i == len(path) - 1:
                    next_state.func = func
                self._nfa.connect(state, next_state, symbol)
            state = next_state

    def compile(self):
        self._traverser = NFATraverser(self._nfa)

    def keypress(self, key):
        return self._consume_key(key)

    def _consume_key(self, key):
        traversals = self._traverser.consume(key)
        if not traversals:
            self._traverser.reset()
        else:
            for traversal in traversals:
                if traversal.node.is_final:
                    traversal.node.func(*traversal.args)
                    self.reset()
                    return True
        return False

    def reset(self):
        self._args = []
        self._active_arg_binding = False
        self._traverser.reset()
