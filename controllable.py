class Controllable(object):
    def __init__(self, name):
        self._name = name

    def process_instruction(self, instruction, argument):
        setattr(self, instruction, argument)

    def process_trigger(self, instruction):
        getattr(self, instruction)()

    def get_parameter_dict(self):
        return {}

    @property
    def name(self):
        return self._name

# Meta class for ControllableDectorator. Each time a ControllableDecorator-subclass is instantiated, a new class
# type is created, which is then actually instantiated. Using this method, the decorated attributes can be forwarded
# properly (properties can not be added to an object, only to a type, but since the properties of one decorated object
# should not end up in ALL ControllableDecorator instances, a class per instance seems one way to go).
class ControllableDecoratorMetaClass(type):
    _type = 0

    def __new__(cls, clsname, bases, attr):
        cls._type += 1
        return type.__new__(cls, clsname + str(cls._type), bases, attr)

# Property-like class that invokes getattr/setattr in target using name
class ForwardingProperty(object):
    def __init__(self, target, name):
        self._target = target
        self._name = name

    def __get__(self, instance, owner):
        return getattr(self._target, self._name)

    def __set__(self, instance, value):
        setattr(self._target, self._name, value)

class ControllableDecorator(Controllable):
    __metaclass__ = ControllableDecoratorMetaClass

    def __init__(self, decorated_controllable, prefix=''):
        super(ControllableDecorator, self).__init__(prefix + decorated_controllable.name)

        self._decorated_controllable = decorated_controllable
        self._base_properties = self._decorated_controllable.get_parameter_dict()

        self._generate_decorated_properties()

    def _generate_decorated_properties(self):
        for attribute_name in self._base_properties.keys():
            attribute = getattr(self._decorated_controllable, attribute_name)

            if hasattr(attribute, '__call__'):
                setattr(type(self), attribute_name, attribute)
            else:
                setattr(type(self), attribute_name, ForwardingProperty(self._decorated_controllable, attribute_name))

    def get_parameter_dict(self):
        total_parameter_dict = self._base_properties.copy()
        total_parameter_dict.update(self._get_decorator_parameter_dict())
        return total_parameter_dict

