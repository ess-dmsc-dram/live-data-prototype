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
            self.replace_result()
            #self.distribute_stream()
            #self.modify_data()
            #self.gather_data()
            #self.append_to_result()

    def connect(self):
        if comm.Get_rank() == 0:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.REQ)
            uri = 'tcp://localhost:{0:d}'.format(ports.event_stream)
            self.socket.connect(uri)
            print 'Connected to event streamer at ' + uri

    #def get_and_verify_stream_info(self):

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
            self.mantid_data = mantid_reduction.reduce(self.data)
            self.mantid_data = numpy.concatenate((self.mantid_data[0], self.mantid_data[1]))
            #print self.mantid_data
            #self.data = self.data.transpose()[1]
        else:
            self.data = None

    def distribute_stream(self):
        if comm.Get_rank() == 0:
            split = numpy.array_split(self.data, comm.size)
        else:
            split = None
        tmp2 = comm.scatter(split, root=0)
        self.data = numpy.frombuffer(tmp2, numpy.float64)

    def modify_data(self):
        self.data = numpy.add(self.data, 10.0 * comm.Get_rank())

    def gather_data(self):
        rawdata = comm.gather(self.data, root=0)
        if comm.Get_rank() == 0:
            self.data = numpy.concatenate([numpy.frombuffer(rawdata[i], numpy.float64) for i in range(comm.size)])

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
            self.result = self.mantid_data
            self.resultLock.release()

class ResultStreamer(threading.Thread):
    def __init__(self, eventListener):
        if comm.Get_rank() != 0:
            raise Exception('ResultStream can run only on rank 0')
        threading.Thread.__init__(self)
        self.eventListener = eventListener

    def run(self):
        print "Starting ResultStreamer"
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://*:{0:d}".format(ports.result_stream))

        while 1:
            command = socket.recv()
            if command == 'h':
                print 'Client requested header'
                eventListener.resultLock.acquire()
                while eventListener.result == None:
                    eventListener.resultLock.release()
                    time.sleep(1)
                    eventListener.resultLock.acquire()
                socket.send_json(eventListener.result.itemsize)
                eventListener.resultLock.release()
            elif command == 'd':
                print 'Client requested data'
                eventListener.resultLock.acquire()
                while eventListener.result == None:
                    eventListener.resultLock.release()
                    time.sleep(1)
                    eventListener.resultLock.acquire()
                print eventListener.result.size
                socket.send(eventListener.result)
                # TODO is it safe to clear/release here? When is zmq done using the buffer?
                eventListener.result = None
                eventListener.resultLock.release()
            else:
                print 'Unknown command ' + command

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
            #print self.eventListener.result.size
            self.socket.send(self.eventListener.result)
            # TODO is it safe to clear/release here? When is zmq done using the buffer?
            self.eventListener.result = None
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
    #resultStreamer = ResultStreamer(eventListener)
    #resultStreamer.start()
    resultPublisher = ResultPublisher(eventListener)
    resultPublisher.start()
    parameterController = ParameterControlServer(port=ports.result_publisher_control, parameter_dict=resultPublisher.get_parameter_dict())
    parameterController.start()

