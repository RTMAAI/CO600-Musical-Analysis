""" HIERARCHY MODULE

    Contains methods for managing the hierarchy of our library.

    NOTE: The new API was added rather late, so isn't fully implemented.
    There are plenty of cases where this could fail to do what a user wants.
    However, the hierarchy should always stay in a valid state.

    LIMITATIONS OF CURRENT IMPLEMENTATION.
    - A node HAS to added to each channel hierarchy for each channel that is being analysed.

"""
import logging
from rtmaii.coordinator import Coordinator
from rtmaii.worker import Worker
from rtmaii.exporter import Exporter

LOGGER = logging.getLogger()

class Hierarchy(object):
    """ Builds a hierarchy for the musical analysis tasks.

    """
    def __init__(self, config, custom_nodes):
        self.config = config
        self.custom_nodes = custom_nodes if custom_nodes else {} # Custom node config, hierarchy will be recreated with these.
        self.reset_hierarchy()

    def reset_hierarchy(self):
        """ Reset hierarchy back to library defaults based on config settings.
            This is quite expensive, as we need to rebuild the entire hierarchy.
            This is mainly reserved for changes with amount of channels being analysed and initial creation.
        """
        self.root = {
            'channels': []
        }
        self.root['thread'] = node_factory('RootCoordinator', **{'config': self.config})
        self.root['peer_list'] = self.root['thread'].peer_list
        self.channels = 1 if self.config.get_config('merge_channels') else self.config.get_config('channels')

        for channel in range(self.channels):
            self.root['channels'].append({'root':{'peer_list': []}})
            self.root['peer_list'].append(self.root['channels'][channel]['root']['peer_list'])

        self.default_hierarchy()
        for key, value in self.custom_nodes.items():
            self.add_node(value['class_name'], key, value['parent'], **value['kwargs'])
        self.clean_hierarchy()

    def default_hierarchy(self):
        """ Create hierarchy tree based on task config provided with the library. """
        pitch_algorithm = self.config.get_config('pitch_algorithm')
        tasks = self.config.get_config('tasks') # The tasks that have been enabled.

        ## COORDINATORS ##
        self.add_node('FrequencyCoordinator')
        self.add_node('SpectrumCoordinator', parent_id='FrequencyCoordinator')
        self.add_node('BPMCoordinator')
        self.add_node('FFTSCoordinator')
        self.add_node('SpectrogramCoordinator', parent_id='FFTSCoordinator')

        ## WORKERS ##
        if tasks['beat']:
            self.add_node('BPMWorker', parent_id='BPMCoordinator')
        if tasks['bands']:
            self.add_node('BandsWorker', parent_id='SpectrumCoordinator')
        if tasks['pitch']:
            if pitch_algorithm == 'hps':
                self.add_node('HPSWorker', parent_id='SpectrumCoordinator')
            elif pitch_algorithm == 'zero-crossings':
                self.add_node('ZeroCrossingWorker', parent_id='FrequencyCoordinator')
            elif pitch_algorithm == 'fft':
                self.add_node('FFTWorker', parent_id='SpectrumCoordinator')
            else:
                self.add_node('AutoCorrelationWorker', parent_id='FrequencyCoordinator')
        if tasks['genre']:
            if tasks['export_spectrograms']:
                args = (Exporter(),)
            self.add_node('GenrePredictorWorker', None, 'SpectrogramCoordinator', *args)

    def clean_hierarchy(self):
        """ Removes any unused nodes from the hierarchy, saving processing time. """
        node_removed = True
        while node_removed:
            node_removed = self.remove_empty_coordinators()

    def remove_empty_coordinators(self):
        """ If there are no peers in a coordinator's peer list remove them.
            NOTE: this is a destructive method!
            i.e. coordinators will be removed if they have an empty peer_list.
            This may be changed, however, a user could easily re-add the coordinator they need.
        """
        for node_id, node in self.root['channels'][0].items():
            # Only need to remove from one channel as remove_node function will clear both.
            if 'thread' in node:
                if hasattr(node['thread'], 'peer_list'):
                    if len(node['thread'].get_peer_list()) <= 0:
                        self.remove_node(node_id)
                        return True
        return False # No nodes were removed this iteration.

    def update_nodes(self):
        """ Propagate updated config settings to nodes of Hierarchy. """
        self.root['thread'].reset_attributes()
        LOGGER.debug('Updating hierarchy nodes, with latest config.')
        for channel in self.root['channels']:
            for _, peer in channel.items():
                if 'thread' in peer:
                    peer['thread'].reset_attributes()

    def add_custom_node(self, class_name, node_id=None, parent=None, *args, **kwargs):
        """ API Based method, stores custom nodes in list, so they can be readded if the hierarchy is reset. """
        uid = node_id if node_id else class_name
        if uid in self.custom_nodes:
            raise AttributeError('Node id already exists in hierarchy, please use a unique ID.')

        self.custom_nodes[node_id] = {'class': class_name, 'parent': parent, 'args': args, 'kwargs': kwargs}
        self.add_node(class_name, uid, parent, *args, **kwargs)

    def add_node(self, class_name, node_id=None, parent_id=None, *args, **kwargs):
        """ Add a new node to the hierarchy on each channel tree. """
        uid = node_id if node_id else class_name

        # Add to each channel hierarchy.
        for channel in range(self.channels):
            kwargs['channel_id'] = channel
            kwargs['config'] = self.config
            node_thread = node_factory(class_name, *args, **kwargs)
            channel_hierarchy = self.root['channels'][channel]
            channel_hierarchy[uid] = {
                'thread': node_thread
            }

            if parent_id:
                try:
                    channel_hierarchy[parent_id]['thread'].add_peer(channel_hierarchy[uid]['thread'])
                    channel_hierarchy[uid]['parent'] = parent_id
                except KeyError:
                    print('Could not find specified parent node {} in hierarchy.'.format(parent_id))
                    raise
            else:
                channel_hierarchy['root']['peer_list'].append(channel_hierarchy[uid]['thread'])
                channel_hierarchy[uid]['parent'] = 'root'

    def remove_node(self, node_id):
        """ Remove a node from the hierarchy tasks. """
        if not node_id in self.root['channels'][0]:
            raise KeyError('Node with id {} could not be found in hierarchy. '.format(node_id))

        if node_id in self.custom_nodes:
            del self.custom_nodes[node_id]

        # Remove node from each channel.
        for channel in range(self.channels):
            if node_id in self.root['channels'][channel]:
                node = self.root['channels'][channel][node_id]

                # Remove any children from node, if deleting a node with children.
                if hasattr(node['thread'], 'peer_list'):
                    peers = node['thread'].get_peer_list()
                    for peer in peers:
                        LOGGER.debug('Removing child node %s of %s from channel hierarchy %d', peer, node_id, channel)
                        self.remove_node(peer.__class__.__name__)

                parent = node['parent']
                if parent == 'root':
                    self.root['channels'][channel]['root']['peer_list'].remove(node['thread'])
                else:
                    self.root['channels'][channel][parent]['thread'].remove_peer(node['thread'])

                del self.root['channels'][channel][node_id]

                LOGGER.debug('Removed node %s from channel hierarchy %d', node_id, channel)
            else:
                LOGGER.error('Node %s does not exist in channel hierarchy %d', node_id, channel)

    def put(self, data):
        """ Push data to root node of hierarchy. """
        self.root['thread'].queue.put(data)

def node_factory(node_class, *args, **kwargs):
    """ Create a new node of the given type.
        The node must inherit from either a worker or coordinator base class.
    """
    coordinators = {subclass.__name__ : subclass for subclass in Coordinator.__subclasses__()}
    workers = {subclass.__name__ : subclass for subclass in Worker.__subclasses__()}
    nodes = {**coordinators, **workers}
    if node_class in nodes:
        return nodes[node_class](*args, **kwargs)
    else:
        raise ValueError("{} does not inherit from Worker or Coordinator.".format(node_class))
