import threading
import time
import argparse

import ports
from parameter_control_server import ParameterControlServer
from streamer import create_DistributionFileBasedEventGenerator
from streamer import start_streamer_daemon_threads


parser = argparse.ArgumentParser()
parser.add_argument("-f", "--distribution_file", default='/home/simon/data/fake_powder_diffraction_data/event_distribution.npy', type=str, help=".")
args = parser.parse_args()

base_generator = create_DistributionFileBasedEventGenerator(args.distribution_file)
parameter_controller = ParameterControlServer(port=ports.streamer_control)

start_streamer_daemon_threads(base_generator, parameter_controller)

while threading.active_count() > 0:
    time.sleep(0.1)
