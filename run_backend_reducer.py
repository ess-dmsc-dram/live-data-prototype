from logger import setup_global_logger
from backend import BackendMantidReducer
from backend import ResultPublisher
from backend import InstrumentViewPublisher
from backend import ZMQQueueServer
from backend import ZMQQueueClient
from parameter_control_server import ParameterControlServer
import ports

import threading
import time
import argparse
import numpy
from mpi4py import MPI


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-l", "--log", type=str,  default='info', help="Set the log level. Allowed values are 'critical', 'error', 'warning', 'info', and 'debug'.")
args = parser.parse_args()

rank = MPI.COMM_WORLD.Get_rank()
event_queue_port = 11000 + rank

setup_global_logger(level=args.log, rank=rank)

event_queue_in = ZMQQueueClient(port=event_queue_port)
event_queue_in_thread = threading.Thread(target=event_queue_in.run)
event_queue_in_thread.start()


reducer = BackendMantidReducer(event_queue_in)
reducer_thread = threading.Thread(target=reducer.run)
reducer_thread.start()

if MPI.COMM_WORLD.Get_rank() == 0:
    reducer_controller = ParameterControlServer(controllees=[reducer], port=ports.rebin_control)
    reducer_controller_thread = threading.Thread(target=reducer_controller.run)
    reducer_controller_thread.start()

    resultPublisher = ResultPublisher(reducer)
    resultPublisher_thread = threading.Thread(target=resultPublisher.run)
    resultPublisher_thread.start()
    instrumentViewPublisher = InstrumentViewPublisher(reducer)
    instrumentViewPublisher_thread = threading.Thread(target=instrumentViewPublisher.run)
    instrumentViewPublisher_thread.start()
    parameterController = ParameterControlServer(controllees=[instrumentViewPublisher], port=ports.result_publisher_control)
    parameterController = ParameterControlServer(controllees=[resultPublisher], port=ports.result_publisher_control)
    parameterController_thread = threading.Thread(target=parameterController.run)
    parameterController_thread.start()

while threading.active_count() > 0:
    time.sleep(0.1)
