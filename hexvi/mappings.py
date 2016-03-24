''' Exports MappingCollection. '''

class _Node(object):
    '''
    One node within a DFA.
    This is where the user naviages to by pressing a key.
    '''
    def __init__(self):
        self.func = None
        self.arg_proxy = None

class _NodeTraversal(object):
    ''' Path that keeps track of visited Nodes. '''
    def __init__(self, node, parent_traversal=None, symbol=None):
        self.node = node
        if parent_traversal:
            self.args = parent_traversal.args + []
            self.path = parent_traversal.path + [symbol]
        else:
            self.args = []
            self.path = [symbol] if symbol is not None else []

class _NFA(object):
    ''' The structure that represents the links between nodes. '''
    def __init__(self):
        self.delta = {}
        self.init_state = _Node()

    def connections(self, state, symbol):
        '''
        Retrieves the list of nodes reachable from the source state by the
        given key.
        '''
        try:
            return self.delta[state][symbol]
        except KeyError:
            return []

    def connect(self, state1, state2, symbol):
        ''' Connects two nodes with given key. '''
        if state1 not in self.delta:
            self.delta[state1] = {}
        if symbol not in self.delta[state1]:
            self.delta[state1][symbol] = set()
        self.delta[state1][symbol].add(state2)

class _NFATraverser(object):
    '''
    An engine that traverses the NFA by consuming user keys. Some keys get
    converted to arguments, that the final function is called with.
    '''
    def __init__(self, nfa):
        self._nfa = nfa
        self._current_traversals = None
        self.reset()

    def reset(self):
        ''' Makes keypress state back as if user just started the program. '''
        self._current_traversals = [_NodeTraversal(self._nfa.init_state)]

    def consume(self, symbol):
        ''' Consumes one key and navigates the NFA. '''
        target_traversals = []
        for traversal in self._current_traversals:
            for neighbour_node in self._nfa.connections(traversal.node, symbol):
                target_traversals += [self._extend_traversal(
                    traversal, neighbour_node, symbol)]
        self._current_traversals = target_traversals
        return target_traversals

    @staticmethod
    def _extend_traversal(source_traversal, target_node, symbol):
        res = _NodeTraversal(target_node, source_traversal, symbol)
        if target_node.arg_proxy:
            if id(source_traversal.node) != id(target_node):
                res.args.append('')
            res.args[-1] += symbol
        return res

class _ArgumentProxy(object):
    '''
    A class that's used to collect certain keypresses as variables/arguments to
    the final function.

    Args:
        name: can be used in bindings in place of "a", "ctrl q" etc.
        keys: list of keys that can be pressed to make it count as an argument.
        loop: whether to allow multiple keypresses.
    '''
    def __init__(self, name, keys, loop=False):
        self.name = name
        self.keys = keys
        self.loop = loop

class MappingCollection(object):
    '''
    Vim mapping emulator. Uses non-deterministic finite state automata, where each
    edge represents a keypress.
    '''

    def __init__(self):
        arg_proxies = [
            _ArgumentProxy('dec', list('0123456789'), loop=True),
            _ArgumentProxy('hex', list('0123456789abcdefABCDEF'), loop=True),
        ]

        self._arg_proxies = {b.name: b for b in arg_proxies}
        self._nfa = _NFA()
        self._compile()

    def add(self, path, func):
        ''' Adds a binding and associates it with a given function. '''
        state = self._nfa.init_state
        for i, symbol in enumerate(path):
            next_state = _Node()
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
        self._compile()

    def _compile(self):
        ''' Compiles current bindings into a NFA. '''
        self._traverser = _NFATraverser(self._nfa)

    def keypress(self, key):
        '''
        Consumes one keypress and navigates the NFA. If it reaches a state
        associated with a function, calls it and resets the state back to zero.
        '''
        traversals = self._traverser.consume(key)
        if not traversals:
            self._traverser.reset()
        else:
            for traversal in traversals:
                if traversal.node.func:
                    traversal.node.func(traversal)
                    self.reset()
                    return True
        return False

    def reset(self):
        ''' Resets the NFA state. '''
        self._traverser.reset()
