import json
from threading import Lock

import numpy

from logger import log

from backend_worker import BackendWorker
from reductions import BasicPowderDiffraction

from create_mantid_workspace_from_events_transition import CreateMantidWorkspaceFromEventsTransition
from reductions_transition import ReductionTransition
from mantid_filter_transition import MantidFilterTransition
from mantid_rebin_transition import MantidRebinTransition
from gather_histogram_transition import GatherHistogramTransition


class BackendMantidReducer(BackendWorker):
    def __init__(self, data_queue_in):
        BackendWorker.__init__(self)
        self._lock = Lock()
        self._data_queue_in = data_queue_in
        self._reducer = BasicPowderDiffraction()
        self._filter_pulses = False
        self._create_workspace_from_events_transition = CreateMantidWorkspaceFromEventsTransition()
	self.tree_string = ""
	self.transition_generator_dict = {'Reduction': ['ReductionTransition','self._reducer'], 'MantidFilter': ['MantidFilterTransition'], 'MantidRebin':['MantidRebinTransition'], 'GatherHistogram':['GatherHistogramTransition']}
	self.transition_objects_dict = {'Reduction':[], 'MantidFilter':[], 'MantidRebin':[], 'GatherHistogram':[]}


    def _process_command(self, command):
        setattr(self, command[0], command[1])

    def _can_process_data(self):
        if self._data_queue_in:
            return True
        else:
            return False

    def _process_data(self):
        if not self._data_queue_in:
            return False

        header, data = self._data_queue_in.get()

        if header == 'meta_data':
            return self._process_meta_data(data)
        else:
            return self._process_event_data(data)

    def _process_meta_data(self, data):
        data = json.loads(data)
        self._pulse_time = str(data['pulse_time'])
        payload = data['payload']
        lattice_spacing = float(payload['unit_cell'].split()[0])
        self._create_workspace_from_events_transition.set_log_data({'lattice_spacing':lattice_spacing})
        self._drop_pulse = abs(lattice_spacing - 5.431) > 0.01
        log.debug('Received meta data {}, ignoring.'.format(data['payload']))
        return True

    def _process_event_data(self, data):
        if self._filter_pulses and self._drop_pulse:
            return True
        event_data = numpy.frombuffer(data, dtype={'names':['detector_id', 'tof'], 'formats':['int32','float32']})
        self._lock.acquire()
        self._create_workspace_from_events_transition.process(event_data, self._pulse_time)
        self._lock.release()
        return True

    def get_parameter_dict(self):
        return {'bin_parameters':'str', 'filter_interval_parameters':'str', 'filter_pulses':'bool', 'transition_tree':'string' }

    def add_transition(self, new_transition):
	self.target_transition = ""
	parentID = new_transition.split('-')[0] 
	transition_type = new_transition.split('-')[1] #add in catch error stuff here
	transition_commands_list = self.transition_generator_dict[transition_type] #try catch here?
	potential_reducer = ""
	if len(transition_commands_list) == 2:
	    potential_reducer =","+ transition_commands_list[1]
	self.find_transition(parentID)
	transitionCommand =  transition_commands_list[0]+"(self.target_transition"+ potential_reducer + ")"
	new_transition_object = eval(transitionCommand)
	return new_transition_object, transition_type
   
    def find_transition(self, transition_ID):
	if self._create_workspace_from_events_transition.get_name().split()[1] != transition_ID:
            self.recurse_transition(transition_ID, self._create_workspace_from_events_transition)
        else: self.target_transition = self._create_workspace_from_events_transition

    def recurse_transition(self, transition_ID, initial_transition):
	for transition in initial_transition._transitions:
	   if transition.get_name().split()[1] != transition_ID:
		self.recurse_transition(transition_ID, transition)
	   else:
		self.target_transition = transition

    def tree(self, transition, padding):
        self.tree_string += "\n" +  padding[:-1] + '+-' + transition.get_name()
        padding = padding + ' '
        transitions = []
        transitions = transition._transitions
        for a in transitions:
            self.tree_string += "\n" + padding + '|'
            self.tree(a, padding+"|")
	
    def post_transition_settings(self, new_transition_object, transition_type):
	if transition_type != "MantidRebin":
	    new_transition_object.accumulate_data = True
   
    def _delete_from_dict(self, transition):
	new_dict= {}
	for key, value in self.transition_objects_dict.items():
	    object_list=[]
	    for transition_object in value:
		if transition_object != transition:
		    object_list.append(transition_object)
	    new_dict[key] = object_list	
	self.transition_objects_dict = new_dict


    def _delete_transition_object(self, transition):
	for transitions in transition._transitions:
	    self._delete_transition_object(transitions)
	    self._delete_from_dict(transitions)
	    print "deleting: " + str(transitions)
	    del transitions
		
    def _delete_transition(self, transition_id):
	self.find_transition(transition_id)
	print "this is before dict"
	for values in self.transition_objects_dict.values():
	    print values
	for transitions in self.target_transition._transitions:
	    self._delete_from_dict(transitions)
	self.target_transition._transitions = []
	print "this is after dict"
        for values in self.transition_objects_dict.values():
            print values

    @property
    def transition_tree(self):
	self.tree_string = ""
	self.tree(self._create_workspace_from_events_transition, '')
	self.tree_string += "\n \n REMEMBER '-' separates \n To add new transition '[parentID]-[transitionType]' \n To delete '[transitionID]-DEL' (This will delete all children) \n To update parameters '[transitionID]-[newParams]'"
	return self.tree_string
	
    @transition_tree.setter
    def transition_tree(self, new_transition):
	self._lock.acquire()
	if new_transition.split('-')[1] == 'DEL':
	    self._delete_transition(new_transition.split('-')[0])
	else:
	    new_transition_object, transition_type = self.add_transition(new_transition)
	    self.post_transition_settings(new_transition_object, transition_type)	
	    self.transition_objects_dict[transition_type].append(new_transition_object)

	self._lock.release() #TODO add in automated 'if nothing entered, just set up what is expected' thing

    @property
    def bin_parameters(self):
	bin_parameters_string = ""
	for transition in self.transition_objects_dict['MantidRebin']:
	    bin_parameters_string += "\n" + transition.get_name() +"-" + transition._bin_parameters
	return bin_parameters_string

    @bin_parameters.setter
    def bin_parameters(self, parameters):
        self._lock.acquire()
	transition_ID = parameters.split('-')[0] #make sure to strip spaces from this?
	actual_parameters = parameters.split('-')[1]
	self.find_transition(transition_ID)
        self.target_transition.set_bin_parameters(actual_parameters)
        self._lock.release()

    @property
    def filter_pulses(self):
        return self._filter_pulses

    @filter_pulses.setter
    def filter_pulses(self, filter_pulses):
        self._filter_pulses = filter_pulses
        self._splitting_transition.next()

    @property
    def filter_interval_parameters(self):
	filter_interval_string = ""
       # for transition in self.transition_objects_dict['MantidRebin']:
       #     filter_interval_string += "\n" + transition.get_name() +"-" + transition._interval_parameters
        filter_interval_string = "NOT IMPLEMENTED YET" #TODO
	return filter_interval_string

    @filter_interval_parameters.setter
    def filter_interval_parameters(self, parameters):
        self._lock.acquire()
	transition_ID = parameters.split('-')[0]
	actual_parameters = parameters.split('-')[1]
	self.find_transition(transition_ID)
	self.target_transition.set_interval_parameters(actual_parameters)
        self._lock.release()
