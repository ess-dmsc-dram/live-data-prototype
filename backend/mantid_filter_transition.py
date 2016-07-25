import mantid.simpleapi as mantid
from mantid.api import AnalysisDataService

from checkpoint import CompositeCheckpoint
from mantid_workspace_checkpoint import MantidWorkspaceCheckpoint
from mantid_workspace_transition import MantidWorkspaceTransition


class MantidFilterTransition(MantidWorkspaceTransition):
    def __init__(self, parent):
        self._value_name = 'lattice_spacing'
        self._value_min = 1.0
        self._value_max = 10.0
        self._value_step = 1.0
        super(MantidFilterTransition, self).__init__(parents=[parent])

    def set_interval_parameters(self, interval_parameters):
        params = [ float(i) for i in interval_parameters.split(',') ]
        self._value_min = params[0]
        self._value_step = params[1]
        self._value_max = params[2]
        # TODO probably this is not thread safe... this is called from another thread!?
        self.trigger_rerun()

    def _do_transition(self, data):
        ws = data[0].data
        splitws, infows = mantid.GenerateEventsFilter(
                InputWorkspace=ws,
                LogName=self._value_name,
                MinimumLogValue=self._value_min,
                MaximumLogValue=self._value_max,
                LogValueInterval=self._value_step)
        mantid.FilterEvents(
                InputWorkspace=ws,
                SplitterWorkspace=splitws,
                InformationWorkspace=infows,
                OutputWorkspaceBaseName='tempsplitws',
                GroupWorkspaces=True,
                FilterByPulseTime=True,
                CorrectionToSample="Direct",
                IncidentEnergy=3,
                OutputWorkspaceIndexedFrom1=False,
                SpectrumWithoutDetector = "Skip",
                OutputTOFCorrectionWorkspace='mock')
        result = [None]*self._step_count()
        for x in AnalysisDataService.Instance()["tempsplitws"]:
            try:
                 index = int(x.name()[12:])
                 result[index] = x
            except:
                pass

        return result

    def _create_checkpoint(self):
        return CompositeCheckpoint(MantidWorkspaceCheckpoint, self._step_count())

    def _step_count(self):
        # +1 to avoid rounding issues
        return int((self._value_max - self._value_min)/self._value_step) + 1
