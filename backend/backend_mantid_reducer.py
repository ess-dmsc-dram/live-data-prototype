import threading
from copy import deepcopy
import time

import numpy
from mpi4py import MPI

from backend_worker import BackendWorker

import mantid.simpleapi as mantid
from mantid.api import WorkspaceFactory
from mantid.api import AnalysisDataService
from mantid.api import StorageMode

mantid.config['MultiThreaded.MaxCores'] = '1'
#if MPI.COMM_WORLD.Get_rank() != 0:
mantid.ConfigService.setConsoleLogLevel(0)



class BackendMantidRebinner(object):
    def __init__(self):
        self._comm = MPI.COMM_WORLD
        self.resultLock = threading.Lock()
        self.bin_boundaries = None
        self.bin_values = None
        self.current_bin_parameters = '0.4,0.1,5'
        self._target_bin_parameters = None
        self._init_workspace()

    def rebin(self):
        self.current_bin_parameters = self._target_bin_parameters
        mantid.Rebin(InputWorkspace=self.ws, OutputWorkspace='accumulated_binned', Params=self.current_bin_parameters, PreserveEvents=False)
        self.histo_ws = AnalysisDataService['accumulated_binned']
        bin_boundaries = deepcopy(self.histo_ws.readX(0))
        bin_values = deepcopy(self.histo_ws.readY(0))

        self.update_result(bin_boundaries, bin_values)

    def get_parameter_dict(self):
        return {'bin_parameters':(self.set_bin_parameters, 'string')}

    def set_bin_parameters(self, bin_parameters):
        self._target_bin_parameters = str(bin_parameters)

    def update_result(self, bin_boundaries, bin_values):
        self.resultLock.acquire()
        self.bin_boundaries = bin_boundaries
        gathered = self._comm.gather(bin_values, root=0)
        if self._comm.Get_rank() == 0:
            self.bin_values = sum(gathered)
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
        mantid.SumSpectra(InputWorkspace=tmp, OutputWorkspace='accumulated')
        mantid.DeleteWorkspace(Workspace='tmp')
        self.ws = AnalysisDataService['accumulated']
        mantid.Rebin(InputWorkspace=self.ws, OutputWorkspace='accumulated_binned', Params=self.current_bin_parameters, PreserveEvents=False)
        self.histo_ws = AnalysisDataService['accumulated_binned']


class BackendMantidReducer(BackendWorker):
    def __init__(self, data_queue_in, rebinner):
        BackendWorker.__init__(self)
        self._data_queue_in = data_queue_in
        self._rebinner = rebinner
        self._packet_index = 0
        self._bin_parameters = '0.4,0.1,5'

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
        event_data = numpy.frombuffer(self._data_queue_in.get(), dtype={'names':['detector_id', 'tof'], 'formats':['int32','float32']})

        reduced = self._reduce(event_data)
        self._merge(reduced)

        return True

    def _reduce(self, event_data):
        ws = WorkspaceFactory.Instance().create("EventWorkspace", 1, 1, 1);
        AnalysisDataService.Instance().addOrReplace('POWDIFF_test', ws)
        ws =  AnalysisDataService['POWDIFF_test']
        mantid.LoadInstrument(Workspace=ws, Filename='/home/simon/data/fake_powder_diffraction_data/POWDIFF_Definition.xml')
        ws.padSpectra()
        ws.getAxis(0).setUnit('tof')
        ws.setStorageMode(StorageMode.Distributed)
        for i in event_data:
            ws.getEventList(int(i[0])).addEventQuickly(float(i[1]))
        mantid.ConvertUnits(InputWorkspace=ws, OutputWorkspace=ws, Target='dSpacing')
        mantid.Rebin(InputWorkspace=ws, OutputWorkspace=ws, Params='0.4,0.1,5')
        # TODO: ADS issues, see Mantid issue #14120. Can we keep this out of ADS?
        name = 'summed-{}'.format(self._packet_index)
        self._packet_index += 1
        mantid.SumSpectra(InputWorkspace=ws, OutputWorkspace=name)
        return AnalysisDataService[name]

    def _merge(self, ws_new):
        histo_ws_new = mantid.Rebin(InputWorkspace=ws_new, Params=self._rebinner.current_bin_parameters, PreserveEvents=False)
        self._rebinner.ws += ws_new
        self._rebinner.histo_ws += histo_ws_new
        AnalysisDataService.Instance().remove(ws_new.name())
        AnalysisDataService.Instance().remove(histo_ws_new.name())
        bin_boundaries = self._rebinner.histo_ws.readX(0)
        bin_values = self._rebinner.histo_ws.readY(0)

        self._rebinner.update_result(bin_boundaries, bin_values)

    def get_parameter_dict(self):
        return {'bin_parameters':'str'}

    @property
    def bin_parameters(self):
        return self._bin_parameters

    @bin_parameters.setter
    def bin_parameters(self, parameters):
        self._bin_parameters = parameters
        self._rebinner.set_bin_parameters(parameters)
        self._rebinner.rebin()
