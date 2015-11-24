import threading
from copy import deepcopy
import time
import json

import numpy
from mpi4py import MPI

from backend_worker import BackendWorker
from reductions import BasicPowderDiffraction

import mantid.simpleapi as mantid
from mantid.api import WorkspaceFactory
from mantid.api import AnalysisDataService
from mantid.api import StorageMode
from mantid.kernel import DateAndTime

from checkpoint import CompositeCheckpoint
from mantid_workspace_checkpoint import MantidWorkspaceCheckpoint
from histogram_checkpoint import HistogramCheckpoint

from transition import FromCheckpointTransition
from create_mantid_workspace_from_events_transition import CreateMantidWorkspaceFromEventsTransition
from reductions_transition import ReductionTransition
from splitting_transition import SplittingTransition
from mantid_rebin_transition import MantidRebinTransition
from gather_histogram_transition import GatherHistogramTransition


mantid.config['MultiThreaded.MaxCores'] = '1'
#if MPI.COMM_WORLD.Get_rank() != 0:
mantid.ConfigService.setConsoleLogLevel(0)


class BackendMantidReducer(BackendWorker):
    def __init__(self, data_queue_in):
        BackendWorker.__init__(self)
        self._data_queue_in = data_queue_in
        self._reducer = BasicPowderDiffraction()
        self._filter_pulses = False
        self._create_workspace_from_events_transition = CreateMantidWorkspaceFromEventsTransition()
        self._reduction_transition = ReductionTransition(self._create_workspace_from_events_transition, self._reducer)
        self._splitting_transition = SplittingTransition(self._reduction_transition)
        self._rebin_transition = MantidRebinTransition(self._splitting_transition)
        self._gather_histogram_transition = GatherHistogramTransition(self._rebin_transition)

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
        self._drop_pulse = abs(lattice_spacing - 5.431) > 0.01
        print('Received meta data {}, ignoring.'.format(data['payload']))
        return True

    def _process_event_data(self, data):
        if self._filter_pulses and self._drop_pulse:
            return True
        event_data = numpy.frombuffer(data, dtype={'names':['detector_id', 'tof'], 'formats':['int32','float32']})
        self._create_workspace_from_events_transition.process(event_data, self._pulse_time)
        return True

    def get_bin_boundaries(self):
        return self._rebin_transition.get_checkpoint()[-1].data.readX(0)

    def get_bin_values(self):
        return self._rebin_transition.get_checkpoint()[-1].data.readY(0)

    def get_parameter_dict(self):
        return {'bin_parameters':'str', 'reset':'trigger', 'next':'trigger', 'filter_pulses':'bool'}

    @property
    def bin_parameters(self):
        return self._rebin_transition._bin_parameters

    @bin_parameters.setter
    def bin_parameters(self, parameters):
        self._rebin_transition.set_bin_parameters(parameters)

    @property
    def filter_pulses(self):
        return self._filter_pulses

    @filter_pulses.setter
    def filter_pulses(self, filter_pulses):
        self._filter_pulses = filter_pulses
        self._splitting_transition.next()

    @property
    def reset(self):
        return False

    @reset.setter
    def reset(self, dummy):
        self._splitting_transition.reset()

    @property
    def next(self):
        return False

    @next.setter
    def next(self, dummy):
        self._splitting_transition.next()
