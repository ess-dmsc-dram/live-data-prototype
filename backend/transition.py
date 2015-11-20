import weakref

from checkpoint import Checkpoint
from checkpoint import DataCheckpoint
from checkpoint import CompositeCheckpoint
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

    def trigger_update(self, data):
        can_update = self._can_do_updates()
        # TODO Make this work for generic dict
        result = self._trigger(can_update, self._build_input_dict(data))
        self._trigger_child_update(result)

    def trigger_rerun(self):
        can_update = False
        #TODO can we ignore the result?
        empty_dict = {}
        if self._parents:
            empty_dict = self._parents[0]().get_checkpoint().zip_data_with_key(None, self._parents[0]().get_checkpoint().get_data())
        self._trigger(can_update, self._build_input_dict(empty_dict))
        self._trigger_child_rerun()

    def _build_input_dict(self, update):
        # TODO extend this for non-matching trees?
        parent_data = [ p().get_checkpoint().get_data() for p in self._parents ]
        out = self._recurse_build_input_dict(self._get_parent_names(), parent_data, update)
        #print parent_data, update, out
        return out

    def _recurse_build_input_dict(self, parent_names, parent_data, update):
        if isinstance(update, dict):
            out = dict(zip(parent_names, parent_data))
            out.update(update)
            return out
        else:
            #print 'parent {} {}'.format(parent_names, parent_data[0])
            # TODO Fix this for multiple parents! How to zip properly??
            return [ self._recurse_build_input_dict(parent_names, [p], u) for p, u in zip(parent_data[0], update) ]

    def _get_name(self):
        return 'parent-{}'.format(id(self))

    def _get_parent_names(self):
        return [ 'parent-{}'.format(id(p())) for p in self._parents ]

    def _trigger(self, can_update, data):
        self._checkpoint = self._make_composite_if_necessary(data, self._checkpoint)
        return self._recurse_trigger(can_update, data, self._checkpoint)

    def _make_composite_if_necessary(self, data, checkpoint_out):
        if isinstance(data, dict):
            # We are at a leaf
            if checkpoint_out is None:
                return self._create_checkpoint()
        else:
            # We are not at a leaf, make sure out is composite of correct length
            if not isinstance(checkpoint_out, CompositeCheckpoint):
                return CompositeCheckpoint(leaf_count=len(data))
            elif len(data) != len(checkpoint_out):
                # TODO non-destructive resize
                return CompositeCheckpoint(leaf_count=len(data))
        return checkpoint_out

    def _recurse_trigger(self, can_update, data, checkpoint_out):
        if isinstance(data, list):
            result = []
            for i in range(len(data)):
                checkpoint_out[i] = self._make_composite_if_necessary(data[i], checkpoint_out[i])
                result.append(self._recurse_trigger(can_update, data[i], checkpoint_out[i]))
            return result
        else:
            return self._do_trigger(can_update, data, checkpoint_out)

    def _do_trigger(self, can_update, data, checkpoint_out):
        if data.values().count(None) != len(data.values()):
            result = self._do_transition(data)
            if can_update:
                checkpoint_out.append(result)
            else:
                checkpoint_out.replace(result)
            return result
        else:
            return None

    def _add_transition(self, transition):
        self._transitions.append(transition)

    def _trigger_child_update(self, data):
        for t in self._transitions:
            t.trigger_update(self.get_checkpoint().zip_data_with_key(self._get_name(), data))
            #t.trigger_update({'parent-{}'.format(id(self)):data})

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
        self._trigger_child_update()

    def _do_transition(self, data):
        return DataCheckpoint()


class IdentityTransition(Transition):
    def __init__(self, parent):
        super(IdentityTransition, self).__init__(parents=[parent])

    def _do_transition(self, data):
        return data.values()[0]


class UpperCaseTransition(Transition):
    def __init__(self, parent):
        super(UpperCaseTransition, self).__init__(parents=[parent])

    def _do_transition(self, data):
        return data.values()[0].upper()
