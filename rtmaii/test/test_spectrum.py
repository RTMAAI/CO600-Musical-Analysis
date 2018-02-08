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


class SpectrumTestSuite(unittest.TestCase):
    '''
        Test Suite Initialization of test parameters.
    '''

    def setUp(self):
        def generate_sin(frequency, sampling_rate, time_step):
            return sin(2 * pi * frequency * time_step / sampling_rate)

        self.sampling_rate = 50
        self.time_step = arange(self.sampling_rate)

        self.low_frequency = generate_sin(5, self.sampling_rate, self.time_step)
        self.med_frequency = generate_sin(10, self.sampling_rate, self.time_step)
        self.high_frequency = generate_sin(20, self.sampling_rate, self.time_step)
        self.complex_wave = self.low_frequency + self.med_frequency + self.high_frequency

        self.window = spectral.new_window(self.sampling_rate, 'blackmanharris')
        self.bp_filter = spectral.butter_bandpass(1, 24, self.sampling_rate)
        self.spectrum = spectral.spectrum(self.low_frequency, self.window, self.bp_filter)

        self.filter_cut_off = 0.006

    def test_spectrum_length(self):
        """ Test output spectrums length, should be half the sampling_rate. """
        self.assertEqual(len(self.spectrum), 25)

    def test_spectrum_value(self):
        """ As it's a basic sine wave the amplitude at the peak should be highest. """
        peak = self.spectrum[5]
        for i in range(len(self.spectrum)):
            self.assertLessEqual(self.spectrum[i], peak)

    def test_window_length(self):
        """ Test that generated window length is equal to sampling rate. """
        self.assertEqual(self.sampling_rate, len(self.window))

    def test_bandpass_filter_low(self):
        """ Test that the bandpass filter removes low frequencies as expected. """
        bp_filter = spectral.butter_bandpass(10, 24, self.sampling_rate)
        spectrum = spectral.spectrum(self.low_frequency, self.window, bp_filter)
        for i in range(len(spectrum)):
            self.assertLessEqual(spectrum[i], self.filter_cut_off)

    def test_bandpass_filter_high(self):
        """ Test that the bandpass filter removes high frequencies as expected. """
        bp_filter = spectral.butter_bandpass(1, 10, self.sampling_rate)
        spectrum = spectral.spectrum(self.high_frequency, self.window, bp_filter)
        for i in range(len(spectrum)):
            self.assertLessEqual(spectrum[i], self.filter_cut_off)

    def test_bandpass_filter_complex(self):
        """ Test that the bandpass filter removes low and high frequencies as expected. """
        bp_filter = spectral.butter_bandpass(10, 24, self.sampling_rate)
        spectrum = spectral.spectrum(self.complex_wave, self.window, bp_filter)
        for i in range(0, 9):
            self.assertLessEqual(spectrum[i], self.filter_cut_off)
        for i in range(25, len(spectrum)):
            self.assertLessEqual(spectrum[i], self.filter_cut_off)
        self.assertGreaterEqual(spectrum[20], self.filter_cut_off)
