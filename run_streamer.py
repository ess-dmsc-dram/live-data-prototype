import threading
import time
import zmq

import ports
from parameter_control_server import ParameterControlServer
from streamer.fake_streamer import FakeEventStreamer
from streamer.event_generator import EventGenerator

from streamer.distribution_file_based_event_generator import DistributionFileBasedEventGenerator
from streamer.bragg_peak_event_generator import create_BraggEventGenerator
from streamer.bragg_peak_event_generator import CrystalStructure


baseGenerator = create_BraggEventGenerator('/home/simon/data/fake_powder_diffraction_data/POWDIFF_Definition.xml', CrystalStructure('5.431 5.431 5.431', 'F d -3 m', "Si 0 0 0 1.0 0.01"), 0.5, 4.0)
#baseGenerator = DistributionFileBasedEventGenerator('/home/simon/data/fake_powder_diffraction_data/event_distribution.npy')

eventGenerator = EventGenerator(baseGenerator)
eventGenerator.start()

streamer = FakeEventStreamer(eventGenerator)
streamer.start()

parameterController = ParameterControlServer(port=ports.streamer_control, parameter_dict=eventGenerator.get_parameter_dict())
parameterController_thread = threading.Thread(target=parameterController.run)
parameterController_thread.start()

while threading.active_count() > 0:
    time.sleep(0.1)
