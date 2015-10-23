import mantid.simpleapi as mantid
from mantid.api import WorkspaceFactory
from mantid.api import AnalysisDataService
from mantid.api import StorageMode
from mpi4py import MPI

mantid.config['MultiThreaded.MaxCores'] = '1'


def reduce(event_data):
    ws = WorkspaceFactory.Instance().create("EventWorkspace", 1, 1, 1);
    AnalysisDataService.Instance().addOrReplace('POWDIFF_test', ws)
    #print ws.name()
    #print ws.getNumberHistograms()
    #print ws.getNumberEvents()
    mantid.LoadInstrument(Workspace='POWDIFF_test', Filename='/home/simon/data/fake_powder_diffraction_data/POWDIFF_Definition.xml')
    ws.padSpectra()
    ws.getAxis(0).setUnit('tof')
    ws.setStorageMode(StorageMode.Distributed)
    for i in event_data:
        ws.getEventList(int(i[0])).addEventQuickly(float(i[1]))
    print ws.getNumberHistograms()
    print ws.getNumberEvents()
    mantid.ConvertUnits(InputWorkspace='POWDIFF_test', OutputWorkspace='pd_dspacing', Target='dSpacing')
    mantid.Rebin(InputWorkspace='pd_dspacing', OutputWorkspace='pd_dspacing_regular', Params='0.4,0.0001,5')
    mantid.SumSpectra(InputWorkspace='pd_dspacing_regular', OutputWorkspace='pd_sum')
    out =  AnalysisDataService['pd_sum']
    return out.readX(0), out.readY(0), out.readE(0)




##ws = AnalysisDataService['test']
#print ws.name()
#print ws.getNumberHistograms()
#print ws.getNumberEvents()
#
#print ws.getNumberEvents()
#print ws.getEventList(0).getTofs()
#
#exit()
#
#comm = MPI.COMM_WORLD
##if comm.Get_rank() != 0:
##    ConfigService.setConsoleLogLevel(0)
##else:
##    ConfigService.setConsoleLogLevel(7)
#
##ws2 = CreateSampleWorkspace()
##SortEvents(ws2)
#
#
#ws = mantid.CreateSampleWorkspace(OutputWorkspace='test', WorkspaceType='Event')
##ws = AnalysisDataService.retrieve('test')
#print ws.name()
#print ws.getNumberHistograms()
#print ws.getNumberEvents()
#print ws.getEventList(0).getTofs()[0]
#ws.getEventList(0).clear()
#print ws.getEventList(0).getTofs()[0]
#
#print ws.getEventList(0).getWeights()[0]
#ws.getEventList(0).getWeights()[0] = 42.0
#print ws.getEventList(0).getWeights()[0]
#
#
##scaled = Scale(ws, 2.0)
##rebinned = Rebin(ws, "0.01,-0.01,100")
#
#mantid.SortEvents('test')
#
#
#comm.Barrier()
