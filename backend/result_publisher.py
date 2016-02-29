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
	self._portList = ports.result_stream
	self._portDict = {}
	self._socketDict = {} 
	self.default_port = self._portList[0]
	self.histogramNum = 0
    
    def run(self):
        log.info("Starting ResultPublisher")
        while True:
	    if len(self.eventListener.transition_objects_dict['GatherHistogram']) >=1:
		for gather_histogram_transition in self.eventListener.transition_objects_dict['GatherHistogram']:
	     	    if self.default_port not in self._portDict.values():
			self._portDict[gather_histogram_transition] = self.default_port
			self.new_connection(self.default_port, gather_histogram_transition)
		    else: 
			if self._portDict.get(gather_histogram_transition) == None:
			    for port in self._portList:
				if port not in self._portDict.values():
				    self._portDict[gather_histogram_transition] = port
				    log.info( "Adding " + gather_histogram_transition.get_name() + " to port " + str(port))
				    self.new_connection(port, gather_histogram_transition)
				    break
		    count = len(gather_histogram_transition.get_checkpoint())
            	    if count != self._last_count:
                    	self._publish_clear(gather_histogram_transition)
                	self._last_count = count
            	    for i in range(count):
                	if gather_histogram_transition.get_checkpoint()[i]:
                    	    self._publish(i, gather_histogram_transition)
            	    time.sleep(self.update_rate)
	   if histogramNum != len(self.eventListener.transition_objects_dict['GatherHistogram']):
	   	self.compare_dicts_update_ports()
		histogramNum = len(self.eventListener.transition_objects_dict['GatherHistogram'])

    def compare_dicts_update_ports(self):
	new_port_dic = {}
	for transitions in self.eventListener.transition_objects_dict['GatherHistogram']:
	    if transitions in self._portDict.keys():
		new_port_dic[transitions] = self._portDict[transitions]
	self._portDict = new_port_dic

	new_socket_dic = {}
	for sockets in self._socketDict.keys():
	    if sockets in self._portDict.keys():
		new_socket_dic[sockets] = self._socketDict[sockets]	
	self._socketDict = new_socket_dic	


    def new_connection(self, port, gather_histogram_transition):
	context = zmq.Context()
	self.socket = context.socket(zmq.PUB)
	uri = 'tcp://*:{0:d}'.format(port)
	self.socket.bind(uri)
	self._socketDict[gather_histogram_transition] = self.socket
	log.info('Bound to ' + uri + ", for: " + gather_histogram_transition.get_name())

    def _create_header(self, command, index):
        return { 'command':command, 'index':index }

    def _publish_clear(self, gather_histogram_transition):
        header = self._create_header('clear', None)
	socket = self._socketDict[gather_histogram_transition]
        socket.send_json(header)

    def _publish(self, index, gather_histogram_transition):
	socket = self._socketDict[gather_histogram_transition]
        boundaries, values = gather_histogram_transition.get_checkpoint()[index].data
        packet = numpy.concatenate((boundaries, values))
        header = self._create_header('data', index)
        socket.send_json(header, flags=zmq.SNDMORE)
        socket.send(packet)

    def get_parameter_dict(self):
        return {'update_rate':'float'}

    @property
    def update_rate(self):
        return self._update_rate

    @update_rate.setter
    def update_rate(self, update_rate):
        self._update_rate = update_rate
