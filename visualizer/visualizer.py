from collections import deque
import zmq
import sys
import numpy
import PyQt4
import mantid.simpleapi as simpleapi
import mantidqtpython as mpy

from logger import log
ConfigService = simpleapi.ConfigService
#InstrumentWidget = mpy.MantidQt.MantidWidgets.InstrumentWidget
#app = PyQt4.QtGui.QApplication(sys.argv)


class InstrumentView(object):
    def __init__(self, dataListener):
        self.dataListener = dataListener
	print "reaches iv clas"
	ws = simpleapi.CreateSimulationWorkspace(Instrument='data/POWDIFF_Definition.xml', BinParams='1,0.5,2')
	self._number_of_spectra = ws.getNumberHistograms()
	ws = simpleapi.WorkspaceFactory.Instance().create("EventWorkspace", self._number_of_spectra, 1, 1)
	simpleapi.AnalysisDataService.Instance().addOrReplace('POWDIFF_test', ws)
        ws =  simpleapi.AnalysisDataService['POWDIFF_test']
        simpleapi.LoadInstrument(Workspace=ws, Filename='data/POWDIFF_Definition.xml', RewriteSpectraMap=True)
        ws.getAxis(0).setUnit('tof')
	print "after getAxis"
	
	InstrumentWidget = mpy.MantidQt.MantidWidgets.InstrumentWidget
        self.iw = InstrumentWidget("POWDIFF_test")
        self.iw.show()
	#app.exec_()

    def clear(self):
        self.curves = {}

    def updateInstrumentView(self):
	print "reaches update"
        while self.dataListener.data:
            index, x, y = self.dataListener.data.popleft()
	    
           # ws = WorkspaceFactory.Instance().create("EventWorkspace", self._number_of_spectra, 1, 1);
           # AnalysisDataService.Instance().addOrReplace('POWDIFF_test', ws)
           # ws =  AnalysisDataService['POWDIFF_test']
           # simpleapi.LoadInstrument(Workspace=ws, Filename='data/POWDIFF_Definition.xml', RewriteSpectraMap=True)
           # ws.getAxis(0).setUnit('tof')
           # iw = InstrumentWidget("ws")
           # iw.show()

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
        log.info('Substribed to result publisher at ' + uri)

    def get_histogram(self):
        data = numpy.frombuffer(self.socket.recv(), numpy.float64)
        x,y = numpy.array_split(data, 2)
        return x,y

    def _receive_header(self):
        header = self.socket.recv_json()
        command = header['command']
        index = header['index']
        return command, index
