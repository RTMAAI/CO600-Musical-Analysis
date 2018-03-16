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
    """ Test Suite for pitch module.

        The pitch methods are asserted to 2 decimal points, i.e. if the expected frequency was 5 then a frequency of 4.995+ would pass.

        This is because the methods make use of interpolation, which gives a closer estimate to the frequency, which can move the decimal points down.
    """

    def setUp(self):
        """ Perform setup of initial parameters. """
        self.sampling_rate = 100
        self.frequency = 5
        self.timestep = arange(self.sampling_rate)
        self.sin_wave = sin(2 * pi * self.frequency * self.timestep / self.sampling_rate)
        self.bp_filter = spectral.butter_bandpass(1, 48, self.sampling_rate)
        self.window = spectral.new_window(len(self.sin_wave), 'blackmanharris')
        self.frequency_spectrum = spectral.spectrum(self.sin_wave, self.window, self.bp_filter)
        self.convolved_spectrum = spectral.convolve_signal(self.sin_wave)

    def test_basic_ZC(self):
        """ Test that the zero-crossings algorithm can detect the correct pitch for a basic sine wave. """
        self.assertEqual(pitch.pitch_from_zero_crossings(self.sin_wave, self.sampling_rate), 5)

    def test_basic_auto_correlation(self):
        """ Test that the zero-crossings algorithm can detect the correct pitch for a basic sine wave. """
        self.assertAlmostEqual(pitch.pitch_from_auto_correlation(self.convolved_spectrum, self.sampling_rate), 5, 2)

    def test_basic_FFT(self):
        """ Test that the zero-crossings algorithm can detect the correct pitch for a basic sine wave. """
        self.assertAlmostEqual(pitch.pitch_from_fft(self.frequency_spectrum, self.sampling_rate), 5, 2)

    def test_basic_HPS(self):
        """ Test that the zero-crossings algorithm can detect the correct pitch for a basic sine wave. """
        self.assertAlmostEqual(pitch.pitch_from_hps(self.frequency_spectrum, self.sampling_rate, 8), 5, 2)
