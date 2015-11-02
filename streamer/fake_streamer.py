import threading
import time
import zmq

import ports
from parameter_control_server import ParameterControlServer
from event_generator import EventGenerator

from distribution_file_based_event_generator import DistributionFileBasedEventGenerator
from bragg_peak_event_generator import create_BraggEventGenerator
from bragg_peak_event_generator import CrystalStructure


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
                'record_type':self.eventGenerator.get_type_info()
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
                self.send_stream_info()
            elif command == 'd':
                event_data = self.eventGenerator.get_events()
                self.send_event_data(pulse_id=0, event_data=event_data)
            else:
                print 'Unknown command ' + command
