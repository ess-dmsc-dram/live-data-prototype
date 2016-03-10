import time
import numpy
import zmq

from logger import log
import ports
from controllable import Controllable


class InstrumentViewPublisher(Controllable):
    def __init__(self, eventListener):
        super(InstrumentViewPublisher, self).__init__(type(self).__name__)
        self.eventListener = eventListener
        self._update_rate = 1.0
        self.socket = None
        self._last_count = 0

    def run(self):
        log.info("Starting InstrumentViewPublisher")
        self.connect()

        self._publish_clear()
        while True:
            count = len(self.eventListener._rebin_for_instrumentview_transition.get_checkpoint())
            if count != self._last_count:
                self._publish_clear()
                self._last_count = count
            for i in range(count):
                if self.eventListener._rebin_for_instrumentview_transition.get_checkpoint()[i]:
                    self._publish(i)
            time.sleep(self.update_rate)

    def connect(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        uri = 'tcp://*:{0:d}'.format(ports.instrumentview_result_stream)
        self.socket.bind(uri)
        log.info('Bound to ' + uri)

    def _create_header(self, command, index):
        return { 'command':command, 'index':index }

    def _publish_clear(self):
        header = self._create_header('clear', None)
        self.socket.send_json(header)

    def _publish(self, index):
        #boundaries, values = self.eventListener._rebin_for_instrumentview_transition.get_checkpoint()[index].data
        #packet = numpy.concatenate((boundaries, values))
	#should want readX, readY, readE and spectrum num via getNumberofHistograms()
	currentws = self.eventListener._rebin_for_instrumentview_transition.get_checkpoint()[index].data
	for i in range(currentws.getNumberHistograms()):
            seriesX = currentws.readX(i)
	    seriesY = currentws.readY(i)
	    seriesE = currentws.readE(i)
	    packet = numpy.concatenate((seriesX, seriesY, seriesE))
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
