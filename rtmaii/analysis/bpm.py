"""
    BPM analysis module.
    - Uses descending velocity algorithm to determine beats.
    - Uses spaces between beats to determine bpm.

"""

from scipy.fftpack import fftfreq
from numpy import argmin, abs

def remove_noise(spectrum: list, noise_level: float):
    """ Remove any frequencies with an amplitude under the noise_level param when calculating balance. """
    return list(map(lambda amp: 0 if amp < noise_level else amp, spectrum))

def normalize_dict(dictionary: dict, dict_sum: float):
    """ Constrain dictionary values to continous range 0-1 based on the dictionary sum given.

        **Args**:
            - dictionary: the dictionary to be normalized.
            - dict_sum: the sum value to normalize with.
    """
    return { key: float(value)/dict_sum if dict_sum > 0 else 0 for key, value in dictionary.items() }


def get_band_power(spectrum: list, bands: dict):
    """ Get the summed power of each frequency range provided by bands.

        **Args**:
            - spectrum: the spectrum to be summed against.
            - bands: the bands to sum powers of.
    """
    return {band: sum(spectrum[int(values[0]):int(values[1])])
                     for band, values in bands.items()}

def frequency_bands(spectrum: list, bands: dict, sampling_rate: int):
    """
        Creates a Dictionary of the amplitude balance between each input frequency band.

        **Args**:
            - spectrum: the spectrum to analyse.
            - bands: the band ranges to find the presence of.
    """
    matched_bands = frequency_bands_to_bins(spectrum, bands, sampling_rate)
    filtered_spectrum = remove_noise(spectrum, 0.5)
    band_power = get_band_power(spectrum, matched_bands)
    normalized_presence = normalize_dict(band_power, sum(filtered_spectrum))

    return normalized_presence

def frequency_bands_to_bins(spectrum: list, bands: dict, sampling_rate: int):
    """
        In order to correctly analyse frequency bands, we need to first find the equivalent frequency bin locations.
    """
    bins = fftfreq(len(spectrum) * 2)[:len(spectrum)] * sampling_rate
    return {band: [find_nearest_bin(bins, values[0]), find_nearest_bin(bins, values[1])] for band, values in bands.items()}

def find_nearest_bin(bins: list, target: int):
    """
        test
    """
    return (abs(bins-target)).argmin()

# NOTE: Could analyse other frequencies in spectrum, find overtones and harmonics
# Default configuration should be bass, lows, highs