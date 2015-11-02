from collections import deque


class DefaultCommandProcessor(object):
    def process(self, key, argument, parameter_dict):
        parameter_dict[key][0](argument)


class QueueingCommandProcessor(object):
    def __init__(self):
        self._command_queue = deque()

    def __len__(self):
        return len(self._command_queue)

    def get(self):
        return self._command_queue.popleft()

    def process(self, key, argument, parameter_dict):
        self._command_queue.append((key, argument))
