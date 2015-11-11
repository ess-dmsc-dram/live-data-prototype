from collections import deque
import time
import numpy

from controllable import Controllable


class EventGenerator(Controllable):
    def __init__(self, generator):
        super(EventGenerator, self).__init__(type(self).__name__)
        self.event_data = deque()
        self._meta_data = deque()
        # do things on per-pulse basis?
        # each chunk must have a pulse ID!
        self._events_per_pulse_mean = 10000
        self._events_per_pulse_spread = 100
        self._max_chunk_size = 5000
        self._pulses_per_second = 14
        self.generator = generator
        self._paused = False

    def run(self):
        print 'Starting EventGenerator...'
        self.init_sleep_time()
        while True:
            while self._paused:
                time.sleep(0.01)
            self.generate_events()
            self.sleep()
            self.update_sleep_time()

    def generate_events(self):
        remaining = max(1, int(numpy.random.normal(loc=self._events_per_pulse_mean, scale=self._events_per_pulse_spread)))
        while remaining >= self._max_chunk_size:
            self.event_data.append(self.generator.get_events(min(remaining, self._max_chunk_size)))
            remaining -= self._max_chunk_size

    def get_events(self):
        while True:
            if self.event_data:
                return self.event_data.popleft()

    def get_meta_data(self):
        if self._meta_data:
            return self._meta_data.popleft()
        else:
            return None

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
        print 'sleep time: {} current pulse rate: {}/second'.format(self.sleep_time, 1.0/elapsed)
        if self.sleep_time == 0.0:
            self.sleep_time = max(0.0, 1.0/self._pulses_per_second - elapsed)
        else:
            if 1.0/elapsed < self._pulses_per_second:
                self.sleep_time = self.sleep_time * 0.99
            else:
                self.sleep_time = self.sleep_time * 1.01
        self.end_old = self.end_new

    def get_parameter_dict(self):
        return {
                'events_per_pulse_mean':'int',
                'events_per_pulse_spread':'int',
                'max_chunk_size':'int',
                'pulses_per_second':'float',
                'queue_status':'int',
                'pause':'trigger'
                }

    @property
    def events_per_pulse_mean(self):
        return self._events_per_pulse_mean

    @events_per_pulse_mean.setter
    def events_per_pulse_mean(self, events_per_pulse_mean):
        self._events_per_pulse_mean = events_per_pulse_mean

    @property
    def events_per_pulse_spread(self):
        return self._events_per_pulse_spread

    @events_per_pulse_spread.setter
    def events_per_pulse_spread(self, events_per_pulse_spread):
        self._events_per_pulse_spread = events_per_pulse_spread

    @property
    def max_chunk_size(self):
        return self._max_chunk_size

    @max_chunk_size.setter
    def max_chunk_size(self, max_chunk_size):
        self._max_chunk_size = max_chunk_size

    @property
    def pulses_per_second(self):
        return self._pulses_per_second

    @pulses_per_second.setter
    def pulses_per_second(self, pulses_per_second):
        self._pulses_per_second = pulses_per_second

    @property
    def queue_status(self):
        return len(self.event_data)

    def pause(self):
        self._paused = not self._paused
