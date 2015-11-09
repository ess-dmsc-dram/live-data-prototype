
class GeneralParameterController(object):
    def __init__(self, control_client):
        self._control_client = control_client

        self._parameter_type_cache = None
        self._update_parameter_type_cache()

    def set_parameter_value(self, controllee, parameter, value):
        command_payload = {controllee: {parameter: self._convert_to_cached_type(controllee, parameter, value)} }

        return self._control_client.send('set_parameters', command_payload)

    def print_available_parameters(self):
        if self._parameter_type_cache is not None:
            print 'Available parameters and types:'
            print '-------------------------------'

            for controllee in self._parameter_type_cache.keys():
                print 'Controllee:', controllee
                for parameter, type in self._parameter_type_cache[controllee].iteritems():
                    print '{}: {}'.format(parameter, repr(type))



    def _convert_to_cached_type(self, controllee, parameter, value):
        return self._parameter_type_cache[controllee][parameter](value)

    def _update_parameter_type_cache(self):
        values = self._get_values(self._get_parameters())

        self._parameter_type_cache = {
            controllee: {
                param_name: type(param_value) for param_name, param_value in values[controllee].iteritems()
                } for controllee in values.keys()
            }

    def _get_parameters(self):
        return self._control_client.send('control', 'send_parameters')['payload']

    def _get_values(self, parameters):
        return self._control_client.send('get_values', parameters)['payload']

