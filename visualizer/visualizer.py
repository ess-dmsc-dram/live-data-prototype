from collections import deque
import zmq
import sys
import numpy
import PyQt4
import mantid.simpleapi as simpleapi
import mantidqtpython as mpy
import random
from logger import log
ConfigService = simpleapi.ConfigService


class InstrumentView(object):
    def __init__(self, dataListener):
        self.dataListener = dataListener
	ws = simpleapi.CreateSimulationWorkspace(Instrument='data/POWDIFF_Definition.xml', BinParams='1,0.5,2')
	self._number_of_spectra = ws.getNumberHistograms()
	ws = simpleapi.WorkspaceFactory.Instance().create("Workspace2D", self._number_of_spectra, 2, 1)
	simpleapi.AnalysisDataService.Instance().addOrReplace('POWDIFF_test', ws)
	simpleapi.LoadInstrument(Workspace=ws, Filename='data/POWDIFF_Definition.xml', RewriteSpectraMap=True)
	ws = simpleapi.Rebin(ws, "0,1,2")
	simpleapi.AnalysisDataService.Instance().addOrReplace('POWDIFF_test', ws)
	#simpleapi.AnalysisDataService['POWDIFF_test']
	#simpleapi.AnalysisDataService.Instance().addOrReplace('POWDIFF_test', ws)
	
        #ws =  simpleapi.AnalysisDataService['POWDIFF_test']
        #simpleapi.LoadInstrument(Workspace=ws, Filename='data/POWDIFF_Definition.xml', RewriteSpectraMap=True)
        #ws.getAxis(0).setUnit('tof')
	
	#ws.setX(1,numpy.array([0,1]))
	#ws.setY(1,numpy.array([1]))
	#ws.setE(1,numpy.array([1]))
	InstrumentWidget = mpy.MantidQt.MantidWidgets.InstrumentWidget
        self.iw = InstrumentWidget('POWDIFF_test')
        self.iw.show()

    def clear(self):
        self.curves = {}
	#TODO

    def updateInstrumentView(self):
	#pass
	ws = simpleapi.AnalysisDataService['POWDIFF_test']
	
        while self.dataListener.data:
            index, x, y, e = self.dataListener.data.popleft()
	    #ws.dataY(index)[1] = y
	    ws.dataY(index)[1] = random.randint(1,5)
	    	
class DataListener(PyQt4.QtCore.QObject):
    clear = PyQt4.QtCore.pyqtSignal()
    new_data = PyQt4.QtCore.pyqtSignal()

    def __init__(self, host, port):
        PyQt4.QtCore.QObject.__init__(self)
        self.data = deque()
        self._host = host
        self._port = port

    def run(self):
        log.info('Starting DataListener...')
        self.connect()
        while True:
            command, index = self._receive_header()
            if command == 'data':
                x,y,e = self.get_histogram()
                self.data.append((index,x,y,e))
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
        x, y, e = numpy.array_split(data, 3)
        return x, y, e

    def _receive_header(self):
        header = self.socket.recv_json()
        command = header['command']
        index = header['index']
        return command, index
