from collections import deque
import time
import numpy

from controllable import Controllable


class EventGenerator(Controllable):
    def __init__(self, generator):
        super(EventGenerator, self).__init__(type(self).__name__)
        self.event_data = deque()
        self._rate = 100000.0
        # do things on per-pulse basis?
        # each chunk must have a pulse ID!
        self.chunk_size = 5000
        self.generator = generator

    def run(self):
        print 'Starting EventGenerator...'
        self.init_sleep_time()
        while True:
            self.generate_events()
            self.sleep()
            self.update_sleep_time()

    def generate_events(self):
        self.event_data.append(self.generator.get_events(self.chunk_size))

    def get_events(self):
        while True:
            if self.event_data:
                return self.event_data.popleft()

    def get_type_info(self):
        return {'names':['detector_id', 'tof'], 'formats':['int32','float32']}

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

    def get_parameter_dict(self):
        return {'rate':'float', 'chunk_size':'int'}

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, rate):
        self._rate = rate

    @property
    def chunk_size(self):
        return self._chunk_size

    @chunk_size.setter
    def chunk_size(self, chunk_size):
        self._chunk_size = chunk_size
