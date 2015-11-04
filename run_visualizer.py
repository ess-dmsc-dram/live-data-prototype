from pyqtgraph.Qt import QtGui

from visualizer import DataListener
from visualizer import Plotter


dataListener = DataListener()
plotter = Plotter(dataListener)

dataListener.new_data.connect(plotter.update)
dataListener.start()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
