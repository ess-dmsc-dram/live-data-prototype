import threading
import time
import argparse

from logger import setup_global_logger
import ports
from parameter_control_server import ParameterControlServer
from streamer import create_BraggEventGenerator
from streamer import start_streamer_daemon_threads


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-i", "--instrument-definition", type=str,  default='data/POWDIFF_Definition.xml', help="Mantid instrument definition file.")
parser.add_argument("-u", "--unit-cell", type=str,  default='5.431 5.431 5.431', help="Mantid instrument definition file.")
parser.add_argument("-s", "--space-group", type=str,  default='F d -3 m', help="")
parser.add_argument("-a", "--atoms", type=str,  default='Si 0 0 0 1.0 0.01', help="")
parser.add_argument("-[", "--min-plane-distance", type=float,  default=0.5, help="")
parser.add_argument("-]", "--max-plane-distance", type=float,  default=4.0, help="")

args = parser.parse_args()

setup_global_logger(level=args.log)

base_generator = create_BraggEventGenerator(args.instrument_definition, (args.unit_cell, args.space_group, args.atoms), args.min_plane_distance, args.max_plane_distance)
parameter_controller = ParameterControlServer(port=ports.streamer_control)

start_streamer_daemon_threads(base_generator, parameter_controller)

while threading.active_count() > 0:
    time.sleep(0.1)
