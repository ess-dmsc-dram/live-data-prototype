import mantid.simpleapi as mantid
from mantid.api import WorkspaceFactory
from mantid.api import AnalysisDataService
from mantid.api import StorageMode
from mpi4py import MPI

mantid.config['MultiThreaded.MaxCores'] = '1'

comm = MPI.COMM_WORLD

if comm.Get_rank() != 0:
    mantid.ConfigService.setConsoleLogLevel(0)


def reduce(event_data):
    ws = WorkspaceFactory.Instance().create("EventWorkspace", 1, 1, 1);
    AnalysisDataService.Instance().addOrReplace('POWDIFF_test', ws)
    mantid.LoadInstrument(Workspace='POWDIFF_test', Filename='/home/simon/data/fake_powder_diffraction_data/POWDIFF_Definition.xml')
    ws.padSpectra()
    ws.getAxis(0).setUnit('tof')
    ws.setStorageMode(StorageMode.Distributed)
    for i in event_data:
        ws.getEventList(int(i[0])).addEventQuickly(float(i[1]))
    mantid.ConvertUnits(InputWorkspace='POWDIFF_test', OutputWorkspace='pd_dspacing', Target='dSpacing')
    mantid.Rebin(InputWorkspace='pd_dspacing', OutputWorkspace='pd_dspacing_regular', Params='0.4,0.0001,5')
    mantid.SumSpectra(InputWorkspace='pd_dspacing_regular', OutputWorkspace='pd_sum')
    out =  AnalysisDataService['pd_sum']
    return out.readX(0), out.readY(0), out.readE(0)
