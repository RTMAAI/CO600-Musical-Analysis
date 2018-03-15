""" HIERARCHY MODULE

"""
from rtmaii.coordinator import Coordinator
from rtmaii.worker import Worker

class Hierarchy(object):
    """ Builds a hierarchy for the musical analysis tasks.

    """
    def __init__(self, config):
        self.config = config
        self.root = {
            'peer_list': [],
            'channels': []
        }
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

        self.root['thread'] = new_node('RootCoordinator', {'config': self.config, 'peer_list': self.root['peer_list']})

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
            self.add_node('GenrePredictorWorker', 'SpectrogramCoordinator', **{'sampling_rate' : sampling_rate})

        for channel in self.root['channels']:
            for node_name, node in channel.items():
                if hasattr(node, 'peer_list'):
                    if len(node['peer_list']) <= 0:
                        print(node_name)
                        self.remove_node(node_name)

    def update_nodes(self):
        """ Propagate updated config settings to nodes of Hierarchy. """
        self.root['thread'].update_attributes()
        for channel in range(self.channels):
            for peer in channel:
                pass
                # peer['thread'].update_attributes() Need to add an update method to workers/coordinators.

    def add_node(self, node_name, parent=None, **kwargs):
        """ Add a new node to the hierarchy on each channel tree. """
        for channel in range(self.channels):
            channel_hierarchy = self.root['channels'][channel]
            kwargs['channel_id'] = channel
            channel_hierarchy[node_name] = {
                'thread': new_node(node_name, kwargs)
            }
            if 'peer_list' in kwargs:
                channel_hierarchy[node_name]['peer_list'] = kwargs['peer_list']
            if parent:
                channel_hierarchy[parent]['peer_list'].append(channel_hierarchy[node_name]['thread'])
            else:
                channel_hierarchy['root_peers'].append(channel_hierarchy[node_name]['thread'])

    def remove_node(self, node_name):
        """ Remove a node from the hierarchy tasks. """
        for channel in range(self.channels):
            node = self.root['channels'][channel][node_name]
            if hasattr(node, 'peer_list'):
                for peer in node['peer_list']:
                    self.remove_node(peer.__name__)

    def put(self, data):
        """ Push data to root node of hierarchy. """
        self.root['thread'].queue.put(data)

COORDINATORS = {subclass.__name__ : subclass for subclass in Coordinator.__subclasses__()}
WORKERS = {subclass.__name__ : subclass for subclass in Worker.__subclasses__()}
NODES = {**COORDINATORS, **WORKERS}

def new_node(node_class, kwargs):
    """ Create a new node of the given type.
        The node must inherit from either a worker or coordinator.
    """
    if node_class in NODES:
        return NODES[node_class](**kwargs)
    else:
        raise ValueError("{} Class not found.".format(node_class))
