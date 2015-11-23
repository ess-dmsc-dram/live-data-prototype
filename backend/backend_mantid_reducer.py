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
#from create_mantid_workspace_from_events_transition import CreateMantidWorkspaceFromEventsTransition
#from reductions_transition import ReductionsTransition
from mantid_rebin_transition import MantidRebinTransition
from gather_histogram_transition import GatherHistogramTransition


mantid.config['MultiThreaded.MaxCores'] = '1'
#if MPI.COMM_WORLD.Get_rank() != 0:
mantid.ConfigService.setConsoleLogLevel(0)



class BackendMantidRebinner(object):
    def __init__(self):
        self._comm = MPI.COMM_WORLD
        self._target_bin_parameters = None
        self.dummy_transition = FromCheckpointTransition(CompositeCheckpoint(MantidWorkspaceCheckpoint, 1))
        self.rebin_transition = MantidRebinTransition(self.dummy_transition)
        self.gather_histogram_transition = GatherHistogramTransition(self.rebin_transition)

    def get_bin_boundaries(self):
        return self.rebin_transition.get_checkpoint()[-1].data.readX(0)

    def get_bin_values(self):
        return self.rebin_transition.get_checkpoint()[-1].data.readY(0)

    def rebin(self):
        self.rebin_transition.bin_parameters = self._target_bin_parameters
        self.rebin_transition.trigger_rerun()

    def reset(self):
        self.dummy_transition = FromCheckpointTransition(CompositeCheckpoint(MantidWorkspaceCheckpoint, 1))
        self.rebin_transition = MantidRebinTransition(self.dummy_transition)
        self.gather_histogram_transition = GatherHistogramTransition(self.rebin_transition)

    def next(self):
        self.dummy_transition.get_checkpoint().add_checkpoint(MantidWorkspaceCheckpoint())

    def get_parameter_dict(self):
        return {'bin_parameters':(self.set_bin_parameters, 'string')}

    def set_bin_parameters(self, bin_parameters):
        self._target_bin_parameters = str(bin_parameters)


class BackendMantidReducer(BackendWorker):
    def __init__(self, data_queue_in, rebinner):
        BackendWorker.__init__(self)
        self._data_queue_in = data_queue_in
        self._rebinner = rebinner
        self._reducer = BasicPowderDiffraction()
        self._packet_index = 0
        self._bin_parameters = '0.4,0.1,5'
        self._filter_pulses = False

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
        event_ws = self._create_workspace_from_events(event_data)
        reduced = self._reduce(event_ws)
        self._rebinner.dummy_transition.append(reduced)
        return True

    def _create_workspace_from_events(self, event_data):
        ws = WorkspaceFactory.Instance().create("EventWorkspace", 1, 1, 1);
        AnalysisDataService.Instance().addOrReplace('POWDIFF_test', ws)
        ws =  AnalysisDataService['POWDIFF_test']
        mantid.LoadInstrument(Workspace=ws, Filename='/home/simon/data/fake_powder_diffraction_data/POWDIFF_Definition.xml')
        ws.padSpectra()
        ws.getAxis(0).setUnit('tof')
        ws.setStorageMode(StorageMode.Distributed)
        for i in event_data:
            ws.getEventList(int(i[0])).addEventQuickly(float(i[1]), DateAndTime(self._pulse_time))
        return ws

    def _reduce(self, ws):
        ws = self._reducer.reduce(ws, 'summed-{}'.format(self._packet_index))
        # TODO: ADS issues, see Mantid issue #14120. Can we keep this out of ADS?
        self._packet_index += 1
        return ws

    def get_parameter_dict(self):
        return {'bin_parameters':'str', 'reset':'trigger', 'next':'trigger', 'filter_pulses':'bool'}

    @property
    def bin_parameters(self):
        return self._bin_parameters

    @bin_parameters.setter
    def bin_parameters(self, parameters):
        self._bin_parameters = parameters
        self._rebinner.set_bin_parameters(parameters)
        self._rebinner.rebin()

    @property
    def filter_pulses(self):
        return self._filter_pulses

    @filter_pulses.setter
    def filter_pulses(self, filter_pulses):
        self._filter_pulses = filter_pulses
        self._rebinner.next()

    @property
    def reset(self):
        return False

    @reset.setter
    def reset(self, dummy):
        self._rebinner.reset()

    @property
    def next(self):
        return False

    @next.setter
    def next(self, dummy):
        self._rebinner.next()
