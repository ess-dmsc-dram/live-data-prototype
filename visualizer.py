from threading import Thread
from collections import deque
import struct
import zmq

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy

import ports

HOST = 'localhost'
PORT = ports.result_stream

def connect_zmq():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    #socket = context.socket(zmq.REQ)
    socket.connect("tcp://%s:%s" % (HOST, PORT))
    socket.setsockopt(zmq.SUBSCRIBE, '')
    return socket

socket = connect_zmq()

def request_header_zmq():
    socket.send('h')
    itemsize = socket.recv_json()
    #header = struct.unpack_from('i', buf)
    print itemsize

    if itemsize == 4:
    #if header[0] == 4:
        datatype = numpy.float32
    else:
        datatype = numpy.float64

    return datatype

datatype = numpy.float64
#datatype = request_header_zmq()

#def request_data_zmq():
#    socket.send('d')
#    data = numpy.frombuffer(socket.recv(), datatype)
#    return data

def request_data_zmq():
    data = numpy.frombuffer(socket.recv(), datatype)
    return data

def get_histogram():
    #data = request_data_socket()
    data = request_data_zmq()
    ## compute standard histogram
    y,x = numpy.histogram(data, bins=200) #, bins=numpy.linspace(-3, 8, 40))
    return y,x


class Plotter():
    def __init__(self, dataListener):
        self.dataListener = dataListener
        self.win = pg.GraphicsWindow()
        self.win.resize(800,350)
        self.win.setWindowTitle('pyqtgraph example: Histogram')
        self.plt1 = self.win.addPlot()
        self.curve = self.plt1.plot(stepMode=True, fillLevel=0, brush=(0,0,255,150))

    def update(self):
        while dataListener.data:
            x,y = dataListener.data.popleft()
            self.curve.setData(x, y)
        self.plt1.enableAutoRange('xy', False)




class DataListener(Thread, QtCore.QObject):
    new_data = QtCore.pyqtSignal()
    def __init__(self):
        Thread.__init__(self)
        QtCore.QObject.__init__(self)
        self.data = deque()
    def run(self):
        while True:
            x,y = numpy.array_split(numpy.frombuffer(socket.recv(), datatype), 2)
            print x
            print y
            print len(x), len(y)
            #y,x = get_histogram()
            self.data.append((x,y))
            self.new_data.emit()

#def update():
#    global curve, plt1
#    y,x = get_histogram()
#    curve.setData(x, y)
#    plt1.enableAutoRange('xy', False)


#timer = QtCore.QTimer()
#timer.timeout.connect(update)
#timer.start(1)

dataListener = DataListener()
dataListener.daemon = True
plotter = Plotter(dataListener)


dataListener.new_data.connect(plotter.update)
dataListener.start()


## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
