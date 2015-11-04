class Controllable(object):
    def __init__(self, name):
        self._name = name

    def process_instruction(self, instruction, argument):
        setattr(self, instruction, argument)

    @property
    def name(self):
        return self._name
