import sys

class Node(object):
    __id = 0

    def __init__(self):
        self.func = None
        self.arg_proxy = None
        self.id = Node.__id
        Node.__id += 1

class NodeTraversal(object):
    def __init__(self, node, parent_traversal=None, symbol=None):
        self.node = node
        if parent_traversal:
            self.args = parent_traversal.args + []
            self.path = parent_traversal.path + [symbol]
        else:
            self.args = []
            self.path = [symbol] if symbol is not None else []

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
                target_traversals += [self._extend_traversal(
                    traversal, neighbour_node, symbol)]
        self.current_traversals = target_traversals
        return target_traversals

    def _extend_traversal(self, source_traversal, target_node, symbol):
        res = NodeTraversal(target_node, source_traversal, symbol)
        if target_node.arg_proxy:
            if source_traversal.node.id != target_node.id:
                res.args.append('')
            res.args[-1] += symbol
        elif source_traversal.node.arg_proxy:
            res.args[-1] = (
                source_traversal.node.arg_proxy.postprocessor(res.args[-1]))
        return res

class ArgumentProxy(object):
    def __init__(self, name, keys, postprocessor=lambda x: x, loop=False):
        self.name = name
        self.keys = keys
        self.postprocessor = postprocessor
        self.loop = loop

class MappingCollection(object):
    def __init__(self):
        arg_proxies = [
            ArgumentProxy('dec', list('0123456789'), loop=True),
            ArgumentProxy('hex', list('0123456789abcdefABCDEF'), loop=True),
        ]

        self._arg_proxies = {b.name: b for b in arg_proxies}
        self._nfa = NFA()

    def add(self, path, func):
        state = self._nfa.init_state
        for i, symbol in enumerate(path):
            next_state = Node()
            if symbol in self._arg_proxies:
                next_state.arg_proxy = self._arg_proxies[symbol]
                for arg_symbol in next_state.arg_proxy.keys:
                    self._nfa.connect(state, next_state, arg_symbol)
                    if next_state.arg_proxy.loop:
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
                if traversal.node.func:
                    traversal.node.func(*traversal.args)
                    self.reset()
                    return True
        return False

    def reset(self):
        self._args = []
        self._active_arg_proxy = False
        self._traverser.reset()
