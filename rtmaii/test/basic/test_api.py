""" RTMA MODULE TESTS

    - Any tests against the RTMA API module methods will be contained here.

    Alot of the methods can't be tested heavily, as they interact with other
    components of our library. Which all have their own tests for validation.

    As initialization of our library will try to find an input device,
    any further tests will fail on Travis CI as the VMs don't have an audio interface.

    Configuration based tests, are already covered by the configuration module.
"""
import unittest
from rtmaii import rtmaii

class TestSuite(unittest.TestCase):
    """ Test Suite for the RTMA module. """

    def test_callback_validation_valid(self):
        """ This function call should not fail. """
        try:
            mock = {'function': sum, 'signal': 'sig'}
            rtmaii.__validate_callback__(mock)
        except TypeError:
            self.fail('test_callback_validation_valid raised unexpected exception.')
        except ValueError:
            self.fail('test_callback_validation_valid raised unexpected exception.')

    def test_empty_callback_error(self):
        """ Empty dictionary should raise a value error. """
        mock = {}
        self.assertRaises(ValueError, rtmaii.__validate_callback__, mock)

    def test_callback_uncallable(self):
        """ Empty dictionary should raise a value error. """
        mock = {'function': '', 'signal': 'sig'}
        self.assertRaises(TypeError, rtmaii.__validate_callback__, mock)

    def test_callback_signal_error(self):
        """ Throw error if signal provided is not a string. """
        mock = {'function': sum, 'signal': 1337}
        self.assertRaises(TypeError, rtmaii.__validate_callback__, mock)

    def test_set_callbacks_error(self):
        """ Throw error on invalid input to set_callbacks function. """
        mock = 'ishouldntbeastring'
        self.assertRaises(TypeError, rtmaii.Rtmaii.set_callbacks, mock)

    def test_remove_callbacks_error(self):
        """ Throw error on invalid input to remove_callbacks function. """
        mock = 'ishouldntbeastring'
        self.assertRaises(TypeError, rtmaii.Rtmaii.set_callbacks, mock)
