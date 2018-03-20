'''
    Test file
    Sine Wave, Sawtooth and Square
'''
import unittest
from numpy import arange, zeros
from rtmaii.configuration import Config

class TestSuite(unittest.TestCase):
    '''
        Test Suite for the bands module.
    '''

    def setUp(self):
        """ Perform setup of initial parameters. """
        self.config = Config()

    def test_source_config(self):
        """ Test that setting up the library with the default input device works. """
        self.config.set_source({'rate': 20000, 'channels': 1})
        self.assertEqual(self.config.get_config('sampling_rate'), 20000)
        self.assertEqual(self.config.get_config('channels'), 1)

    def test_task_config(self):
        """ Test that task is correctly set when a valid setting is used. """
        self.config.set_config(**{'tasks': {'pitch': False}})
        self.assertEqual(self.config.get_config('tasks')['pitch'], False)

    def test_task_config_multiple(self):
        """ Test that task is correctly set when valid settings are used. """
        arguments = {'tasks': {'pitch': False, 'genre': False, 'beat': False}}
        self.config.set_config(**arguments)
        config = self.config.get_config('tasks')
        for key, value in arguments['tasks'].items():
            self.assertEqual(config[key], value)

    def test_task_key_error(self):
        """ Test that task config throws error when invalid key is used. """
        self.assertRaises(KeyError, self.config.set_config, **{'tasks': {'random_task': False}})

    def test_task_type_error(self):
        """ Test that task config throws error when invalid type is used. """
        self.assertRaises(TypeError, self.config.set_config, **{'tasks': {'pitch': 'True'}})

    def test_bands_config(self):
        """ Test that band is correctly set when a valid setting is used. """
        arguments = {'bands': {'test': [0, 2000]}}
        self.config.set_config(**arguments)
        self.assertEqual(self.config.get_config('bands'), arguments['bands'])
