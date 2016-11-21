from collections import defaultdict
from typing import List, Dict, Set, Optional, Tuple, Callable, Iterator


UNKNOWN_VARIABLE_TYPE = 'Unknown variable type %r'
MISSING_CLOSING_BRACE = 'Unexpected end of input (missing closing brace)'
MISSING_BACKSLASH = (
    'Unexpected end of input (missing character after backslash)')


class AutomataTraversal:
    def __init__(
            self,
            nodes: 'Tuple[AutomataNode, ...]',
            parent: 'AutomataTraversal'=None) -> None:
        self.nodes = nodes
        self.user_input = ''
        self.recorded_variable = None  # type: Optional[str]
        self.variables = defaultdict(str)  # type: Dict[str, str]

        if parent:
            self.user_input = parent.user_input
            self.recorded_variable = parent.recorded_variable
            for k, v in parent.variables.items():
                self.variables[k] = v

    def __repr__(self) -> str:
        return 'traversal[%r, %r]' % (self.nodes, self.user_input)


class AutomataNode:
    _node_number = 0

    def __init__(self) -> None:
        self.name = '%s%s' % (
            self.__class__.__name__, AutomataNode._node_number)
        AutomataNode._node_number += 1

    def accept(self, symbol: str, traversal: AutomataTraversal) -> None:
        pass

    def __repr__(self) -> str:
        return self.name


AutomataNodePath = Tuple[AutomataNode, ...]


class ConcatAutomataNode(AutomataNode):
    def accept(self, symbol: str, traversal: AutomataTraversal) -> None:
        traversal.user_input += symbol
        if traversal.recorded_variable:
            traversal.variables[traversal.recorded_variable] += symbol


class StartRecordingVariableAutomataNode(AutomataNode):
    def __init__(self, variable: str) -> None:
        super().__init__()
        self.variable = variable

    def accept(self, symbol: str, traversal: AutomataTraversal) -> None:
        traversal.recorded_variable = self.variable


class StopRecordingVariableAutomataNode(AutomataNode):
    def __init__(self, postprocessor: Callable) -> None:
        super().__init__()
        self.postprocessor = postprocessor

    def accept(self, symbol: str, traversal: AutomataTraversal) -> None:
        assert traversal.recorded_variable
        traversal.variables[traversal.recorded_variable] = self.postprocessor(
            traversal.variables[traversal.recorded_variable])
        traversal.recorded_variable = None


class ExecuteCommandAutomataNode(AutomataNode):
    def __init__(self, command: Callable) -> None:
        super().__init__()
        self.command = command

    def accept(self, symbol: str, traversal: AutomataTraversal) -> None:
        self.command(**traversal.variables)
        raise StopIteration()


class Automata:
    def __init__(self) -> None:
        self.delta = defaultdict(set)  # type: Dict[Tuple[AutomataNode, str], Set[AutomataNode]]
        self.init_node = AutomataNode()  # type: AutomataNode

    ''' Returns paths starting at `node` that consume `symbol`. '''
    def traverse(
            self,
            parent_traversal: AutomataTraversal,
            node: AutomataNode,
            symbol: str) -> Iterator[AutomataTraversal]:
        for path1 in self.epsilon_closure(node):
            for node2 in self.delta[path1[-1], symbol]:
                for path2 in self.epsilon_closure(node2):
                    new_traversal = AutomataTraversal(
                        parent_traversal.nodes + path1[1:] + path2,
                        parent_traversal)
                    for node in path1[1:]:
                        node.accept('', new_traversal)
                    path2[0].accept(symbol, new_traversal)
                    for node in path2[1:]:
                        node.accept('', new_traversal)
                    yield new_traversal

    def epsilon_closure(self, node: AutomataNode) -> Set[AutomataNodePath]:
        stack = [(node, (node,))]  # type: List[Tuple[AutomataNode, AutomataNodePath]]
        paths = set()  # type: Set[AutomataNodePath]
        while stack:
            (node, path) = stack.pop()
            if path not in paths:
                paths.add(path)
                for neighbor_node in self.delta[node, '']:
                    new_path = path + (neighbor_node,)
                    stack.append((neighbor_node, new_path))
        return paths

    def connect(
            self,
            node1: AutomataNode,
            node2: AutomataNode,
            symbol: str) -> None:
        self.delta[node1, symbol].add(node2)

    def dump(self) -> str:
        lines = []  # type: List[str]
        for node1, symbol in self.delta.keys():
            for node2 in self.delta[node1, symbol]:
                lines.append('%s -> %s [label=%s]' % (
                    node1.name,
                    node2.name,
                    symbol or '\N{GREEK SMALL LETTER EPSILON}',
                ))
        lines = list(sorted(lines))
        lines.insert(0, 'digraph {')
        lines.append('}')
        return '\n'.join(lines)


class AutomataTraverser:
    def __init__(self, automata: Automata) -> None:
        self._automata = automata
        self._current_traversals = self._get_neutral_traversals()

    def consume(self, symbol: str) -> None:
        target_traversals = self._get_neutral_traversals()
        try:
            for traversal in self._current_traversals:
                for new_traversal in self._automata.traverse(
                        traversal, traversal.nodes[-1], symbol):
                    target_traversals.append(new_traversal)
            self._current_traversals = target_traversals
        except StopIteration:
            self._current_traversals = self._get_neutral_traversals()

    def _get_neutral_traversals(self) -> List[AutomataTraversal]:
        return [AutomataTraversal((self._automata.init_node,))]


class InputToken:
    def extend_automata(
            self,
            _automata: Automata,
            prev_node: AutomataNode) -> AutomataNode:
        raise NotImplementedError()


class StaticInputToken(InputToken):
    def __init__(self, char: str) -> None:
        self.char = char

    def extend_automata(
            self,
            automata: Automata,
            prev_node: AutomataNode) -> AutomataNode:
        next_node = ConcatAutomataNode()
        automata.connect(prev_node, next_node, self.char)
        return next_node


class NumberInputToken(InputToken):
    def __init__(self, var_name: str) -> None:
        self.var_name = var_name

    def extend_automata(
            self,
            automata: Automata,
            prev_node: AutomataNode) -> AutomataNode:

        def postprocess(var: str) -> int:
            if var.startswith('0x'):
                return int(var, 16)
            return int(var)

        start_node = StartRecordingVariableAutomataNode(self.var_name)
        stop_node = StopRecordingVariableAutomataNode(postprocess)

        automata.connect(prev_node, start_node, '')

        decimal_node = ConcatAutomataNode()
        for num in list('123456789'):
            automata.connect(start_node, decimal_node, num)
        for num in list('0123456789'):
            automata.connect(decimal_node, decimal_node, num)
        automata.connect(decimal_node, stop_node, '')

        hex_node1 = ConcatAutomataNode()
        hex_node2 = ConcatAutomataNode()
        hex_node3 = ConcatAutomataNode()
        automata.connect(start_node, hex_node1, '0')
        for num in list('123456789'):
            automata.connect(hex_node1, decimal_node, num)
        automata.connect(hex_node1, hex_node2, 'x')
        automata.connect(hex_node1, stop_node, '')
        for num in list('0123456789ABCDEFabcdef'):
            automata.connect(hex_node2, hex_node3, num)
            automata.connect(hex_node3, hex_node3, num)
        automata.connect(hex_node3, stop_node, '')

        return stop_node


def tokenize(text: str) -> List[InputToken]:
    i = 0
    tokens = []  # type: List[InputToken]

    while i < len(text):
        if text[i] == '\\':
            if i + 1 == len(text):
                raise ValueError(MISSING_BACKSLASH)
            tokens.append(StaticInputToken(text[i + 1]))
            i += 2

        elif text[i] == '<':
            nesting = 1
            i += 1
            text_in_braces = ''
            while nesting != 0:
                if i == len(text):
                    raise ValueError(MISSING_CLOSING_BRACE)

                if text[i] == '<':
                    nesting += 1
                    i += 1

                elif text[i] == '>':
                    nesting -= 1
                    i += 1

                elif nesting >= 1:
                    if text[i] == '\\':
                        if i + 1 == len(text):
                            raise ValueError(MISSING_BACKSLASH)
                        text_in_braces += text[i + 1]
                        i += 2
                    else:
                        text_in_braces += text[i]
                        i += 1

            var_name, var_type = text_in_braces.split(':')
            if var_type == 'number':
                tokens.append(NumberInputToken(var_name))
            else:
                raise ValueError(UNKNOWN_VARIABLE_TYPE % var_type)

        else:
            tokens.append(StaticInputToken(text[i]))
            i += 1

    return tokens


class BindingList:
    def __init__(self) -> None:
        self._automata = Automata()
        self._traverser = AutomataTraverser(self._automata)

    def bind(self, sequence: str, command: Callable) -> None:
        node = self._automata.init_node
        for token in tokenize(sequence):
            node = token.extend_automata(self._automata, node)
        final_node = ExecuteCommandAutomataNode(command)
        self._automata.connect(node, final_node, '')
        self._traverser = AutomataTraverser(self._automata)

    def accept_char(self, input_char: str) -> None:
        self._traverser.consume(input_char)


binding_list = BindingList()
