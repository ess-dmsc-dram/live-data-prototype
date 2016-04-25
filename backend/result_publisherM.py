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
	self.ports = None

    def run(self):
	pass

    def connect(self):
	context = zmq.Context()
	self.socket = context.socket(zmq.PUB)
	uri = 'tcp://*:{0:d}'.format(self.ports)
	self.socket.bind(uri)
	log.info('Bound to ' + uri)

    def _create_header(self,command,index):
	return {'command':command, 'index':index}

    def _publish_clear(self):
	header = self._create_header('clear', None)
	self.socket.send_json(header)

    def _publish(self, index):
	pass

    def get_parameter_dict(self):
	return {'update_rate':'float'}

    @property
    def update_rate(self):
        return self._update_rate

    @update_rate.setter
    def update_rate(self, update_rate):
        self._update_rate = update_rate    
