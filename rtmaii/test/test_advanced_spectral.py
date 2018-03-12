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
import logging


class SpectralTestSuite(unittest.TestCase):
    '''
        Advanced Test Suite for the spectral module.
    '''

    def setUp(self):
        """ Perform setup"""
        def generate_sine(frequency, sampling_rate, time_step):
            return sin(2 * pi * frequency * time_step / sampling_rate)

        self.sampling_rate = 44100 # standard sampling rate.
        self.time_step = arange(self.sampling_rate)

        self.low_frequency = generate_sine(200, self.sampling_rate, self.time_step)
        self.med_frequency = generate_sine(5000, self.sampling_rate, self.time_step)
        self.high_frequency = generate_sine(21000, self.sampling_rate, self.time_step)
        self.complex_wave = self.low_frequency + self.med_frequency + self.high_frequency

        self.window = spectral.new_window(self.sampling_rate, 'blackmanharris')
        self.bp_filter = spectral.butter_bandpass(100, 20000, self.sampling_rate, 5)
        self.spectrum = spectral.spectrum(self.low_frequency, self.window, self.bp_filter)
        self.conv_spectrum = spectral.convolve_signal(self.low_frequency)

        self.filter_cut_off = 0.006 # Maximum amplitude expected of filtered frequencies.

    def test_spectrum_length(self):
        """ Test output spectrums length, should be half the sampling_rate. """
        self.assertEqual(len(self.spectrum), self.sampling_rate / 2)

    def test_conv_spectrum_length(self):
        """ Test length of generated convolved spectrums. Two spectrums so should be == sampling rate. """
        self.assertEqual(len(self.conv_spectrum), self.sampling_rate)
