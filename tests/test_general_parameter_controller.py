from general_parameter_controller import GeneralParameterController

import unittest
import numpy as np
from mock import patch, call


class MockParameterControlClient(object):
    def send(self):
        pass


class TestGeneralParameterController(unittest.TestCase):
    def test_construction_updated_parameter_cache(self):
        with patch.object(GeneralParameterController, '_update_parameter_type_cache') as mock_method:
            controller = GeneralParameterController(MockParameterControlClient())

        self.assertEqual(mock_method.call_count, 1, 'Constructor did not update parameter cache.')

    def test_client_send_is_called_twice_on_update(self):
        with patch.object(MockParameterControlClient, 'send') as mock_method:
            controller = GeneralParameterController(MockParameterControlClient())

        self.assertEqual(mock_method.call_count, 2, 'Send was not called twice.')

    def test_parameter_type_cache_works(self):
        replies = [
            {'payload': {'TestControllee': {'test_param_1': 'float', 'test_param_2': 'int'}}},
            {'payload': {'TestControllee': {'test_param_1': 4.5, 'test_param_2': 34}}}
        ]

        with patch.object(MockParameterControlClient, 'send', side_effect=replies) as mock_method:
            controller = GeneralParameterController(MockParameterControlClient())

            self.assertEqual(controller._convert_to_cached_type('TestControllee', 'test_param_1', '0.6'), 0.6)
            self.assertEqual(controller._convert_to_cached_type('TestControllee', 'test_param_2', '443'), 443)

        expected_calls = [call('control', 'send_parameters'),
                          call('get_values', {'TestControllee': {'test_param_1': 'float', 'test_param_2': 'int'}})]
        mock_method.assert_has_calls(expected_calls)

    def test_set_parameter_value(self):
        replies = [
            {'payload': {'TestControllee': {'test_param_1': 'float', 'test_param_2': 'int'}}},
            {'payload': {'TestControllee': {'test_param_1': 4.5, 'test_param_2': 34}}},
            {'payload': 'Ok.'}, {'payload': 'Ok.'}
        ]

        with patch.object(MockParameterControlClient, 'send', side_effect=replies) as mock_method:
            controller = GeneralParameterController(MockParameterControlClient())
            controller.set_parameter_value('TestControllee', 'test_param_1', '34')
            controller.set_parameter_value('TestControllee', 'test_param_2', '45')

        expected_calls = [call('control', 'send_parameters'),
                          call('get_values', {'TestControllee': {'test_param_1': 'float', 'test_param_2': 'int'}}),
                          call('set_parameters', {'TestControllee': {'test_param_1': 34.0}}),
                          call('set_parameters', {'TestControllee': {'test_param_2': 45.0}})]
        mock_method.assert_has_calls(expected_calls)


if __name__ == '__main__':
    unittest.main()
