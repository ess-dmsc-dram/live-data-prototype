from threading import Thread
import time
import random
import sys
import PyQt4
import mantid.simpleapi as simpleapi
import mantidqtpython as mpy
import numpy

ws = simpleapi.WorkspaceFactory.create("Workspace2D", 1000, 2,1)
simpleapi.AnalysisDataService.Instance().addOrReplace('POWDIFF_test', ws)
simpleapi.LoadInstrument(Workspace=ws, Filename='data/POWDIFF_Definition.xml', RewriteSpectraMap=True)
ws = simpleapi.Rebin(ws, "0,0.1,2")
simpleapi.AnalysisDataService.Instance().addOrReplace('POWDIFF_test', ws)
InstrumentWidget = mpy.MantidQt.MantidWidgets.InstrumentWidget
app = PyQt4.QtGui.QApplication(sys.argv)
iw = InstrumentWidget("POWDIFF_test")
iw.show()
picktab = iw.getTab("Pick")
picktab.__class__ = mpy.MantidQt.MantidWidgets.InstrumentWidgetPickTab
#picktab.get_currentPickID()
dir(picktab)

x = 1
def addtoY():
    x =1
    while 1:
        time.sleep(1)
        x+=1
        print x

        ws.dataY(2)[1]+=1
	ws.dataY(random.randint(1,999))[random.randint(1,9)] += random.randint(1,6)
        simpleapi.AnalysisDataService.Instance().addOrReplace('POWDIFF_test', ws) #added this line
        print "the detector ID is"
	print picktab.get_currentPickID()


ws.dataY(1)[9] = 3
ws.dataY(1)[8] = 9
addThread = Thread(target=addtoY)
addThread.start()
app.exec_()
