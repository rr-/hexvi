class BindingNode(object):
    def __init__(self):
        self.children = {}
        self.func = None

    def __repr__(self):
        return ('BindingNode('
            + repr(self.func) + ', '
            + repr(self.children) + ')')

class ArgumentBinding(object):
    def __init__(self, name, keys, postprocessor=lambda x: x, loop=False):
        self.name = name
        self.keys = keys
        self.postprocessor = postprocessor
        self.loop = loop

class BindingMixin(object):
    def __init__(self):
        arg_bindings = [
            ArgumentBinding(
                '<number>', list('0123456789'), lambda x: int(x), loop=True),
        ]
        self.__arg_bindings = {b.name: b for b in arg_bindings}
        self.__root = BindingNode()
        self.__current_node = self.__root
        self.__args = []
        self.__active_arg_binding = None
        self.bind(['esc'], self.__reset)

    def bind(self, path, func):
        node = self.__root
        for i in path:
            if i not in node.children:
                node.children[i] = BindingNode()
            node = node.children[i]
            if i[0] == '<':
                if i not in self.__arg_bindings:
                    raise RuntimeError('Unknown argument binding')
                if self.__arg_bindings[i].loop:
                    node.children[i] = node
        if node.func or node.children:
            raise RuntimeError('Ambiguous binding')
        node.func = func

    def keypress(self, pos, key):
        for b in self.__arg_bindings.values():
            if key not in b.keys or b.name not in self.__current_node.children:
                continue
            if self.__active_arg_binding != b:
                self.__finalize_arg()
                self.__args.append('')
                self.__active_arg_binding = b
            self.__args[len(self.__args) - 1] += key
            self.__current_node = self.__current_node.children[b.name]
            return

        self.__finalize_arg()

        if key not in self.__current_node.children:
            self.__reset()
            return key

        self.__current_node = self.__current_node.children[key]
        if self.__current_node.func:
            self.__current_node.func(*self.__args)
            self.__reset()

    def __finalize_arg(self):
        if not self.__active_arg_binding:
            return
        self.__args[len(self.__args) - 1] = (
            self.__active_arg_binding.postprocessor(
                self.__args[len(self.__args) - 1]))
        self.__active_arg_binding = None

    def __reset(self):
        self.__current_node = self.__root
        self.__args = []
        self.__active_arg_binding = False
