import zmq


class ParameterControlServer(object):
    def __init__(self, controllees=[], host='*', port=10000, version=1):
        self.host = host
        self.port = port
        self.set_controllees(controllees)
        self.version = version
        self.socket = None

    def add_controllee(self, controllee):
        name = controllee.name
        if name in self._controllees:
            raise RuntimeError('Duplicate controllee name {}'.format(name))
        self._controllees[name] = controllee

    def add_controllees(self, controllees):
        for c in controllees:
            self.add_controllee(c)

    def set_controllees(self, controllees):
        self._controllees = {}
        self.add_controllees(controllees)

    def run(self):
        print 'Starting ParameterControlServer...'
        self.connect()

        while True:
            packet = self.recv_packet()
            if self.check_version(packet):
                self.process_request(packet)

    def connect(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        uri = 'tcp://{0}:{1}'.format(self.host, self.port)
        self.socket.bind(uri)
        print 'Bound to ' + uri

    def recv_packet(self):
        packet = self.socket.recv_json()
        print packet
        return packet

    def send_parameters(self):
        packet = {
                'version':self.version,
                'reply_type':'parameters',
                'payload':{ key:value.get_parameter_dict() for key,value in self._controllees.iteritems() }
                }
        self.socket.send_json(packet)

    def send_status(self, status):
        packet = {
                'version':self.version,
                'reply_type':'status',
                'payload':status
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
        if request_type == 'control':
            self.process_command(payload)
        elif request_type == 'set_parameters':
            self.process_parameters(payload)
        else:
            self.send_status('Unknown request type {0}, ignoring.'.format(request_type))

    def process_command(self, command):
        if command == 'send_parameters':
            self.send_parameters()
        else:
            self.send_status('Unknown control command {0}, ignoring.'.format(command))

    def process_parameters(self, all_parameters):
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
