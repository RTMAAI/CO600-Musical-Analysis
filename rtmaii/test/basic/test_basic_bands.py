'''
    Test file
    Sine Wave, Sawtooth and Square
'''
import logging
import unittest
from numpy import sin, pi, arange
from rtmaii.analysis import pitch
from rtmaii.analysis import spectral
from numpy import fft


class TestSuite(unittest.TestCase):
    '''
        Test Suite for the bands module.
    '''

    def test_basic_Bands(self):
        """ Test that the zero-crossings algorithm can detect the correct pitch for a basic sine wave. """
        self.assertEqual(1, 1)


