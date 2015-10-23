from mantid.simpleapi import *
from mantid.geometry import CrystalStructure, ReflectionGenerator
import numpy as np
from functools import partial
from scipy.constants import m_n, h
import time

class BraggPeakEventGenerator(object):
    def __init__(self, crystal_structure, d_min, d_max, tof_factors):
        super(BraggPeakEventGenerator, self).__init__()

        self.distributions, self.weights = self._get_bragg_peak_parameters(crystal_structure, d_min, d_max)
        self.tof_factors = tof_factors
        self.detector_ids = range(len(self.tof_factors))

    def _get_bragg_peak_parameters(self, crystal_structure, d_min, d_max):
        gen = ReflectionGenerator(crystal_structure)
        hkls = gen.getUniqueHKLs(d_min, d_max)
        fsqr = gen.getFsSquared(hkls)

        point_group = crystal_structure.getSpaceGroup().getPointGroup()
        mult = [len(point_group.getEquivalents(hkl)) for hkl in hkls]

        weights = np.array([x * y for x, y in zip(fsqr, mult)])
        weights /= sum(weights)

        dval = gen.getDValues(hkls)

        distributions = [partial(np.random.normal, loc=d, scale=0.002 * d) for d in dval]

        return distributions, weights

    def get_events(self, size):
        d_values = self._get_random_d_values(size)
        detector_ids = np.array(np.random.choice(self.detector_ids, size=size), dtype='int32')
        tofs = np.array([d * self.tof_factors[i] for d, i in zip(d_values, detector_ids)], dtype='float32')

        return np.core.records.fromarrays([detector_ids, tofs], names=['detector_id', 'tof'], formats=['int32', 'float32'])

    def _get_random_d_values(self, size):
        return [x() for x in np.random.choice(self.distributions, size=size, p=self.weights)]

    def _d_to_tof(self, d_value, detector_id):
        return 0

    def _get_random_detector_id(self):
        return 0

def create_BraggEventGenerator(idf, crystal_structure, dmin, dmax):
    ws = CreateSimulationWorkspace(Instrument=idf,
                                   BinParams='0.0,0.1,0.2')

    instrument = ws.getInstrument()
    sample = instrument.getSample()
    source_sample_distance = (sample.getPos() - instrument.getSource().getPos()).norm()

    detectors = [ws.getDetector(x) for x in range(ws.getNumberHistograms())]
    sin_theta = [np.sin(ws.detectorTwoTheta(x) / 2.0) for x in detectors]
    distances = [source_sample_distance + (x.getPos() - sample.getPos()).norm() for x in detectors]

    tof_factors = [2.0 * m_n * s * st / h * 1e-4 for s, st in zip(distances, sin_theta)]

    return BraggPeakEventGenerator(cs, dmin, dmax, tof_factors)


if __name__ == '__main__':
    cs = CrystalStructure('5.431 5.431 5.431', 'F d -3 m', "Si 0 0 0 1.0 0.01")

    gen = create_BraggEventGenerator('/data/additional_mantid_test_data/POWDIFF_Definition.xml', cs, 0.5, 4.0)

    s = time.clock()
    events = gen.get_events(200000)
    e = time.clock()

    print e - s