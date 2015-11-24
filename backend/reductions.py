import mantid.simpleapi as mantid
from mantid.api import AnalysisDataService


mantid.config['MultiThreaded.MaxCores'] = '1'
#if MPI.COMM_WORLD.Get_rank() != 0:
mantid.ConfigService.setConsoleLogLevel(0)


class Reduction(object):
    def reduce(self, input_name, output_name):
        raise RuntimeError('Reduction not implemented. Subclass "Reduction" and implement "reduce()".')


class BasicPowderDiffraction(Reduction):
    def reduce(self, input_name, output_name):
        mantid.ConvertUnits(InputWorkspace=input_name, OutputWorkspace=input_name, Target='dSpacing')
        mantid.Rebin(InputWorkspace=input_name, OutputWorkspace=input_name, Params='0.4,0.1,5')
        mantid.SumSpectra(InputWorkspace=input_name, OutputWorkspace=output_name)
        return AnalysisDataService[output_name]
