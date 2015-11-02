from threading import Thread
from fake_streamer import FakeEventStreamer
from event_generator import EventGenerator


def start_streamer_daemon_threads(base_generator, parameter_controller):
    event_generator = EventGenerator(base_generator)
    event_generator_thread = Thread(target=event_generator.run)
    event_generator_thread.daemon = True
    event_generator_thread.start()

    streamer = FakeEventStreamer(event_generator)
    streamer_thread = Thread(target=streamer.run)
    streamer_thread.daemon = True
    streamer_thread.start()

    parameter_controller.set_controllee(event_generator)
    parameter_controller_thread = Thread(target=parameter_controller.run)
    parameter_controller_thread.daemon = True
    parameter_controller_thread.start()
