'''
    Test file
    Sine Wave, Sawtooth and Square
'''
import unittest
from numpy import arange, zeros
from rtmaii.configuration import Config

class TestSuite(unittest.TestCase):
    '''
        Test Suite for the configuration module.
    '''

    def setUp(self):
        """ Perform setup of initial parameters. """
        self.config = Config()

    def test_source_config(self):
        """ Test that setting up the library with the default input device works.

            No need to validate args, as these should be supplied by Pyaudio/Wave.
        """
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

    def test_bands_type_error(self):
        """ Test that task config throws error when invalid type is used for band range. """
        self.assertRaises(TypeError, self.config.set_config, **{'bands': {'test': 'thisIsWrong'}})

    def test_bands_length_error(self):
        """ Test that task config throws error when range does not contain 2 items. """
        self.assertRaises(ValueError, self.config.set_config, **{'bands': {'test': [0]}})

    def test_bands_index_error(self):
        """ Test that band is correctly set when a valid setting is used. """
        self.assertRaises(TypeError, self.config.set_config, **{'bands': {'test': [0, 'notanum']}})

    def test_pitch_config(self):
        """ Test that band is correctly set when a valid setting is used. """
        arguments = {'pitch_algorithm': 'auto-correlation'}
        self.config.set_config(**arguments)
        self.assertEqual(self.config.get_config('pitch_algorithm'), arguments['pitch_algorithm'])

    def test_invalid_pitch(self):
        """ Test that band is correctly set when a valid setting is used. """
        self.assertRaises(ValueError, self.config.set_config, **{'pitch_algorithm': 'pirate'})

    def test_pitch_type_error(self):
        """ Test that band is correctly set when a valid setting is used. """
        self.assertRaises(TypeError, self.config.set_config, **{'pitch_algorithm': 1337})

    def test_frames_valid(self):
        """ Test that band is correctly set when a valid setting is used. """
        arguments = {'frames_per_sample': 512}
        self.config.set_config(**arguments)
        self.assertEqual(self.config.get_config('frames_per_sample'), arguments['frames_per_sample'])

    def test_frames_type_error(self):
        """ Test that band is correctly set when a valid setting is used. """
        self.assertRaises(TypeError, self.config.set_config, **{'frames_per_sample': None})

    def test_frequency_valid(self):
        """ Test that band is correctly set when a valid setting is used. """
        arguments = {'frequency_resolution': 512}
        self.config.set_config(**arguments)
        self.assertEqual(self.config.get_config('frequency_resolution'), arguments['frequency_resolution'])

    def test_frequency_type_error(self):
        """ Test that band is correctly set when a valid setting is used. """
        self.assertRaises(TypeError, self.config.set_config, **{'frequency_resolution': None})

    def test_merge_channels_valid(self):
        """ Test that band is correctly set when a valid setting is used. """
        arguments = {'merge_channels': False}
        self.config.set_config(**arguments)
        self.assertEqual(self.config.get_config('merge_channels'), arguments['merge_channels'])

    def test_merge_channels_type_error(self):
        """ Test that band is correctly set when a valid setting is used. """
        self.assertRaises(TypeError, self.config.set_config, **{'merge_channels': None})
