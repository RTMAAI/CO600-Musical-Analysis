""" HIERARCHY MODULE

"""
import logging
from rtmaii.coordinator import Coordinator
from rtmaii.worker import Worker
from rtmaii.exporter import Exporter

LOGGER = logging.getLogger()
class Hierarchy(object):
    """ Builds a hierarchy for the musical analysis tasks.

    """
    def __init__(self, config, custom_tasks):
        self.config = config
        self.root = {
            'peer_list': [],
            'channels': []
        }
        self.custom_tasks = custom_tasks
        self.channels = 1 if config.get_config('merge_channels') else config.get_config('channels')
        self.reset_hierarchy()

    def reset_hierarchy(self):
        """ Reset hierarchy back to library default tasks based on config settings. """
        pitch_algorithm = self.config.get_config('pitch_algorithm')
        sampling_rate = self.config.get_config('sampling_rate')
        tasks = self.config.get_config('tasks') # The tasks that have been enabled.

        for channel in range(self.channels):
            self.root['channels'].append({'root_peers': []})
            self.root['peer_list'].append(self.root['channels'][channel]['root_peers'])

        self.root['thread'] = node_factory('RootCoordinator', {'config': self.config, 'peer_list': self.root['peer_list']})

        ## COORDINATORS ##
        self.add_node('FrequencyCoordinator', **{'config': self.config, 'peer_list': []})
        self.add_node('SpectrumCoordinator', 'FrequencyCoordinator', **{'config': self.config, 'peer_list': []})
        self.add_node('BPMCoordinator', **{'config': self.config, 'peer_list': []})
        self.add_node('FFTSCoordinator', **{'config': self.config, 'peer_list': []})
        self.add_node('SpectrogramCoordinator', 'FFTSCoordinator',  **{'config': self.config, 'peer_list': [], 'sampling_rate': sampling_rate})

        if tasks['beat']:
            self.add_node('BPMWorker', 'BPMCoordinator', **{'sampling_rate' : sampling_rate})
        if tasks['bands']:
            self.add_node('BandsWorker', 'SpectrumCoordinator', **{'bands_of_interest' : self.config.get_config('bands'), 'sampling_rate' : sampling_rate})
        if tasks['pitch']:
            if pitch_algorithm == 'hps':
                self.add_node('HPSWorker', 'SpectrumCoordinator', **{'sampling_rate' : sampling_rate})
            elif pitch_algorithm == 'zero-crossings':
                self.add_node('ZeroCrossingWorker', 'FrequencyCoordinator', **{'sampling_rate' : sampling_rate})
            elif pitch_algorithm == 'fft':
                self.add_node('FFTWorker', 'SpectrumCoordinator', **{'sampling_rate' : sampling_rate})
            else:
                self.add_node('AutoCorrelationWorker', 'FrequencyCoordinator', **{'sampling_rate' : sampling_rate})
        if tasks['genre']:
            exporter_list = []
            self.add_node('GenrePredictorWorker', 'SpectrogramCoordinator', **{'sampling_rate' : sampling_rate, 'exporter': exporter_list})
            if tasks['export_spectrograms']:
                    exporter_list.append(Exporter())

        for task in self.custom_tasks:
            self.add_node(task['class'], task['parent'], **task['kwargs'])

        self.clean_hierarchy()

    def clean_hierarchy(self):
        """ Removes any unused nodes from the hierarchy, saving processing time. """
        node_removed = True
        while node_removed:
            node_removed = self.remove_empty_coordinators()

    def remove_empty_coordinators(self):
        """ If there are no peers in a coordinator's peer list remove them. """
        for node_name, node in self.root['channels'][0].items(): # Only need to remove from one side as function will clear both.
            if 'peer_list' in node:
                if len(node['peer_list']) <= 0:
                    self.remove_node(node_name)
                    return True
        return False

    def update_nodes(self):
        """ Propagate updated config settings to nodes of Hierarchy. """
        self.root['thread'].update_attributes()
        LOGGER.debug('Updating hierarchy nodes, with latest config.')
        for channel in range(self.channels):
            for peer in channel.items():
                peer['thread'].update_attributes()

    def add_custom_node(self, node_name, parent=None, **kwargs):
        self.custom_tasks.append({'class': node_name, 'parent': parent, 'kwargs': kwargs})
        self.add_node(node_name, parent=None, **kwargs)

    def add_node(self, node_name, parent=None, **kwargs):
        """ Add a new node to the hierarchy on each channel tree. """
        for channel in range(self.channels):
            channel_hierarchy = self.root['channels'][channel]
            kwargs['channel_id'] = channel
            channel_hierarchy[node_name] = {
                'thread': node_factory(node_name, kwargs)
            }
            if 'peer_list' in kwargs:
                channel_hierarchy[node_name]['peer_list'] = kwargs['peer_list']
            if parent:
                try:
                    channel_hierarchy[parent]['peer_list'].append(channel_hierarchy[node_name]['thread'])
                except KeyError:
                    print('Could not find specified parent node {} in hierarchy.'.format(parent))
                    raise
            else:
                channel_hierarchy['root_peers'].append(channel_hierarchy[node_name]['thread'])

    def remove_node(self, node_name):
        """ Remove a node from the hierarchy tasks. """
        for channel in range(self.channels):

            node = self.root['channels'][channel][node_name]

            # Remove any children from node, if deleting a node with children.
            if 'peer_list' in node:
                for peer in node['peer_list']:
                    LOGGER.debug('Removing child node %s of %s from channel hierarchy %d', peer, node_name, channel)
                    self.remove_node(peer.__class__.__name__)

            # Remove node from parent.
            for nodename, value in self.root['channels'][channel].items():
                if 'peer_list' in value:
                    if node['thread'] in value['peer_list']:
                        self.root['channels'][channel][nodename]['peer_list'].remove(node['thread'])

            del self.root['channels'][channel][node_name]
            LOGGER.debug('Removed node %s from channel hierarchy %d', node_name, channel)

    def put(self, data):
        """ Push data to root node of hierarchy. """
        self.root['thread'].queue.put(data)

def node_factory(node_class, kwargs):
    """ Create a new node of the given type.
        The node must inherit from either a worker or coordinator base class.
    """
    coordinators = {subclass.__name__ : subclass for subclass in Coordinator.__subclasses__()}
    workers = {subclass.__name__ : subclass for subclass in Worker.__subclasses__()}
    nodes = {**coordinators, **workers}
    if node_class in nodes:
        return nodes[node_class](**kwargs)
    else:
        raise ValueError("{} does not inherit from Worker or Coordinator.".format(node_class))
