from threading import Thread
import PyQt4
import sys
from logger import setup_global_logger
import ports
import command_line_parser
from visualizer import DataListener
from visualizer import InstrumentView

app = PyQt4.QtGui.QApplication(sys.argv)

setup_global_logger(level=command_line_parser.get_log_level())

data_listener = DataListener(host=command_line_parser.get_host(), port=ports.result_stream)
data_listener_thread = Thread(target=data_listener.run)
data_listener_thread.daemon = True
instrumentview = InstrumentView(data_listener)
print "til datalistener"
data_listener.clear.connect(instrumentview.clear)
data_listener.new_data.connect(instrumentview.updateInstrumentView)
data_listener_thread.start()
print "post thread start"

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        app.instance().exec_()
