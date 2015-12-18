import mantid.simpleapi as mantid
from mantid.api import WorkspaceFactory
from mantid.api import AnalysisDataService
from mantid.kernel import DateAndTime

from checkpoint import DataCheckpoint
from mantid_workspace_checkpoint import MantidWorkspaceCheckpoint
from mantid_workspace_transition import MantidWorkspaceTransition


class CreateMantidWorkspaceFromEventsTransition(MantidWorkspaceTransition):
    def __init__(self):
        self._log_data = {}
        self._number_of_spectra = self._get_number_of_spectra_from_instrument()
        super(CreateMantidWorkspaceFromEventsTransition, self).__init__(parents=[])

    def set_log_data(self, data):
        self._log_data = dict(data)

    def process(self, event_data, pulse_time):
        update = DataCheckpoint()
        update._data = (event_data, pulse_time)
        self.trigger_update({'no-parent':update})

    def _do_transition(self, data):
        event_data, pulse_time = data[0].data
        ws = WorkspaceFactory.Instance().create("EventWorkspace", self._number_of_spectra, 1, 1);
        AnalysisDataService.Instance().addOrReplace('POWDIFF_test', ws)
        ws =  AnalysisDataService['POWDIFF_test']
        mantid.LoadInstrument(Workspace=ws, Filename='/home/simon/data/fake_powder_diffraction_data/POWDIFF_Definition.xml', RewriteSpectraMap=True)
        ws.getAxis(0).setUnit('tof')
        for i in event_data:
            ws.getEventList(int(i[0])).addEventQuickly(float(i[1]), DateAndTime(pulse_time))
        self._add_log_data(ws, pulse_time)
        return ws

    def _add_log_data(self, ws, pulse_time):
        mantid.AddSampleLog(ws, LogName='start_time', LogText=str(DateAndTime(pulse_time)))
        for key, value in self._log_data.items():
            mantid.AddTimeSeriesLog(ws, Name=key, Time=str(DateAndTime(pulse_time)), Value=value)

    def _get_number_of_spectra_from_instrument(self):
        # We create a helper workspace to obtain the number of detectors.
        ws = mantid.CreateSimulationWorkspace(Instrument='/home/simon/data/fake_powder_diffraction_data/POWDIFF_Definition.xml', BinParams='1,0.5,2')
        return ws.getNumberHistograms()
