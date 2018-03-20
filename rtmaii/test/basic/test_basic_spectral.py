""" SPECTRAL MODULE TESTS

    - Any tests against the spectral analysis module methods will be contained here.
"""
import unittest
from numpy import sin, pi, arange
from rtmaii.analysis import spectral

class SpectralTestSuite(unittest.TestCase):
    """ Test Suite for the spectral module. """

    def setUp(self):
        """ Perform setup of initial parameters. """
        def generate_sine(frequency, sampling_rate, time_step):
            """ Generates a basic sine wave for testing. """
            return sin(2 * pi * frequency * time_step / sampling_rate)

        self.sampling_rate = 50
        self.time_step = arange(self.sampling_rate)

        self.low_frequency = generate_sine(5, self.sampling_rate, self.time_step)
        self.med_frequency = generate_sine(10, self.sampling_rate, self.time_step)
        self.high_frequency = generate_sine(20, self.sampling_rate, self.time_step)
        self.complex_wave = self.low_frequency + self.med_frequency + self.high_frequency

        self.window = spectral.new_window(self.sampling_rate, 'blackmanharris')
        self.bp_filter = spectral.butter_bandpass(1, 24, self.sampling_rate, 10)
        self.spectrum = spectral.spectrum(self.low_frequency, self.window, self.bp_filter)
        self.conv_signal = spectral.convolve_signal(self.low_frequency)

        self.filter_cut_off = 0.006 # Maximum amplitude expected of filtered frequencies.

    def test_spectrum_length(self):
        """ Test output spectrums length, should be half the sampling_rate. """
        self.assertEqual(len(self.spectrum), self.sampling_rate / 2)

    def test_spectrum_value(self):
        """ As it's a basic sine wave the amplitude at the frequency location should be highest. """
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
        for power in spectrum:
            self.assertLessEqual(power, self.filter_cut_off)

    def test_bandpass_filter_high(self):
        """ Test that the bandpass filter removes high frequencies as expected. """
        bp_filter = spectral.butter_bandpass(1, 10, self.sampling_rate)
        spectrum = spectral.spectrum(self.high_frequency, self.window, bp_filter)
        for power in spectrum:
            self.assertLessEqual(power, self.filter_cut_off)

    def test_bandpass_filter_complex(self):
        """ Test that the bandpass filter removes low and high frequencies as expected. """
        bp_filter = spectral.butter_bandpass(10, 24, self.sampling_rate)
        spectrum = spectral.spectrum(self.complex_wave, self.window, bp_filter)
        for low_frequency in range(0, 9):
            self.assertLessEqual(spectrum[low_frequency], self.filter_cut_off)
        for high_frequency in range(25, len(spectrum)):
            self.assertLessEqual(spectrum[high_frequency], self.filter_cut_off)
        self.assertGreaterEqual(spectrum[20], self.filter_cut_off)

    def test_conv_spectrum_length(self):
        """ Test length of generated convolved spectrums.
            Two spectrums so should be == sampling rate.
        """
        self.assertEqual(len(self.conv_signal), self.sampling_rate)

    def test_conv_spectrum_value(self):
        """ As it's a basic sine wave the amplitude at the frequency location should be lowest.
            (Opposite to standard spectrum.)
        """
        peak = self.conv_signal[5]
        for i in range(len(self.spectrum)):
            self.assertLessEqual(peak, self.conv_signal[i])
