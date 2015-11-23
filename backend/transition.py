import weakref

from checkpoint import Checkpoint
from checkpoint import DataCheckpoint
from checkpoint import CompositeCheckpoint
from checkpoint import coiterate
from mantid_workspace_checkpoint import MantidWorkspaceCheckpoint


class Transition(object):
    def __init__(self, create_checkpoint = lambda: DataCheckpoint(), parents = []):
        # TODO merge inputs into CompositeCheckpoint? No! They may have nothing to do with each other
        # TODO move such an init to child classes? i.e., child defines what outputs it has!
        # no.. just replace this later by appropriate CompositeCheckpoint
        # TODO would it make sense to init this as Checkpoint() instead?
        self._parents = []
        self._create_checkpoint = create_checkpoint
        self._checkpoint = None
        self._transitions = []
        for p in parents:
            # We keep a *weakref* to upstream checkpoints to break cyclic references.
            self._parents.append(weakref.ref(p))
            p._add_transition(self)
        self.trigger_rerun()

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

    def _get_name(self):
        return 'parent-{}'.format(id(self))

    def _get_parent_names(self):
        return [ 'parent-{}'.format(id(p())) for p in self._parents ]

    def _trigger(self, can_update, data):
        if data:
            # TODO handle multiple input checkpoints
            self._checkpoint = self._clone_checkpoint_structure(data[0], self._checkpoint)
            out_update = self._clone_checkpoint_structure(data[0])
        else:
            self._checkpoint = self._create_checkpoint()
            out_update = self._create_checkpoint()
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
            elif len(checkpoint_in) != len(checkpoint_out):
                # TODO non-destructive resize
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
            if can_update:
                out.append(result)
            else:
                out.replace(result)
            out_update.replace(result)

    def _add_transition(self, transition):
        self._transitions.append(transition)

    def _trigger_child_update(self, update):
        for t in self._transitions:
            t.trigger_update({'parent-{}'.format(id(self)):update})

    def _trigger_child_rerun(self):
        for t in self._transitions:
            t.trigger_rerun()

    def _do_transition(self, data):
        raise RuntimeError('Transition._do_transition() must be implemented in child classes!')

    def _can_do_updates(self):
        """Can this transition work on data updates, i.e., partial data?
        Reimplement this in child classes to change the default (True)"""
        return True

    def _get_output_checkpoint_type(self, input_checkpoint):
        return MantidWorkspaceCheckpoint
        # TODO How can we do this if we do not have checkpoint but underlying data?
        #return type(input_checkpoint)


# TODO This class is badly broken and just here for testing. Get rid of it as soon as possible!
class FromCheckpointTransition(Transition):
    def __init__(self, checkpoint):
        super(FromCheckpointTransition, self).__init__(parents=[])
        self._checkpoint = checkpoint
        self._trigger_child_rerun()

    def append(self, data):
        self._checkpoint[-1].append(data)
        leaf_type = type(self._checkpoint[-1])
        update = leaf_type()
        update.replace(data)
        update_tree = CompositeCheckpoint(leaf_type, len(self._checkpoint))
        update_tree[-1] = update
        self._trigger_child_update(update_tree)

    def _do_transition(self, data):
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
