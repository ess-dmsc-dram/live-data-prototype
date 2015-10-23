import numpy


class DistributionFileBasedEventGenerator():
    def __init__(self, distribution_file):
        self._load_event_data(distribution_file)

    def get_events(self, count):
        events = numpy.ndarray(shape=(count), dtype=self.get_type_info())
        indices = numpy.random.random_integers(0, len(self.generator_data)-1, count)
        for i in range(count):
            events[i] = self.generator_data[indices[i]]
        return events

    def get_type_info(self):
        return {'names':['detector_id', 'tof'], 'formats':['int32','float32']}

    def _load_event_data(self, distribution_file):
        print 'Loading event distribution...'
        self.generator_data = numpy.load(distribution_file)
