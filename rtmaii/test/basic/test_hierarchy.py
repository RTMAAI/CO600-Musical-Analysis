""" HIERARCHY MODULE TESTS

    - Any tests against the Hierarchy module methods will be contained here.

    As the library and thread creation is strictly tied to the hierarchy,
    this test module is a lot heavier.

    Each time a test is run, we can check that the hierarchy is updated,
    as expected.

    This is more of an integration test module than a unit test module.

    As we can't be sure of the order of execution, cleanup is performed
    after each test, to ensure future tests don't break.
"""
import unittest
import logging
from rtmaii.hierarchy import Hierarchy
from rtmaii.configuration import Config
from rtmaii.worker import Worker
from rtmaii.coordinator import Coordinator

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.ERROR) # Stop module logging.

class CustomWorker(Worker):
    """ Basic worker to test hierarchy addition. """
    def __init__(self, **kwargs):
        Worker.__init__(self, channel_id=kwargs['channel_id'])
    def run(self):
        pass

class CustomCoordinator(Coordinator):
    """ Basic coordinator to test hierarchy addition. """
    def __init__(self, **kwargs):
        Coordinator.__init__(self, channel_id=kwargs['channel_id'])
    def run(self):
        pass

class TestSuite(unittest.TestCase):
    """ Test Suite for the Hierarchy module. """

    def setUp(self):
        """ Perform setup of initial parameters. """
        tasks = {
            "pitch": False,
            "genre": False,
            "beat": True,
            "export_spectrograms" : False,
            "bands": False
        }
        self.config = Config(**{'tasks': tasks})
        self.config.set_source(
            {'channels': 3,
             'rate': 44100
            })
        self.hierarchy = Hierarchy(self.config, [])

    def test_coordinator_removal(self):
        """ Test that hierarchy removed disabled task coordinators, when initialized. """
        self.assertIn('EnergyBPMCoordinator', self.hierarchy.root['channels'][0])
        self.assertNotIn('FrequencyCoordinator', self.hierarchy.root['channels'][0])
        self.assertNotIn('SpectrumCoordinator', self.hierarchy.root['channels'][0])

    def test_worker_removal(self):
        """ Test that hierarchy removed disabled task workers, when initialized. """
        self.assertIn('BPMWorker', self.hierarchy.root['channels'][0])
        self.assertNotIn('BandsWorker', self.hierarchy.root['channels'][0])
        self.assertNotIn('PredictorWorker', self.hierarchy.root['channels'][0])

    def test_add_custom_node_thread(self):
        """ Test that adding a custom node to the library works.
            - Must be added to hierarchy dictionary of single channel.
            - Must be added to custom tasks list
            - Thread must be added to root peer_list
        """
        self.hierarchy.add_custom_node(CustomCoordinator.__name__)
        self.assertIn(CustomCoordinator.__name__, self.hierarchy.custom_nodes)
        self.assertIn(CustomCoordinator.__name__, self.hierarchy.root['channels'][0])
        thread = self.hierarchy.root['channels'][0][CustomCoordinator.__name__]['thread']
        self.assertIn(thread, self.hierarchy.root['channels'][0]['root']['peer_list'])
        self.hierarchy.remove_node(CustomCoordinator.__name__) # Cleanup.

    def test_add_custom_node_parent(self):
        """ Test that adding a custom node to a parent thread works. """
        self.hierarchy.add_custom_node(CustomCoordinator.__name__, parent_id='EnergyBPMCoordinator')
        thread = self.hierarchy.root['channels'][0][CustomCoordinator.__name__]['thread']
        parent = self.hierarchy.root['channels'][0]['EnergyBPMCoordinator']['thread']
        self.assertIn(thread, parent.get_peer_list())
        self.hierarchy.remove_node(CustomCoordinator.__name__) # Cleanup.

    def test_unique_node(self):
        """ Test that adding and removing by a unique ID to a node correctly assigns/removes it."""
        uid = 'electricboogalo'
        self.hierarchy.add_custom_node(CustomCoordinator.__name__, uid,
                                       parent_id='EnergyBPMCoordinator')
        self.assertIn(uid, self.hierarchy.custom_nodes)
        self.hierarchy.remove_node(uid) # Cleanup.
        self.assertNotIn(uid, self.hierarchy.custom_nodes)

    def test_unique_node_error(self):
        """ Test that node added has a unique ID in the hierarchy. """
        self.assertRaises(AttributeError, self.hierarchy.add_custom_node,
                          CustomCoordinator.__name__, 'EnergyBPMCoordinator')

    def test_add_node(self):
        """ Test that adding a custom node to the library works.
            - Must be added to hierarchy dictionary of single channel.
            - Thread must be added to root peer_list.
        """
        self.hierarchy.add_node('FrequencyCoordinator')
        self.assertNotIn('FrequencyCoordinator', self.hierarchy.custom_nodes)
        self.assertIn('FrequencyCoordinator', self.hierarchy.root['channels'][0])
        thread = self.hierarchy.root['channels'][0]['FrequencyCoordinator']['thread']
        self.assertIn(thread, self.hierarchy.root['channels'][0]['root']['peer_list'])
        self.hierarchy.remove_node('FrequencyCoordinator') # Cleanup.

    def test_add_node_parent(self):
        """ Test that a node is added to a given parent node. """
        self.hierarchy.add_node('FrequencyCoordinator')
        self.hierarchy.add_node('BandsWorker', parent_id='FrequencyCoordinator')
        parent = self.hierarchy.root['channels'][0]['FrequencyCoordinator']['thread']
        thread = self.hierarchy.root['channels'][0]['BandsWorker']['thread']
        self.assertIn(thread, parent.get_peer_list())
        self.hierarchy.remove_node('BandsWorker')
        self.hierarchy.remove_node('FrequencyCoordinator')

    def test_remove_custom_node(self):
        """ Test removal of a custom added node from the hierarchy.
            - Tests that the node is removed from the custom_node list.
            - Tests that the node is removed from the root peer_list.
        """
        self.hierarchy.add_node(CustomWorker.__name__)
        thread = self.hierarchy.root['channels'][0][CustomWorker.__name__]['thread']
        self.hierarchy.remove_node(CustomWorker.__name__)
        self.assertNotIn(CustomWorker.__name__, self.hierarchy.root['channels'][0])
        self.assertNotIn(thread, self.hierarchy.root['channels'][0]['root']['peer_list'])

    def test_child_removal(self):
        """ Test that when a parent node is removed child nodes are removed. """
        self.hierarchy.add_node('FrequencyCoordinator')
        self.hierarchy.add_node('BandsWorker', parent_id='FrequencyCoordinator')
        self.hierarchy.remove_node('FrequencyCoordinator')
        self.assertNotIn('BandsWorker', self.hierarchy.root['channels'][0])

    def test_remove_node(self):
        """ Test that removing a node removes the thread from the parent node. """
        thread = self.hierarchy.root['channels'][0]['BPMWorker']['thread']
        self.hierarchy.remove_node('BPMWorker')
        parent_thread = self.hierarchy.root['channels'][0]['EnergyBPMCoordinator']['thread']
        self.assertNotIn('BPMWorker', self.hierarchy.root['channels'][0])
        self.assertNotIn(thread, parent_thread.get_peer_list())

    def test_remove_node_error(self):
        """ Test that key error is thrown when trying to remove a non-existent node. """
        self.assertRaises(KeyError, self.hierarchy.remove_node, 'Trump')

    def test_remove_root_error(self):
        """ Test that value error is thrown when trying to remove the root node. """
        self.assertRaises(ValueError, self.hierarchy.remove_node, 'root')

    def test_worker_parent_error(self):
        """ Test that a node can't be added to an invalid parent, without a peer_list. """
        self.assertRaises(AttributeError, self.hierarchy.add_custom_node,
                          CustomCoordinator.__name__, 'BPMWorker')

    def test_parent_error(self):
        """ Test that error is thrown when trying to add to a none existent parent. """
        self.assertRaises(KeyError, self.hierarchy.add_custom_node,
                          CustomCoordinator.__name__, None, 'nullparent')

    def test_empty_peer_removal(self):
        """ Test that Coordinators with no peers are removed on cleanup. """
        self.hierarchy.add_node('FrequencyCoordinator')
        self.hierarchy.clean_hierarchy()
        self.assertNotIn('FrequencyCoordinator', self.hierarchy.root['channels'][0])

    def test_empty_peer_custom_removal(self):
        """ Test that Custom Coordinators with no peers aren't removed on cleanup. """
        self.hierarchy.add_custom_node('FrequencyCoordinator')
        self.hierarchy.clean_hierarchy()
        self.assertIn('FrequencyCoordinator', self.hierarchy.root['channels'][0])

    def test_channel_creation(self):
        """ Test that one channel hierarchy was created. """
        self.assertEqual(len(self.hierarchy.root['channels']), 1)
        channel_peer_list = self.hierarchy.root['channels'][0]['root']['peer_list']
        self.assertListEqual(self.hierarchy.root['peer_list'][0], channel_peer_list)

    def test_multichannel_creation(self):
        """ Test that multiple hierarchies are created. """
        self.config.set_config(**{'merge_channels': False})
        self.hierarchy.reset_hierarchy()
        self.assertEqual(len(self.hierarchy.root['channels']), 3)
        self.config.set_config(**{'merge_channels': True})
        self.hierarchy.reset_hierarchy()
