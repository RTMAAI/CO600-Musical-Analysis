""" PITCH MODULE TESTS

    - Any advanced tests against the pitch analysis module methods will be contained here.

    Advanced tests can vary, i.e. adding noise to the signal, harmonics, etc.

    These are accuracy tests rather than unit tests, ensuring accuracy doesn't decrease,
    between builds.
"""
import unittest
from numpy import sin, pi, arange
from numpy.random import normal
from rtmaii.analysis import pitch
from rtmaii.analysis import spectral

def generate_sine(frequency, sampling_rate, time_step):
    """ Generates a basic sine wave for testing. """
    return sin(2 * pi * frequency * time_step / sampling_rate)

class TestSuite(unittest.TestCase):
    """ Advanced Test Suite for the pitch module.
        This go further than basic unit tests, these test the pitch methods,
        against a more complex signal.

        However, including these as unit tests is useful,
        as the accuracy shouldn't decrease in implementations.
        So if these tests break, then the accuracy has reduced in a new iteration.
    """
    def setUp(self):
        """ Perform setup"""
        self.sampling_rate = 44100 # standard sampling rate.
        time_step = arange(self.sampling_rate)

        self.fundamental_freq = 5000
        low_frequency = generate_sine(200, self.sampling_rate, time_step)
        fundamental = generate_sine(self.fundamental_freq,
                                    self.sampling_rate, time_step) * 500 # Fundamental
        high_frequency = generate_sine(12000, self.sampling_rate, time_step)
        noise = normal(0, 1, self.sampling_rate) # Add noise to make it harder to detect pitch.
        self.complex_wave = low_frequency + fundamental + high_frequency + noise

        # Pre-processing to setup signal.
        self.window = spectral.new_window(self.sampling_rate, 'blackmanharris')
        self.bp_filter = spectral.butter_bandpass(100, 20000, self.sampling_rate, 5)
        self.spectrum = spectral.spectrum(self.complex_wave, self.window, self.bp_filter)
        self.conv_spectrum = spectral.convolve_signal(self.complex_wave)

    def test_advanced_zc(self):
        """ Test that the zero-crossings algorithm can detect the pitch for a basic sine wave. """
        fundamental = pitch.pitch_from_zero_crossings(self.complex_wave, self.sampling_rate)
        difference = abs(self.fundamental_freq - fundamental)
        self.assertLessEqual(difference, 2)

# def test_advanced_auto_correlation(self):
#     """ Test that the auto-correlation algorithm can detect the pitch for a basic sine wave. """
#     fundamental = pitch.pitch_from_auto_correlation(self.conv_spectrum, self.sampling_rate)
#     difference = abs(self.fundamental_freq - fundamental)
#     self.assertLessEqual(difference, 2)

    def test_advanced_fft(self):
        """ Test that the fft algorithm can detect the pitch for a basic sine wave. """
        fundamental = pitch.pitch_from_fft(self.spectrum, self.sampling_rate)
        difference = abs(self.fundamental_freq - fundamental)
        self.assertLessEqual(difference, 2)

    def test_advanced_hps(self):
        """ Test that the harmonic product spectrum algorithm can detect the pitch. """
        fundamental = pitch.pitch_from_hps(self.spectrum, self.sampling_rate, 2)
        difference = abs(self.fundamental_freq - fundamental)
        self.assertLessEqual(difference, 2)
