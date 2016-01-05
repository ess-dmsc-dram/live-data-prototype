from backend import BackendEventListener
from backend import ZMQQueueServer
import ports
import command_line_parser

import threading
import time
import numpy
from mpi4py import MPI

from logger import setup_global_logger


rank = MPI.COMM_WORLD.Get_rank()
event_queue_port = 11000 + rank

setup_global_logger(level=command_line_parser.get_log_level(), rank=rank)

event_queue_out = ZMQQueueServer(port=event_queue_port)
event_queue_out_thread = threading.Thread(target=event_queue_out.run)
event_queue_out_thread.start()

listener = BackendEventListener(event_queue_out, host=command_line_parser.get_host(), port=ports.event_stream)
listener_thread = threading.Thread(target=listener.run)
listener_thread.start()
