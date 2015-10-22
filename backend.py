import threading
import time
import numpy
import zmq
from mpi4py import MPI

import ports
import mantid_reduction
from parameter_control_server import ParameterControlServer

comm = MPI.COMM_WORLD

print 'Rank {0:3d} started.'.format(comm.Get_rank())


class EventListener(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.data = None
        self.result = None
        self.resultLock = threading.Lock()
        self.context = None
        self.socket = None

    def run(self):
        print 'Starting EventListener...'
        self.connect()
        while True:
            self.get_data_from_stream()
            self.distribute_stream()
            self.process_data()
            self.gather_data()
            self.replace_result()
            #self.append_to_result()

    def connect(self):
        if comm.Get_rank() == 0:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.REQ)
            uri = 'tcp://localhost:{0:d}'.format(ports.event_stream)
            self.socket.connect(uri)
            print 'Connected to event streamer at ' + uri

    def request_header(self):
        packet = {
                'version':self.version,
                'request_type':'parameters',
                'payload':None
                }
        self.socket.send('h')
        itemsize = self.socket.recv_json()

        if itemsize == 4:
            datatype = numpy.float32
        else:
            datatype = numpy.float64

        return datatype

    def get_data_from_stream(self):
        if comm.Get_rank() == 0:
            self.socket.send('d')
            self.data = self.socket.recv_json()
            event_count = self.data['event_count']
            self.data = self.socket.recv()
            self.data = numpy.frombuffer(self.data, numpy.float64).reshape((event_count, 2))
        else:
            self.data = None

    def distribute_stream(self):
        if comm.Get_rank() == 0:
            split = []
            for i in range(comm.size):
                split.append([])
            for i in self.data:
                detector_id = int(i[0])
                target = detector_id % comm.size
                split[target].append(i)
        else:
            split = None
        self.data = comm.scatter(split, root=0)

    def process_data(self):
        # readX, readY
        self.mantid_data = mantid_reduction.reduce(self.data)
        #self.mantid_data = numpy.concatenate((self.mantid_data[0], self.mantid_data[1]))

    def gather_data(self):
        rawdata = comm.gather(self.mantid_data[1], root=0)
        if comm.Get_rank() == 0:
            for i in range(1, len(rawdata)):
                rawdata[0] = numpy.add(rawdata[0], rawdata[i])
            self.mantid_data = [self.mantid_data[0], rawdata[0]]
            #self.mantid_data = numpy.concatenate((self.mantid_data[0], rawdata[0]))
            #self.mantid_data = numpy.concatenate([numpy.frombuffer(rawdata[i], numpy.float64) for i in range(comm.size)])

    def append_to_result(self):
        if comm.Get_rank() == 0:
            self.resultLock.acquire()
            if self.result == None:
                self.result = self.data
            else:
                self.result = numpy.append(self.result, self.data)
            self.resultLock.release()

    def replace_result(self):
        if comm.Get_rank() == 0:
            self.resultLock.acquire()
            if self.result == None:
                self.result = [ numpy.array(x, copy=True) for x in self.mantid_data ]
            else:
                self.result[1] += self.mantid_data[1]
                #self.result[1] = numpy.add(self.result[1], self.mantid_data[1])
            self.resultLock.release()


class ResultPublisher(threading.Thread):
    def __init__(self, eventListener):
        if comm.Get_rank() != 0:
            raise Exception('ResultPublisher can run only on rank 0')
        threading.Thread.__init__(self)
        self.eventListener = eventListener
        self.update_rate = 1.0
        self.socket = None

    def run(self):
        print "Starting ResultPublisher"
        self.connect()

        while True:
            self.eventListener.resultLock.acquire()
            while self.eventListener.result == None:
                self.eventListener.resultLock.release()
                time.sleep(1)
                self.eventListener.resultLock.acquire()
            packet = numpy.concatenate((self.eventListener.result[0], self.eventListener.result[1]))
            self.socket.send(packet)
            # TODO is it safe to clear/release here? When is zmq done using the buffer?
            #self.eventListener.result = None
            self.eventListener.resultLock.release()
            time.sleep(self.update_rate)

    def connect(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        uri = 'tcp://*:{0:d}'.format(ports.result_stream)
        self.socket.bind(uri)
        print 'Bound to ' + uri

    def get_parameter_dict(self):
        return {'update_rate':(self.set_update_rate, 'float')}

    def set_update_rate(self, update_rate):
        self.update_rate = update_rate



eventListener = EventListener()
eventListener.start()

if comm.Get_rank() == 0:
    resultPublisher = ResultPublisher(eventListener)
    resultPublisher.start()
    parameterController = ParameterControlServer(port=ports.result_publisher_control, parameter_dict=resultPublisher.get_parameter_dict())
    parameterController.start()
