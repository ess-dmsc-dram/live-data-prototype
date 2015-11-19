import mantid.simpleapi as mantid

from transition import Transition


class MantidRebinTransition(Transition):
    def __init__(self, parent):
        self.bin_parameters = '0.4,0.1,5'
        super(MantidRebinTransition, self).__init__([parent])

    def _do_transition(self, data):
        if data is None:
            return data
        tmp = mantid.Rebin(data, Params=self.bin_parameters, PreserveEvents=False)
        return tmp
