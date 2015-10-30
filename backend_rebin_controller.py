from backend_worker import BackendCommandPublisher
import threading

import time
import sys

import ports


publisher = BackendCommandPublisher(num_clients=int(sys.argv[1]), port=ports.rebin_control)

time.sleep(0.5)

#def connect_zmq():
#    context = zmq.Context()
#    socket = context.socket(zmq.REQ)
#    socket.connect("tcp://%s:%s" % (HOST, PORT))
#    return socket
#
#socket = connect_zmq()

def set_bin_parameters(params):
    #socket.send_json({'version':1, 'request_type':'set_parameters','payload':{'bin_parameters':str(sys.argv[1])}})
    publisher.publish({'version':1, 'request_type':'set_parameters','payload':{'bin_parameters':str(params)}})
    #status = socket.recv()
    #print status

while True:
    params=str(raw_input('Rebin parameters: '))
    set_bin_parameters(params)

