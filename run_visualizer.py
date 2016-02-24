from threading import Thread
import argparse
from pyqtgraph.Qt import QtGui

from logger import setup_global_logger
import ports
import command_line_parser
from visualizer import DataListener
from visualizer import Plotter
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

setup_global_logger(level=command_line_parser.get_log_level())
parser.add_argument('-p', '--port', type=str, default='10003', help='Port to connect to.')
parser.add_argument('-H', '--host', type=str, default='localhost', help='Host to connect to.')
args = parser.parse_args()



data_listener = DataListener(args.host, args.port)
data_listener_thread = Thread(target=data_listener.run)
data_listener_thread.daemon = True
plotter = Plotter(data_listener)

data_listener.clear.connect(plotter.clear)
data_listener.new_data.connect(plotter.update)
data_listener_thread.start()

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
