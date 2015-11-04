class Controllable(object):
    def __init__(self, name):
        self._name = name

    def process_instruction(self, instruction, argument):
        setattr(self, instruction, argument)

    def get_parameter_dict(self):
        return {}

    @property
    def name(self):
        return self._name
