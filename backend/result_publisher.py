import time
import numpy
import zmq

import ports
from controllable import Controllable


class ResultPublisher(Controllable):
    def __init__(self, eventListener):
        super(ResultPublisher, self).__init__(type(self).__name__)
        self.eventListener = eventListener
        self._update_rate = 1.0
        self.socket = None
        self._publish_historical_data = False

    def run(self):
        print "Starting ResultPublisher"
        self.connect()

        while True:
            if self._publish_historical_data:
                self._publish_history()
            while self.eventListener._gather_histogram_transition.get_checkpoint()[-1].data == None:
                time.sleep(1)
            boundaries, values = self.eventListener._gather_histogram_transition.get_checkpoint()[-1].data
            packet = numpy.concatenate((boundaries, values))
            self.socket.send_json(len(self.eventListener._gather_histogram_transition.get_checkpoint())-1, flags=zmq.SNDMORE)
            self.socket.send(packet)
            # TODO is it safe to clear/release here? When is zmq done using the buffer?
            #self.eventListener.result = None
            time.sleep(self.update_rate)

    def connect(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        uri = 'tcp://*:{0:d}'.format(ports.result_stream)
        self.socket.bind(uri)
        print 'Bound to ' + uri

    def _publish_history(self):
        self._publish_historical_data = False
        for i in range(len(self.eventListener.result_indices)-1):
            if self.eventListener.bin_boundaries[i] is not None:
                packet = numpy.concatenate((self.eventListener.bin_boundaries[i], self.eventListener.bin_values[i]))
                self.socket.send_json(self.eventListener.result_indices[i], flags=zmq.SNDMORE)
                self.socket.send(packet)

    def get_parameter_dict(self):
        return {'update_rate':'float', 'publish_historical_data':'trigger'}

    @property
    def update_rate(self):
        return self._update_rate

    @update_rate.setter
    def update_rate(self, update_rate):
        self._update_rate = update_rate

    def publish_historical_data(self):
        self._publish_historical_data = True
