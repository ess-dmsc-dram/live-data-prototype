from threading import Thread
from collections import deque
import zmq

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy

import ports
import command_line_parser


class Plotter(object):
    def __init__(self, dataListener):
        self.dataListener = dataListener
        self.win = pg.GraphicsWindow()
        self.win.resize(800,350)
        self.win.setWindowTitle('pyqtgraph example: Histogram')
        self.plt1 = self.win.addPlot()
        self.curve = self.plt1.plot(stepMode=True, fillLevel=0, brush=(0,0,255,150))

    def update(self):
        while self.dataListener.data:
            x,y = self.dataListener.data.popleft()
            self.curve.setData(x, y)
        self.plt1.enableAutoRange('xy', False)


class DataListener(Thread, QtCore.QObject):
    new_data = QtCore.pyqtSignal()

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        QtCore.QObject.__init__(self)
        self.data = deque()

    def run(self):
        print 'Starting DataListener...'
        self.connect()
        while True:
            x,y = self.get_histogram()
            self.data.append((x,y))
            self.new_data.emit()

    def connect(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        uri = 'tcp://{0}:{1:d}'.format(command_line_parser.get_host(), ports.result_stream)
        self.socket.connect(uri)
        self.socket.setsockopt(zmq.SUBSCRIBE, '')
        print 'Substribed to result publisher at ' + uri

    def get_histogram(self):
        data = numpy.frombuffer(self.socket.recv(), numpy.float64)
        x,y = numpy.array_split(data, 2)
        return x,y
