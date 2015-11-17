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
        final_class_name = clsname
        if final_class_name != 'ControllableDecorator':
            final_class_name += str(cls._type)
            cls._type += 1

        print clsname, final_class_name

        return type.__new__(cls, final_class_name, bases, attr)

    def __init__(cls, clsname, bases, attr):
        print cls, clsname
        type.__init__(cls, clsname, bases, attr)


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
    def __init__(self, decorated_controllable, prefix='Decorated'):
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
                setattr(type(self),
                        attribute_name,
                        ForwardingProperty(self._decorated_controllable, attribute_name))

    def get_parameter_dict(self):
        total_parameter_dict = self._base_properties.copy()
        total_parameter_dict.update(self._get_decorator_parameter_dict())
        return total_parameter_dict


def make_decorator(cls, decorated_controllable):
    newType = ControllableDecoratorMetaClass(cls.__name__, (cls,), {})

    return newType(decorated_controllable)



if __name__ == '__main__':
    class Yeah(Controllable):
        def __init__(self):
            super(Yeah, self).__init__(type(self).__name__)

            self._lol = 'LOL'
            self._rofl = 'ROFL'

        def get_parameter_dict(self):
            return {'lol': 'str', 'rofl': 'str', 'trigger': 'None'}

        def trigger(self):
            print 'Yeah yeah.'

        @property
        def lol(self):
            return self._lol

        @lol.setter
        def lol(self, new_lol):
            self._lol = new_lol

        @property
        def rofl(self):
            return self._rofl


    class Nope(Controllable):
        def __init__(self):
            super(Nope, self).__init__(type(self).__name__)

        def get_parameter_dict(self):
            return {'nope': 'None'}

        def nope(self):
            print 'Nope, nope, nope!'


    class Phrase(ControllableDecorator):
        def __init__(self, decorated_controllable):
            super(Phrase, self).__init__(decorated_controllable, 'Phrased')

            self._phrase = 'right'

        def _get_decorator_parameter_dict(self):
            return {'phrase': 'str'}

        @property
        def phrase(self):
            return self._phrase

        @phrase.setter
        def phrase(self, new_phrase):
            self._phrase = new_phrase

        def printCoolStuff(self):
            if hasattr(self._decorated_controllable, 'lol') and hasattr(self._decorated_controllable, 'rofl'):
                print self._decorated_controllable.lol + ' ' + self._decorated_controllable.rofl + ', ' + self.phrase + '?'


    yeah = Yeah()
    nope = Nope()
    dec = make_decorator(Phrase, yeah)

    print dec.name
    print dec.get_parameter_dict()
    dec.printCoolStuff()
    print dec.lol
    dec.lol = 'Test'
    print dec.lol
    dec.trigger()
    yeah.trigger()
    print yeah.lol
    dec.printCoolStuff()
    dec.phrase = 'eh'
    dec.printCoolStuff()

    dec2 = make_decorator(Phrase, nope)
    dec2.nope()
    print dec.__class__.__mro__
    print dec2.__class__.__mro__
