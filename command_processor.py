from collections import deque


class DefaultCommandProcessor(object):
    def process(self, setter, argument):
        setter(argument)


class QueueingCommandProcessor(object):
    def __init__(self):
        self._command_queue = deque()

    def __len__(self):
        return len(self._command_queue)

    def get(self):
        return self._command_queue.popleft()

    def process(self, setter, argument):
        self._command_queue.append((setter, argument))
