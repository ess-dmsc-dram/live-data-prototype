from streamer.bragg_peak_event_generator import BraggPeakEventGenerator

import unittest
from mock import patch
import numpy as np


class MockTOFFactorCalculator(object):
    def __init__(self, tof_factors=[0]):
        self._tof_factors = tof_factors

    def get_tof_factors(self):
        return self._tof_factors


class TestBraggPeakEventGenerator(unittest.TestCase):
    def test_construction_incorrect_parameter_length(self):
        with self.assertRaises(RuntimeError):
            BraggPeakEventGenerator(['5.43 5.43 5.43', 'F d -3 m'], 0.4, 4.0, MockTOFFactorCalculator())

        with self.assertRaises(RuntimeError):
            BraggPeakEventGenerator(['5.431 5.431 5.431', 'F d -3 m', 'Si 0 0 0 1.0 0.01', 'Four'], 0.4, 4.0,
                                    MockTOFFactorCalculator())

        # try:
        BraggPeakEventGenerator(['5.431 5.431 5.431', 'F d -3 m', 'Si 0 0 0 1.0 0.01'], 0.4, 4.0,
                                MockTOFFactorCalculator())
        # except:
        # self.assertTrue(False, 'Constructor with three crystal_structure_parameters failed, but it should not.')

    def test_unit_cell_updates_distributions(self):
        generator = BraggPeakEventGenerator(['5.431 5.431 5.431', 'F d -3 m', 'Si 0 0 0 1.0 0.01'], 3.0, 4.0,
                                            MockTOFFactorCalculator([2500.]))

        with patch.object(generator, '_update_distributions_and_weights') as mock_method:
            generator.unit_cell = '4 4 4'
            self.assertEquals(generator.unit_cell, '4 4 4')

        self.assertEqual(mock_method.call_count, 1,
                         '_update_distributions_and_weights has been called the wrong number of times when setting unit_cell: {}'.format(
                             mock_method.call_count))

    def test_space_group_updates_distributions(self):
        generator = BraggPeakEventGenerator(['5.431 5.431 5.431', 'F d -3 m', 'Si 0 0 0 1.0 0.01'], 3.0, 4.0,
                                            MockTOFFactorCalculator([2500.]))

        with patch.object(generator, '_update_distributions_and_weights') as mock_method:
            generator.space_group = 'P m -3 m'
            self.assertEquals(generator.space_group, 'P m -3 m')

        self.assertEqual(mock_method.call_count, 1,
                         '_update_distributions_and_weights has been called the wrong number of times when setting space_group: {}'.format(
                             mock_method.call_count))

    def test_atoms_updates_distributions(self):
        generator = BraggPeakEventGenerator(['5.431 5.431 5.431', 'F d -3 m', 'Si 0 0 0 1.0 0.01'], 3.0, 4.0,
                                            MockTOFFactorCalculator([2500.]))

        with patch.object(generator, '_update_distributions_and_weights') as mock_method:
            generator.atoms = 'Si 0.1 0.1 0.1 1.0 0.002'
            self.assertEquals(generator.atoms, 'Si 0.1 0.1 0.1 1.0 0.002')

        self.assertEqual(mock_method.call_count, 1,
                         '_update_distributions_and_weights has been called the wrong number of times when setting atoms: {}'.format(
                             mock_method.call_count))

    def test_d_min_updates_distributions(self):
        generator = BraggPeakEventGenerator(['5.431 5.431 5.431', 'F d -3 m', 'Si 0 0 0 1.0 0.01'], 3.0, 4.0,
                                            MockTOFFactorCalculator([2500.]))

        with patch.object(generator, '_update_distributions_and_weights') as mock_method:
            generator.d_min = 0.2
            self.assertEquals(generator.d_min, 0.2)

        self.assertEqual(mock_method.call_count, 1,
                         '_update_distributions_and_weights has been called the wrong number of times when setting d_min: {}'.format(
                             mock_method.call_count))

    def test_d_max_updates_distributions(self):
        generator = BraggPeakEventGenerator(['5.431 5.431 5.431', 'F d -3 m', 'Si 0 0 0 1.0 0.01'], 3.0, 4.0,
                                            MockTOFFactorCalculator([2500.]))

        with patch.object(generator, '_update_distributions_and_weights') as mock_method:
            generator.d_max = 4.0
            self.assertEquals(generator.d_max, 4.0)

        self.assertEqual(mock_method.call_count, 1,
                         '_update_distributions_and_weights has been called the wrong number of times when setting d_max: {}'.format(
                             mock_method.call_count))

    def test_relative_peak_width_updates_distributions(self):
        generator = BraggPeakEventGenerator(['5.431 5.431 5.431', 'F d -3 m', 'Si 0 0 0 1.0 0.01'], 3.0, 4.0,
                                            MockTOFFactorCalculator([2500.]))

        with patch.object(generator, '_update_distributions_and_weights') as mock_method:
            generator.relative_peak_width = 4.0
            self.assertEquals(generator.relative_peak_width, 4.0)

        self.assertEqual(mock_method.call_count, 1,
                         '_update_distributions_and_weights has been called the wrong number of times when setting relative_peak_width: {}'.format(
                             mock_method.call_count))

    def test_get_events(self):
        generator = BraggPeakEventGenerator(['5.431 5.431 5.431', 'F d -3 m', 'Si 0 0 0 1.0 0.01'], 3.0, 4.0,
                                            MockTOFFactorCalculator([2500.]))

        generator.relative_peak_width = 0.0001

        # Generates events only for one peak, and only for one detector.
        events = generator.get_events(10)

        # All events should have the same detector id
        self.assertTrue(np.all(events['detector_id'] == 0))

        # The TOFs should correspond to d values of roughly 5.431 / sqrt(3)
        delta_d_values = np.fabs((events['tof'] / 2500. * np.sqrt(3)) - 5.431)
        self.assertTrue(np.all(delta_d_values < 2e-3))


if __name__ == '__main__':
    unittest.main()
