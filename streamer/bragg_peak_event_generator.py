from mantid.simpleapi import CreateSimulationWorkspace
from mantid.geometry import CrystalStructure, ReflectionGenerator
import numpy as np
from functools import partial
from scipy.constants import m_n, h


class TOFFactorCalculator(object):
    def __init__(self, instrument_definition_file):
        self._instrument_definition_file = instrument_definition_file

    def get_tof_factors(self):
        ws = CreateSimulationWorkspace(Instrument=self._instrument_definition_file,
                                       BinParams='0.0,0.1,0.2')

        instrument = ws.getInstrument()
        sample = instrument.getSample()
        source_sample_distance = (sample.getPos() - instrument.getSource().getPos()).norm()

        # Get the detectors of the instrument
        detectors = [ws.getDetector(x) for x in range(ws.getNumberHistograms())]

        # Calculate sin(theta)...
        sin_theta = [np.sin(ws.detectorTwoTheta(x) / 2.0) for x in detectors]

        # ...and the total flight paths for each detector.
        distances = [source_sample_distance + (x.getPos() - sample.getPos()).norm() for x in detectors]

        # Multiplying a d-value in Angstrom with a value in this list gives the TOF in microseconds
        return [2.0 * m_n * s * st / h * 1e-4 for s, st in zip(distances, sin_theta)]


class BraggPeakEventGenerator(object):
    def __init__(self, crystal_structure_parameters, d_min, d_max, tof_factor_calculator):
        super(BraggPeakEventGenerator, self).__init__()

        # Peak shape related parameters
        self._peak_distributions = None
        self._peak_weights = None
        self._relative_sigma = 0.002

        if len(crystal_structure_parameters) != 3:
            raise RuntimeError('crystal_structure_parameters must contain 3 elements (contains {})'.format(
                len(crystal_structure_parameters)))
        # Crystal structure parameters
        self._unit_cell = crystal_structure_parameters[0]
        self._space_group = crystal_structure_parameters[1]
        self._atoms = crystal_structure_parameters[2]

        # Resolution parameters
        self._d_min = d_min
        self._d_max = d_max

        # Instrument dependent parameters
        self._tof_factors = tof_factor_calculator.get_tof_factors()
        self._detector_ids = range(len(self._tof_factors))

        self._update_distributions_and_weights()

    def _update_distributions_and_weights(self):
        crystal_structure = CrystalStructure(self._unit_cell, self._space_group, self._atoms)
        reflection_generator = ReflectionGenerator(crystal_structure)

        # Calculate all unique reflections within the specified resolution limits, including structure factors
        unique_hkls = reflection_generator.getUniqueHKLs(self.d_min, self.d_max)
        structure_factors = reflection_generator.getFsSquared(unique_hkls)

        # Calculate multiplicities of the reflections
        point_group = crystal_structure.getSpaceGroup().getPointGroup()
        multiplicities = [len(point_group.getEquivalents(hkl)) for hkl in unique_hkls]

        # Calculate weights as F^2 * multiplicity and normalize so that Sum(weights) = 1
        weights = np.array([x * y for x, y in zip(structure_factors, multiplicities)])
        self._peak_weights = weights / sum(weights)

        d_values = reflection_generator.getDValues(unique_hkls)
        self._peak_distributions = [partial(np.random.normal, loc=d, scale=self._relative_sigma * d) for d in d_values]

    def get_events(self, size):
        d_values = self._get_random_d_values(size)
        detector_ids = np.array(np.random.choice(self._detector_ids, size=size), dtype='int32')

        tofs = np.array([d * self._tof_factors[i] for d, i in zip(d_values, detector_ids)], dtype='float32')

        return np.core.records.fromarrays([detector_ids, tofs], names=['detector_id', 'tof'],
                                          formats=['int32', 'float32'])

    def _get_random_d_values(self, size):
        return [x() for x in np.random.choice(self._peak_distributions, size=size, p=self._peak_weights)]

    def get_parameter_dict(self):
        return {'unit_cell': 'str', 'space_group': 'str', 'atoms': 'str',
                'd_min': 'float', 'd_max': 'float', 'relative_peak_width': 'float'}

    @property
    def unit_cell(self):
        return self._unit_cell

    @unit_cell.setter
    def unit_cell(self, new_unit_cell):
        self._unit_cell = new_unit_cell
        self._update_distributions_and_weights()

    @property
    def space_group(self):
        return self._space_group

    @space_group.setter
    def space_group(self, new_space_group):
        self._space_group = new_space_group
        self._update_distributions_and_weights()

    @property
    def atoms(self):
        return self._atoms

    @atoms.setter
    def atoms(self, new_atoms):
        self._atoms = new_atoms
        self._update_distributions_and_weights()

    @property
    def d_min(self):
        return self._d_min

    @d_min.setter
    def d_min(self, new_d_min):
        self._d_min = new_d_min
        self._update_distributions_and_weights()

    @property
    def d_max(self):
        return self._d_max

    @d_max.setter
    def d_max(self, new_d_max):
        self._d_min = new_d_max
        self._update_distributions_and_weights()

    @property
    def relative_peak_width(self):
        return self._relative_sigma

    @relative_peak_width.setter
    def relative_peak_width(self, new_relative_peak_width):
        self._relative_sigma = new_relative_peak_width
        self._update_distributions_and_weights()


def create_BraggEventGenerator(idf, crystal_structure_parameters, dmin, dmax):
    tof_factor_calculator = TOFFactorCalculator(idf)
    return BraggPeakEventGenerator(crystal_structure_parameters, dmin, dmax, tof_factor_calculator)
