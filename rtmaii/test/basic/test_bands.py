""" BANDS MODULE TESTS

    - Any tests against the bands analysis module methods will be contained here.
"""
import unittest
from numpy import arange, zeros
from rtmaii.analysis import frequency

class TestSuite(unittest.TestCase):
    """ Test Suite for the bands module. """

    def setUp(self):
        """ Perform setup of initial parameters. """
        self.band_sum = 10000
        self.interested_bands = {'low': [0, 10],
                                 'med': [10, 70],
                                 'high': [70, 100]}
        self.spectrum = arange(0, 100, 1) # Create 100 values increasing by 1 at each step.
        self.spectrum_len = len(self.spectrum)
        # key value where key == expected value after normalization.
        self.bands = {'0.1': 10, '0.2': 20, '0.3': 30, '1': 100}
        self.bands_sum = 100 # Sum to compare normalized values against.

    def test_noise_removal(self):
        """ Remove frequencies below amplitude of 11. Keep amplitudes above. """
        noiseless_spectrum = frequency.remove_noise(self.spectrum, 11)
        for i in range(10):
            self.assertEqual(noiseless_spectrum[i], 0)
        for i in range(11, self.spectrum_len):
            self.assertNotEqual(noiseless_spectrum[i], 0)

    def test_normalization(self):
        """ Test that the values are normalized as expected. """
        normalized_dictionary = frequency.normalize_dict(self.bands, self.bands_sum)
        for key, value in normalized_dictionary.items():
            self.assertEqual(float(key), value)

    def test_band_power(self):
        """ Test that a given frequency range is summed correctly. """
        power = frequency.get_band_power(self.spectrum, {'full_range': [0, self.spectrum_len]})
        self.assertEqual(power['full_range'], sum(self.spectrum))

    def test_multiple_band_power(self):
        """ Test that multiple frequency ranges are summed correctly. """
        power = frequency.get_band_power(self.spectrum, self.interested_bands)
        for key, value in self.interested_bands.items():
            self.assertEqual(power[key], sum(self.spectrum[value[0]:value[1]]))

    def test_frequency_bands(self):
        """ End-to-end test of retrieiving the presence of a frequency bands. """
        spectrum = zeros(100) # Start with empty array
        spectrum[2] = 100 # Set low band to have all the power.
        bands = frequency.frequency_bands(spectrum, {'full_range': [2, 3]}, len(spectrum) * 2)
        self.assertEqual(bands['full_range'], 1)

    def test_frequency_bands_to_bins(self):
        """ Tests that the frequency bins points are correctly found. """
        spectrum = arange(0, 102, 1)
        bands = frequency.frequency_bands_to_bins(spectrum,
                                                  {'full_range': [0, 100]},
                                                  len(spectrum) * 2)
        self.assertEqual({'full_range': [0, 100]}, bands)
