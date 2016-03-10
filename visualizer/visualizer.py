from collections import deque
import zmq

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
import numpy

from logger import log


class Plotter(object):
    def __init__(self, dataListener):
        self.dataListener = dataListener
        self.win = pg.GraphicsWindow()
        self.win.resize(800,350)
        self.win.setWindowTitle('pyqtgraph example: Histogram')
        self.plt1 = self.win.addPlot()
        self.curves = {}

    def clear(self):
        self.curves = {}
        self.plt1.clear()

    def update(self):
        while self.dataListener.data:
            index,x,y = self.dataListener.data.popleft()
            if not index in self.curves:
                self.curves[index] = self.plt1.plot(stepMode=True, pen=(index), name=str(index))
            self.curves[index].setData(x, y)
        self.plt1.enableAutoRange('xy', False)


class DataListener(QtCore.QObject):
    clear = QtCore.pyqtSignal()
    new_data = QtCore.pyqtSignal()

    def __init__(self, host, port):
        QtCore.QObject.__init__(self)
        self.data = deque()
        self._host = host
        self._port = port

    def run(self):
        log.info('Starting DataListener...')
        self.connect()
        while True:
            command, index = self._receive_header()
            if command == 'data':
                x,y = self.get_histogram()
                self.data.append((index,x,y))
                self.new_data.emit()
            elif command == 'clear':
                self.clear.emit()

    def connect(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        uri = 'tcp://{0}:{1:d}'.format(self._host, self._port)
        self.socket.connect(uri)
        self.socket.setsockopt(zmq.SUBSCRIBE, '')
        log.info('Subscribed to result publisher at ' + uri)

    def get_histogram(self):
        data = numpy.frombuffer(self.socket.recv(), numpy.float64)
        x,y = numpy.array_split(data, 2)
        return x,y

    def _receive_header(self):
        header = self.socket.recv_json()
        command = header['command']
        index = header['index']
        return command, index
