from backend_worker import BackendCommandPublisher
import threading

import time
import sys

import ports


publisher = BackendCommandPublisher(port=ports.rebin_control)


#def connect_zmq():
#    context = zmq.Context()
#    socket = context.socket(zmq.REQ)
#    socket.connect("tcp://%s:%s" % (HOST, PORT))
#    return socket
#
#socket = connect_zmq()

def set_bin_parameters():
    #socket.send_json({'version':1, 'request_type':'set_parameters','payload':{'bin_parameters':str(sys.argv[1])}})
    publisher.publish({'version':1, 'request_type':'set_parameters','payload':{'bin_parameters':str(sys.argv[1])}})
    #status = socket.recv()
    #print status

set_bin_parameters()

