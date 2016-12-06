import time
import numpy
import zmq
import mantid.simpleapi as simpleapi
from logger import log
import ports
from controllable import Controllable


class SpectraViewPublisher(Controllable):
    def __init__(self, eventListener):
        super(SpectraViewPublisher, self).__init__(type(self).__name__)
        self.eventListener = eventListener
        self._update_rate = 1.0
        self.socket = None
        self._last_count = 0

    def run(self):
        log.info("Starting SpectraViewPublisher")
        self.connect()

        self._publish_clear()
        while True:
            if self.eventListener._create_workspace_from_events_transition.get_checkpoint():
                self._publish()
            time.sleep(self.update_rate)

    def connect(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        uri = 'tcp://*:{0:d}'.format(ports.spectra_result_stream)
        self.socket.bind(uri)
        log.info('Bound to ' + uri)

    def _create_header(self, command, index):
        return { 'command':command, 'index':index }

    def _publish_clear(self):
        header = self._create_header('clear', None)
        self.socket.send_json(header)

    def _publish(self):
	try:
	    x, y = self.eventListener._gather_spectra_transition.get_checkpoint().data
	except TypeError:
	    time.sleep(5)
	    x, y = self.eventListener._gather_spectra_transition.get_checkpoint().data 
	index =  self.eventListener._gather_spectra_transition._spectra_id
	packet = numpy.concatenate((x, y))
	header = self._create_header('spectraData', index)
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
