""" PITCH MODULE TESTS

    - Any basic tests against the pitch analysis module methods will be contained here.

    By basic I mean just tests against a basic sine wave to make sure the components work.
"""
import unittest
from numpy import sin, pi, arange, zeros
from rtmaii.analysis import pitch
from rtmaii.analysis import spectral

class TestSuite(unittest.TestCase):
    """ Test Suite for pitch module.

        The pitch methods are asserted to 2 decimal points,
        i.e. if the expected frequency was 5 then a frequency of 4.995+ would pass.

        This is because the methods make use of interpolation,
        which gives a closer estimate to the frequency,
        this can force the value to multiple decimal points.
    """
    def setUp(self):
        """ Perform setup of initial parameters. """
        self.sampling_rate = 100
        self.frequency = 5
        self.timestep = arange(self.sampling_rate)
        self.sin_wave = sin(2 * pi * self.frequency * self.timestep / self.sampling_rate)
        bp_filter = spectral.butter_bandpass(1, 48, self.sampling_rate)
        window = spectral.new_window(len(self.sin_wave), 'blackmanharris')
        self.frequency_spectrum = spectral.spectrum(self.sin_wave, window, bp_filter)
        self.convolved_signal = spectral.convolve_signal(self.sin_wave)

    def test_basic_zc(self):
        """ Test that the zero-crossings algorithm can detect the pitch for a basic sine wave. """
        self.assertEqual(pitch.pitch_from_zero_crossings(self.sin_wave, self.sampling_rate), 5)

    def test_stubbed_auto_correlation(self):
        """ Test that auto-corellation works on a stub list. """
        conv_signal = zeros(20)
        conv_signal[0] = 1
        conv_signal[10] = 1
        self.assertEqual(pitch.pitch_from_auto_correlation(conv_signal, 10), 1)

    def test_basic_auto_correlation(self):
        """ Test that the auto-correlation algorithm can detect the pitch for a basic sine wave.
            Using our convolve_signal method, so more of an integration test.
        """
        self.assertAlmostEqual(pitch.pitch_from_auto_correlation(self.convolved_signal,
                                                                 self.sampling_rate),
                               self.frequency, 2)

    def test_stub_fft(self):
        """ Test that fft peak method, works on a stub list. """
        spectrum = zeros(50)
        spectrum[10] = 1
        self.assertEqual(pitch.pitch_from_fft(spectrum, 10), 1)

    def test_basic_fft(self):
        """ Test that the fft algorithm can detect the pitch for a basic sine wave. """
        self.assertAlmostEqual(pitch.pitch_from_fft(self.frequency_spectrum, self.sampling_rate),
                               self.frequency, 2)

    def test_stub_hps(self):
        """ Test that hps method, works on a stub list.
            Only creates one harmonic product spectrum.
        """
        spectrum = zeros(80)
        spectrum[19] = 20
        spectrum[9] = 19
        self.assertEqual(pitch.pitch_from_hps(spectrum, 160, 3), 9)

    def test_basic_hps(self):
        """ Test that the harmonic product spectrum algorithm can detect the pitch. """
        self.assertAlmostEqual(pitch.pitch_from_hps(self.frequency_spectrum, self.sampling_rate, 2),
                               self.frequency, 2)

    def test_interpolation(self):
        """ Test that interpolation works on basic values. """
        values = [20, 50, 40] # The index will be interpolated to 1.5.
        self.assertEqual(pitch.interpolate_peak(values, 1), 1.5)
