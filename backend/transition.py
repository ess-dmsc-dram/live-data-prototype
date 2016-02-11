import weakref

from checkpoint import Checkpoint
from checkpoint import DataCheckpoint
from checkpoint import CompositeCheckpoint
from checkpoint import coiterate
from mantid_workspace_checkpoint import MantidWorkspaceCheckpoint


class Transition(object):
    def __init__(self, parents = []):
        # TODO merge inputs into CompositeCheckpoint? No! They may have nothing to do with each other
        # TODO move such an init to child classes? i.e., child defines what outputs it has!
        # no.. just replace this later by appropriate CompositeCheckpoint
        # TODO would it make sense to init this as Checkpoint() instead?
        self._parents = []
        self._checkpoint = None
        self._transitions = []
        self._accumulate_data = False
        for p in parents:
            # We keep a *weakref* to upstream checkpoints to break cyclic references.
            self._parents.append(weakref.ref(p))
            p._add_transition(self)
        self.trigger_rerun()

    @property
    def accumulate_data(self):
        return self._accumulate_data

    @accumulate_data.setter
    def accumulate_data(self, accumulate):
        self._accumulate_data = bool(accumulate)

    def get_checkpoint(self):
        return self._checkpoint

    def _get_parent_checkpoint_dict(self):
        checkpoints = [ p().get_checkpoint() for p in self._parents ]
        return dict(zip(self._get_parent_names(), checkpoints))

    def trigger_update(self, update):
        can_update = self._can_do_updates()
        data = self._get_parent_checkpoint_dict()
        data.update(update)
        result = self._trigger(can_update, data.values())
        self._trigger_child_update(result)
        # We return the result in case the caller needs it for some reason.
        return result

    def trigger_rerun(self):
        can_update = False
        data = self._get_parent_checkpoint_dict()
        self._trigger(can_update, data.values())
        self._trigger_child_rerun()

    def get_name(self):
        return 'transition-{}'.format(id(self))

    def _get_parent_names(self):
        return [ p().get_name() for p in self._parents ]

    def _trigger(self, can_update, data):
        if data:
            # TODO handle multiple input checkpoints
            out_update = self._clone_checkpoint_structure(data[0])
            if self._accumulate_data:
                self._checkpoint = self._clone_checkpoint_structure(data[0], self._checkpoint)
            else:
                self._checkpoint = out_update
        else:
            out_update = self._create_checkpoint()
            if self._accumulate_data:
                self._checkpoint = self._create_checkpoint()
            else:
                self._checkpoint = out_update
        mastertree = None
        if len(data) > 0:
            mastertree = data[0]
        for i in coiterate(mastertree, tuple(data[1:]) + (self._checkpoint, out_update)):
            self._do_trigger(can_update, i)

        return out_update

    def _clone_checkpoint_structure(self, checkpoint_in, checkpoint_out=None):
        if isinstance(checkpoint_in, CompositeCheckpoint):
            # We are not at a leaf, make sure out is composite of correct length
            if not isinstance(checkpoint_out, CompositeCheckpoint):
                out = CompositeCheckpoint()
                for i in checkpoint_in:
                    out.add_checkpoint(self._clone_checkpoint_structure(i))
                return out
            elif len(checkpoint_in) > len(checkpoint_out):
                for i in range(len(checkpoint_out), len(checkpoint_in)):
                    checkpoint_out.add_checkpoint(self._clone_checkpoint_structure(checkpoint_in[i]))
                return checkpoint_out
            elif len(checkpoint_in) != len(checkpoint_out):
                out = CompositeCheckpoint()
                for i in checkpoint_in:
                    out.add_checkpoint(self._clone_checkpoint_structure(i))
                return out
        else:
            # We are at a leaf
            if checkpoint_out is None:
                return self._create_checkpoint()
        return checkpoint_out

    def _do_trigger(self, can_update, data):
        out = data[-2]
        out_update = data[-1]
        inputs = data[:-2]
        if all(inputs):
            result = self._do_transition(inputs)
            # When not accumulating out data, out refers to same object
            # as out_update, so we do not modify both.
            if not out is out_update:
                if can_update:
                    out.append(result)
                else:
                    out.replace(result)
            out_update.replace(result)

    def _add_transition(self, transition):
        self._transitions.append(transition)

    def _trigger_child_update(self, update):
        for t in self._transitions:
            t.trigger_update({self.get_name():update})

    def _trigger_child_rerun(self):
        for t in self._transitions:
            t.trigger_rerun()

    def _do_transition(self, data):
        raise RuntimeError('Transition._do_transition() must be implemented in child classes!')

    def _can_do_updates(self):
        """Can this transition work on data updates, i.e., partial data?
        Reimplement this in child classes to change the default (True)"""
        return True

    def _create_checkpoint(self):
        return DataCheckpoint()


class IdentityTransition(Transition):
    def __init__(self, parent):
        super(IdentityTransition, self).__init__(parents=[parent])

    def _do_transition(self, data):
        return data[0].data


class UpperCaseTransition(Transition):
    def __init__(self, parent):
        super(UpperCaseTransition, self).__init__(parents=[parent])

    def _do_transition(self, data):
        return data[0].data.upper()
