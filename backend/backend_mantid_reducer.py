import json
from threading import Lock

import numpy

from backend_worker import BackendWorker
from reductions import BasicPowderDiffraction

from create_mantid_workspace_from_events_transition import CreateMantidWorkspaceFromEventsTransition
from reductions_transition import ReductionTransition
from mantid_filter_transition import MantidFilterTransition
from mantid_rebin_transition import MantidRebinTransition
from gather_histogram_transition import GatherHistogramTransition


class BackendMantidReducer(BackendWorker):
    def __init__(self, data_queue_in):
        BackendWorker.__init__(self)
        self._lock = Lock()
        self._data_queue_in = data_queue_in
        self._reducer = BasicPowderDiffraction()
        self._filter_pulses = False
        self._create_workspace_from_events_transition = CreateMantidWorkspaceFromEventsTransition()
        self._reduction_transition = ReductionTransition(self._create_workspace_from_events_transition, self._reducer)
        self._reduction_transition.accumulate_data = True
        self._filter_transition = MantidFilterTransition(self._reduction_transition)
        self._filter_transition.accumulate_data = True
        self._rebin_transition = MantidRebinTransition(self._filter_transition)
        self._gather_histogram_transition = GatherHistogramTransition(self._rebin_transition)
        self._gather_histogram_transition.accumulate_data = True

    def _process_command(self, command):
        setattr(self, command[0], command[1])

    def _can_process_data(self):
        if self._data_queue_in:
            return True
        else:
            return False

    def _process_data(self):
        if not self._data_queue_in:
            return False

        header, data = self._data_queue_in.get()

        if header == 'meta_data':
            return self._process_meta_data(data)
        else:
            return self._process_event_data(data)

    def _process_meta_data(self, data):
        data = json.loads(data)
        self._pulse_time = str(data['pulse_time'])
        payload = data['payload']
        lattice_spacing = float(payload['unit_cell'].split()[0])
        self._create_workspace_from_events_transition.set_log_data({'lattice_spacing':lattice_spacing})
        self._drop_pulse = abs(lattice_spacing - 5.431) > 0.01
        print('Received meta data {}, ignoring.'.format(data['payload']))
        return True

    def _process_event_data(self, data):
        if self._filter_pulses and self._drop_pulse:
            return True
        event_data = numpy.frombuffer(data, dtype={'names':['detector_id', 'tof'], 'formats':['int32','float32']})
        self._lock.acquire()
        self._create_workspace_from_events_transition.process(event_data, self._pulse_time)
        self._lock.release()
        return True

    def get_bin_boundaries(self):
        return self._rebin_transition.get_checkpoint()[-1].data.readX(0)

    def get_bin_values(self):
        return self._rebin_transition.get_checkpoint()[-1].data.readY(0)

    def get_parameter_dict(self):
        return {'bin_parameters':'str', 'filter_interval_parameters':'str', 'filter_pulses':'bool'}

    @property
    def bin_parameters(self):
        return self._rebin_transition._bin_parameters

    @bin_parameters.setter
    def bin_parameters(self, parameters):
        self._lock.acquire()
        self._rebin_transition.set_bin_parameters(parameters)
        self._lock.release()

    @property
    def filter_pulses(self):
        return self._filter_pulses

    @filter_pulses.setter
    def filter_pulses(self, filter_pulses):
        self._filter_pulses = filter_pulses
        self._splitting_transition.next()

    @property
    def filter_interval_parameters(self):
        return 'min,step,max'

    @filter_interval_parameters.setter
    def filter_interval_parameters(self, parameters):
        self._lock.acquire()
        self._filter_transition.set_interval_parameters(parameters)
        self._lock.release()
