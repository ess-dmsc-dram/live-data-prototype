import time
import numpy
import zmq

from logger import log
import ports
from controllable import Controllable


class ResultPublisher(Controllable):
    def __init__(self, eventListener):
        super(ResultPublisher, self).__init__(type(self).__name__)
        self.eventListener = eventListener
        self._update_rate = 1.0
        self.socket = None
        self._last_count = 0

    def run(self):
        log.info("Starting ResultPublisher")
        self.connect()
	self._publish_clear()
        while True:
	    if len(self.eventListener.transition_objects_dict['GatherHistogram']) >=1:
                for gather_histogram_transition in self.eventListener.transition_objects_dict['GatherHistogram']:
		    count = len(gather_histogram_transition.get_checkpoint())
            	    if count != self._last_count:
                    	self._publish_clear()
                	self._last_count = count
            	    for i in range(count):
                	if gather_histogram_transition.get_checkpoint()[i]:
                    	    self._publish(i, gather_histogram_transition)
            	    time.sleep(self.update_rate)

    def connect(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        uri = 'tcp://*:{0:d}'.format(ports.result_stream)
        self.socket.bind(uri)
        log.info('Bound to ' + uri)

    def _create_header(self, command, index):
        return { 'command':command, 'index':index }

    def _publish_clear(self):
        header = self._create_header('clear', None)
        self.socket.send_json(header)

    def _publish(self, index, gather_histogram_transition):
        boundaries, values = gather_histogram_transition.get_checkpoint()[index].data
        packet = numpy.concatenate((boundaries, values))
        header = self._create_header('data', index)
        self.socket.send_json(header, flags=zmq.SNDMORE)
        self.socket.send(packet)

    def get_parameter_dict(self):
        return {'update_rate':'float'}

    @property
    def update_rate(self):
        return self._update_rate

    @update_rate.setter
    def update_rate(self, update_rate):
        self._update_rate = update_rate
