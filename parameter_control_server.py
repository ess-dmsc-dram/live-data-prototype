import logging
import zmq


class ParameterControlServer(object):
    def __init__(self, controllees=[], host='*', port=10000, version=1):
        self._logger = logging.getLogger()
        self.host = host
        self.port = port
        self.set_controllees(controllees)
        self.version = version
        self.socket = None
        self._request_type_map = {}
        self._request_type_map['control'] = self.process_command
        self._request_type_map['get_values'] = self.process_get_values
        self._request_type_map['set_parameters'] = self.process_set_parameters
        self._request_type_map['trigger_actions'] = self.process_trigger_actions

    def add_controllee(self, controllee):
        name = controllee.name
        if name in self._controllees:
            raise RuntimeError('Duplicate controllee name {}'.format(name))
        self._verify_controllee_attributes(controllee)
        self._controllees[name] = controllee

    def add_controllees(self, controllees):
        for c in controllees:
            self.add_controllee(c)

    def set_controllees(self, controllees):
        self._controllees = {}
        self.add_controllees(controllees)

    def run(self):
        self._logger.info('Starting ParameterControlServer...')
        self.connect()

        while True:
            packet = self.recv_packet()
            if self.check_version(packet):
                self.process_request(packet)

    def _verify_controllee_attributes(self, controllee):
        keys = controllee.get_parameter_dict().keys()
        for key in keys:
            value = getattr(controllee, key)
            if value is None:
                raise RuntimeError('Parameter "{}" in controllee {} is None. Needs to be initialized.'.format(key, controllee.name))

    def connect(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        uri = 'tcp://{0}:{1}'.format(self.host, self.port)
        self.socket.bind(uri)
        self._logger.info('Bound to ' + uri)

    def recv_packet(self):
        packet = self.socket.recv_json()
        self._logger.info('{}'.format(packet))
        return packet

    def send_parameters(self):
        self._reply('parameters', { key:value.get_parameter_dict() for key,value in self._controllees.iteritems() })

    def send_status(self, status):
        self._reply('status', status)

    def _reply(self, reply_type, payload):
        packet = {
                'version':self.version,
                'reply_type':reply_type,
                'payload':payload
                }
        self.socket.send_json(packet)

    def check_version(self, packet):
        version = packet['version']
        if version != self.version:
            self.send_status('Invalid packet version, got {0}, expected {1}.'.format(version, self.version))
            return False
        return True

    def process_request(self, packet):
        request_type = packet['request_type']
        payload = packet['payload']
        try:
            self._request_type_map[request_type](payload)
        except KeyError:
            self.send_status('Unknown request type {0}, ignoring.'.format(request_type))

    def process_command(self, command):
        if command == 'send_parameters':
            self.send_parameters()
        else:
            self.send_status('Unknown control command {0}, ignoring.'.format(command))

    def process_set_parameters(self, all_parameters):
        for controllee_name, parameters in all_parameters.iteritems():
            try:
                controllee = self._controllees[controllee_name]
                for key in parameters:
                    if hasattr(controllee, key):
                        try:
                            controllee.process_instruction(key, parameters[key])
                            self.send_status('Ok.')
                        except:
                            self.send_status('Internal error when setting value for key {0}, ignoring.'.format(key))
                    else:
                        self.send_status('Unknown key {0}, ignoring.'.format(key))
            except KeyError:
                self.send_status('Unknown controllee {0}, ignoring.'.format(controllee_name))

    def process_get_values(self, all_parameters):
        reply = {}
        for controllee_name, parameters in all_parameters.iteritems():
            try:
                reply[controllee_name] = {}
                controllee = self._controllees[controllee_name]
                for key in parameters:
                    if hasattr(controllee, key):
                        try:
                            tmp = getattr(controllee, key)
                            if not hasattr(tmp, '__call__'):
                                reply[controllee_name][key] = tmp
                        except:
                            pass
                    else:
                        pass
            except KeyError:
                pass
        self._reply('values', reply)

    def process_trigger_actions(self, all_parameters):
        for controllee_name, parameters in all_parameters.iteritems():
            try:
                controllee = self._controllees[controllee_name]
                for key in parameters:
                    if hasattr(controllee, key):
                        try:
                            controllee.process_trigger(key)
                            self.send_status('Ok.')
                        except:
                            self.send_status('Internal error when setting value for key {0}, ignoring.'.format(key))
                    else:
                        self.send_status('Unknown key {0}, ignoring.'.format(key))
            except KeyError:
                self.send_status('Unknown controllee {0}, ignoring.'.format(controllee_name))
