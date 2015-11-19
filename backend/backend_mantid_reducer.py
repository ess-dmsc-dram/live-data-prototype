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


mantid.config['MultiThreaded.MaxCores'] = '1'
#if MPI.COMM_WORLD.Get_rank() != 0:
mantid.ConfigService.setConsoleLogLevel(0)



class BackendMantidRebinner(object):
    def __init__(self):
        self._comm = MPI.COMM_WORLD
        self.resultLock = threading.Lock()
        self.bin_boundaries = [None]
        self.bin_values = [None]
        self.current_bin_parameters = '0.4,0.1,5'
        self._target_bin_parameters = None
        self.checkpoint = CompositeCheckpoint(MantidWorkspaceCheckpoint, 1)
        self.histo_checkpoint = CompositeCheckpoint(MantidWorkspaceCheckpoint, 1)
        self._init_workspace()

    def get_bin_boundaries(self):
        return self.histo_checkpoint[-1].data.readX(0)

    def get_bin_values(self):
        return self.histo_checkpoint[-1].data.readY(0)

    def rebin(self):
        self.current_bin_parameters = self._target_bin_parameters
        tmp = mantid.Rebin(InputWorkspace=self.checkpoint[-1].data, Params=self.current_bin_parameters, PreserveEvents=False)
        self.histo_checkpoint[-1].replace(tmp)
        bin_boundaries = deepcopy(self.get_bin_boundaries())
        bin_values = deepcopy(self.get_bin_values())

        self.update_result(bin_boundaries, bin_values)

    def reset(self):
        self.checkpoint = CompositeCheckpoint(MantidWorkspaceCheckpoint, 1)
        self.histo_checkpoint = CompositeCheckpoint(MantidWorkspaceCheckpoint, 1)
        self.resultLock.acquire()
        self.bin_boundaries = [None]
        self.bin_values = [None]
        self.resultLock.release()
        self._init_workspace()

    def next(self):
        self.resultLock.acquire()
        self.bin_boundaries.append(None)
        self.bin_values.append(None)
        self.resultLock.release()
        self.checkpoint.add_checkpoint(MantidWorkspaceCheckpoint())
        self.histo_checkpoint.add_checkpoint(MantidWorkspaceCheckpoint())
        self._init_workspace()

    def get_parameter_dict(self):
        return {'bin_parameters':(self.set_bin_parameters, 'string')}

    def set_bin_parameters(self, bin_parameters):
        self._target_bin_parameters = str(bin_parameters)

    def update_result(self, bin_boundaries, bin_values):
        self.resultLock.acquire()
        self.bin_boundaries[-1] = bin_boundaries
        gathered = self._comm.gather(bin_values, root=0)
        if self._comm.Get_rank() == 0:
            self.bin_values[-1] = sum(gathered)
        self.resultLock.release()

    def _init_workspace(self):
        tmp = WorkspaceFactory.Instance().create("EventWorkspace", 1, 1, 1);
        AnalysisDataService.Instance().addOrReplace('tmp', tmp)
        tmp =  AnalysisDataService['tmp']
        mantid.LoadInstrument(Workspace=tmp, Filename='/home/simon/data/fake_powder_diffraction_data/POWDIFF_Definition.xml')
        tmp.padSpectra()
        tmp.getAxis(0).setUnit('tof')
        tmp.setStorageMode(StorageMode.Distributed)
        mantid.ConvertUnits(InputWorkspace=tmp, OutputWorkspace=tmp, Target='dSpacing')
        mantid.Rebin(InputWorkspace=tmp, OutputWorkspace=tmp, Params=self.current_bin_parameters)
        tmp = mantid.SumSpectra(InputWorkspace=tmp)
        self.checkpoint[-1].replace(tmp)
        tmp = mantid.Rebin(InputWorkspace=self.checkpoint[-1].data, Params=self.current_bin_parameters, PreserveEvents=False)
        self.histo_checkpoint[-1].replace(tmp)


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
        self._merge(reduced)
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

    def _merge(self, ws_new):
        histo_ws_new = mantid.Rebin(InputWorkspace=ws_new, Params=self._rebinner.current_bin_parameters, PreserveEvents=False)
        self._rebinner.checkpoint[-1].append(ws_new)
        self._rebinner.histo_checkpoint[-1].append(histo_ws_new)
        bin_boundaries = self._rebinner.get_bin_boundaries()
        bin_values = self._rebinner.get_bin_values()

        self._rebinner.update_result(bin_boundaries, bin_values)

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
