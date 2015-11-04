import zmq
import sys

HOST = 'localhost'
PORT = 10002

def connect_zmq():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://%s:%s" % (HOST, PORT))
    return socket

socket = connect_zmq()

def set(arg, value):
    socket.send_json({'version':1, 'request_type':'control','payload':'send_parameters'})
    reply = socket.recv_json()
    print reply
    socket.send_json({'version':1, 'request_type':'get_values','payload':reply['payload']})
    reply = socket.recv_json()
    print reply

    arg_type = type(reply['payload']['BraggPeakEventGenerator'][arg])

    socket.send_json({'version':1, 'request_type':'set_parameters','payload':{'BraggPeakEventGenerator':{arg:arg_type(value)}}})
    status = socket.recv()
    print status

arg = sys.argv[1]
value = sys.argv[2]
set(arg, value)
