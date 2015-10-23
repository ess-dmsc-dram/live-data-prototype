import threading
from collections import deque
import time
import numpy


class EventGenerator(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.event_data = deque()
        self.rate = 1000000.0
        # do things on per-pulse basis?
        # each chunk must have a pulse ID!
        self.chunk_size = 50000
        self.scale = 1.0
        self.size = 5000
        self.generator_data = None

    def run(self):
        print 'Starting EventGenerator...'
        self.load_event_data()
        self.init_sleep_time()
        while True:
            self.generate_events()
            self.sleep()
            self.update_sleep_time()

    def generate_events(self):
        events = numpy.ndarray(shape=(self.chunk_size,2), dtype=float)
        indices = numpy.random.random_integers(0, len(self.generator_data)-1, self.chunk_size)
        for i in range(self.chunk_size):
            events[i] = self.generator_data[indices[i]]
        self.event_data.append(events)

        #events = numpy.hstack([numpy.random.normal(size=self.size, scale=self.scale), numpy.random.normal(size=260, loc=4)])
        #self.event_data.append(events)

    def get_events(self):
        while True:
            if self.event_data:
                return self.event_data.popleft()
            time.sleep(0.01)

    def sleep(self):
        time.sleep(self.sleep_time)

    def init_sleep_time(self):
        self.sleep_time = 0.0
        self.end_old = time.time()

    def update_sleep_time(self):
        self.end_new = time.time()
        elapsed = self.end_new - self.end_old
        print 'sleep time: {} current rate: {}'.format(self.sleep_time, float(self.chunk_size)/elapsed)
        if self.sleep_time == 0.0:
            self.sleep_time = max(0.0, float(self.chunk_size)/self.rate - elapsed)
        else:
            if float(self.chunk_size)/elapsed < self.rate:
                self.sleep_time = self.sleep_time * 0.99
            else:
                self.sleep_time = self.sleep_time * 1.01
        self.end_old = self.end_new

    def load_event_data(self):
        print 'Loading event distribution...'
        self.generator_data = numpy.load('/home/simon/data/fake_powder_diffraction_data/event_distribution.npy')

    def get_parameter_dict(self):
        return {'rate':(self.set_rate, 'float'), 'chunk_size':(self.set_chunk_size, 'int'), 'scale':(self.set_scale, 'float'), 'size':(self.set_size, 'int')}

    def set_rate(self, rate):
        self.rate = rate

    def set_chunk_size(self, chunk_size):
        self.chunk_size = chunk_size

    def set_scale(self, scale):
        self.scale = scale

    def set_size(self, size):
        self.size = size

