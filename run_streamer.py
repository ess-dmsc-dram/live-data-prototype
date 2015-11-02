import threading
import time
import zmq

import ports
from parameter_control_server import ParameterControlServer
from streamer import FakeEventStreamer
from streamer import EventGenerator
from streamer import DistributionFileBasedEventGenerator
from streamer import create_BraggEventGenerator
from streamer import CrystalStructure


base_generator = create_BraggEventGenerator('/home/simon/data/fake_powder_diffraction_data/POWDIFF_Definition.xml', CrystalStructure('5.431 5.431 5.431', 'F d -3 m', "Si 0 0 0 1.0 0.01"), 0.5, 4.0)
#baseGenerator = DistributionFileBasedEventGenerator('/home/simon/data/fake_powder_diffraction_data/event_distribution.npy')

event_generator = EventGenerator(base_generator)
event_generator_thread = threading.Thread(target=event_generator.run)
event_generator_thread.daemon = True
event_generator_thread.start()

streamer = FakeEventStreamer(event_generator)
streamer_thread = threading.Thread(target=streamer.run)
streamer_thread.daemon = True
streamer_thread.start()

parameter_controller = ParameterControlServer(port=ports.streamer_control, parameter_dict=event_generator.get_parameter_dict())
parameter_controller_thread = threading.Thread(target=parameter_controller.run)
parameter_controller_thread.daemon = True
parameter_controller_thread.start()

while threading.active_count() > 0:
    time.sleep(0.1)
