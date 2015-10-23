import threading
from collections import deque
import time
import zmq
import numpy

import ports
from parameter_control_server import ParameterControlServer
from event_generator import EventGenerator


class FakeEventStreamer(threading.Thread):
    def __init__(self, eventGenerator, version=1):
        threading.Thread.__init__(self)
        self.daemon = True
        self.version = version
        self.socket = None
        self.eventGenerator = eventGenerator

    def connect(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        uri = 'tcp://*:{0:d}'.format(ports.event_stream)
        self.socket.bind(uri)
        print 'Bound to ' + uri

    def send_stream_info(self):
        packet = {
                'type':'stream_info',
                'version':self.version,
                }
        self.socket.send_json(packet)

    def send_meta_data(self, meta_data):
        packet = {
                'type':'meta_data',
                'meta_data':meta_data
                }
        self.socket.send_json(packet)

    def send_event_data(self, pulse_id, event_data):
        header = {
                'type':'event_data',
                'event_count':len(event_data),
                'pulse_id':pulse_id
                }
        self.socket.send_json(header, flags=zmq.SNDMORE)
        self.socket.send(event_data)

    def run(self):
        print 'Starting FakeEventStreamer...'
        self.connect()

        while True:
            command = self.socket.recv()
            if command == 'h':
                print 'Client requested header'
                x = numpy.hstack([numpy.random.normal(size=1), numpy.random.normal(size=1, loc=4)])
                self.socket.send_json(x.itemsize)
            elif command == 'd':
                event_data = self.eventGenerator.get_events()
                self.send_event_data(pulse_id=0, event_data=event_data)
            else:
                print 'Unknown command ' + command


class MetaDataGenerator(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.meta_data = None
        # support two types:
        # - based on timer (every N seconds)
        # - based on change

    def run(self):
        print 'Starting MetaDataGenerator...'

eventGenerator = EventGenerator()
eventGenerator.start()

streamer = FakeEventStreamer(eventGenerator)
streamer.start()

parameterController = ParameterControlServer(port=ports.streamer_control, parameter_dict=eventGenerator.get_parameter_dict())
parameterController.start()

while threading.active_count() > 0:
    time.sleep(0.1)
