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
        self.bin_boundaries = None
        self.bin_values = None
        self.resultLock = threading.Lock()
        self.context = None
        self.socket = None

    def run(self):
        print 'Starting EventListener...'
        self.connect()
        while True:
            data = self.get_data_from_stream()
            split_data = self.distribute_stream(data)
            processed_data = self.process_data(split_data)
            gathered_data = self.gather_data(processed_data)
            self.update_result(gathered_data)
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
            header = self.socket.recv_json()
            event_count = header['event_count']
            data = self.socket.recv()
            return numpy.frombuffer(data, numpy.float64).reshape((event_count, 2))
        else:
            return None

    def distribute_stream(self, data):
        if comm.Get_rank() == 0:
            split = []
            for i in range(comm.size):
                split.append([])
            for i in data:
                detector_id = int(i[0])
                target = detector_id % comm.size
                split[target].append(i)
        else:
            split = None
        return comm.scatter(split, root=0)

    def process_data(self, data):
        # readX, readY
        return mantid_reduction.reduce(data)
        #self.mantid_data = numpy.concatenate((self.mantid_data[0], self.mantid_data[1]))

    def gather_data(self, data):
        rawdata = comm.gather(data[1], root=0)
        if comm.Get_rank() == 0:
            for i in range(1, len(rawdata)):
                rawdata[0] += rawdata[i]
            return data[0], rawdata[0]
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

    def update_result(self, data):
        if comm.Get_rank() == 0:
            self.resultLock.acquire()
            if self.bin_boundaries == None:
                self.bin_boundaries = numpy.array(data[0], copy=True)
                self.bin_values = numpy.array(data[1], copy=True)
                #self.result = [ numpy.array(x, copy=True) for x in data ]
            else:
                self.bin_values += data[1]
                #self.result[1] += data[1]
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
            while self.eventListener.bin_boundaries == None:
                self.eventListener.resultLock.release()
                time.sleep(1)
                self.eventListener.resultLock.acquire()
            packet = numpy.concatenate((self.eventListener.bin_boundaries, self.eventListener.bin_values))
            #packet = numpy.concatenate((self.eventListener.result[0], self.eventListener.result[1]))
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
eventListener.daemon = True
eventListener.start()

if comm.Get_rank() == 0:
    resultPublisher = ResultPublisher(eventListener)
    resultPublisher.daemon = True
    resultPublisher.start()
    parameterController = ParameterControlServer(port=ports.result_publisher_control, parameter_dict=resultPublisher.get_parameter_dict())
    parameterController.daemon = True
    parameterController.start()

while threading.active_count() > 0:
    time.sleep(0.1)
