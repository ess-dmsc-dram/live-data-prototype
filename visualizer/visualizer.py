from collections import deque
import zmq

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
import numpy


class Plotter(object):
    def __init__(self, dataListener):
        self.dataListener = dataListener
        self.win = pg.GraphicsWindow()
        self.win.resize(800,350)
        self.win.setWindowTitle('pyqtgraph example: Histogram')
        self.plt1 = self.win.addPlot()
        self.plt1.addLegend()
        self.curves = {}

    def update(self):
        while self.dataListener.data:
            index,x,y = self.dataListener.data.popleft()
            if not index in self.curves:
                self.curves[index] = self.plt1.plot(stepMode=True, pen=(index), name=str(index))
            self.curves[index].setData(x, y)
        self.plt1.enableAutoRange('xy', False)


class DataListener(QtCore.QObject):
    new_data = QtCore.pyqtSignal()

    def __init__(self, host, port):
        QtCore.QObject.__init__(self)
        self.data = deque()
        self._host = host
        self._port = port

    def run(self):
        print 'Starting DataListener...'
        self.connect()
        while True:
            index,x,y = self.get_histogram()
            self.data.append((index,x,y))
            self.new_data.emit()

    def connect(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        uri = 'tcp://{0}:{1:d}'.format(self._host, self._port)
        self.socket.connect(uri)
        self.socket.setsockopt(zmq.SUBSCRIBE, '')
        print 'Substribed to result publisher at ' + uri

    def get_histogram(self):
        index = self.socket.recv_json()
        data = numpy.frombuffer(self.socket.recv(), numpy.float64)
        x,y = numpy.array_split(data, 2)
        return index,x,y
