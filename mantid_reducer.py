import threading
from collections import deque
import time
from copy import deepcopy

import mantid.simpleapi as mantid
from mantid.api import WorkspaceFactory
from mantid.api import AnalysisDataService
from mantid.api import StorageMode
from mpi4py import MPI

mantid.config['MultiThreaded.MaxCores'] = '1'

comm = MPI.COMM_WORLD

if comm.Get_rank() != 0:
    mantid.ConfigService.setConsoleLogLevel(0)


class MantidReducer(object):
    def __init__(self):
        self.data = deque()
        self.index = 0

    def reduce(self, event_data):
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
        # TODO: ADS issues, see Mantid issue #14120. CAn we keep this out of ADS?
        name = 'summed-{}'.format(self.index)
        self.index += 1
        mantid.SumSpectra(InputWorkspace=ws, OutputWorkspace=name)
        out = AnalysisDataService[name]
        self.data.append(out)


class MantidMerger(threading.Thread):
    def __init__(self, reducer, rebinner):
        threading.Thread.__init__(self)
        self.daemon = True
        self._reducer = reducer
        self._rebinner = rebinner

    def run(self):
        while True:
            while not self._reducer.data:
                time.sleep(0.1)
            ws_new = self._reducer.data.popleft()

            self._rebinner.wsLock.acquire()
            # TODO: use Mantid to compare bin sizes?
            if self._rebinner.current_bin_parameters != '0.4,0.1,5':
                # TODO: we should probably move the Rebin outside the lock (but take care when checking bin params!)
                mantid.Rebin(InputWorkspace=ws_new, OutputWorkspace=ws_new, Params=self._rebinner.current_bin_parameters)
            self._rebinner.ws += ws_new
            AnalysisDataService.Instance().remove(ws_new.name())
            bin_boundaries = deepcopy(self._rebinner.ws.readX(0))
            bin_values = deepcopy(self._rebinner.ws.readY(0))
            self._rebinner.wsLock.release()

            # TODO: can this lead to race conditions with update from within rebinner?
            self._rebinner.update_result(bin_boundaries, bin_values)


class MantidRebinner(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.wsLock = threading.Lock()
        self.resultLock = threading.Lock()
        self.bin_boundaries = None
        self.bin_values = None
        self.current_bin_parameters = '0.4,0.1,5'
        self._target_bin_parameters = None
        self._rebinEvent = threading.Event()
        self._init_workspace()

    def run(self):
        while True:
            self._rebinEvent.wait()
            self._rebinEvent.clear()

            self.wsLock.acquire()
            self.current_bin_parameters = self._target_bin_parameters
            mantid.Rebin(InputWorkspace=self.ws, OutputWorkspace=self.ws, Params=self.current_bin_parameters)
            bin_boundaries = deepcopy(self.ws.readX(0))
            bin_values = deepcopy(self.ws.readY(0))
            self.wsLock.release()

            self.update_result(bin_boundaries, bin_values)

    def get_parameter_dict(self):
        return {'bin_parameters':(self.set_bin_parameters, 'string')}

    def set_bin_parameters(self, bin_parameters):
        self._target_bin_parameters = str(bin_parameters)
        self._rebinEvent.set()

    def update_result(self, bin_boundaries, bin_values):
        self.resultLock.acquire()
        self.bin_boundaries = bin_boundaries
        self.bin_values = sum(comm.gather(bin_values, root=0))
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
