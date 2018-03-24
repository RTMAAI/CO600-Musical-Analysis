""" FREQUENCY ANALYSIS MODULE.
    Analyses parts of the frequency spectrum, including the presence of each band.

    INPUTS:
        Spectrum: The spectrum to be analysed.
        Bands: The frequency bands to compare the presence of.
        Sampling_rate: The sampling rate of the signal being analysed.

    OUTPUTS:
        Frequency_bands_presence: The normalised presence of each band analysed.
"""
from scipy.fftpack import fftfreq
from numpy import absolute, real

def remove_noise(spectrum: list, noise_level: float) -> list:
    """ Remove any frequencies with an amplitude under a specified noise level.

        Args:
            - spectrum: the spectrum to be perform noise reduction on.
            - noise_level: the min power bin values should have to not be removed.
    """
    return list(map(lambda amp: 0 if amp < noise_level else amp, spectrum))

def normalize_dict(dictionary: dict, dict_sum: float) -> dict:
    """ Constrain dictionary values to continous range 0-1 based on the dictionary sum given.

        Args:
            - dictionary: the dictionary to be normalized.
            - dict_sum: the sum value to normalize with.
    """
    return {key: real(value)/dict_sum if dict_sum > 0 else 0 for key, value in dictionary.items()}

def get_band_power(spectrum: list, bands: dict) -> dict:
    """ Get the summed power of each frequency range provided by bands.

        Args:
            - spectrum: the spectrum to be summed against.
            - bands: the bands to sum powers of.
    """
    return {band: sum(spectrum[values[0]:values[1]])
            for band, values in bands.items()}

def frequency_bands(spectrum: list, bands: dict, sampling_rate: int) -> dict:
    """ Creates a Dictionary of the amplitude balance between each input frequency band.

        Args:
            - spectrum: the spectrum to analyse.
            - bands: the band ranges to find the presence of.
            - sampling_rate: sampling rate of signal used to create spectrum.
    """
    matched_bands = frequency_bands_to_bins(spectrum, bands, sampling_rate)
    filtered_spectrum = remove_noise(spectrum, 5)
    band_power = get_band_power(filtered_spectrum, matched_bands)
    normalized_presence = normalize_dict(band_power, real(sum(filtered_spectrum)))

    return normalized_presence

def frequency_bands_to_bins(spectrum: list, bands: dict, sampling_rate: int) -> dict:
    """ In order to correctly analyse frequency bands, finds the equivalent frequency bin locations.

        As the frequency spectrums resolution is as good as the size of the data used to create it.

        We need to find a mapping between a frequency in Hz to it's index location in the spectrum.

        Args:
            - spectrum: frequency spectrum of analysed signal.
            - bands: the band ranges to find the presence of.
            - sampling_rate: sampling rate of signal used to create spectrum.
    """
    bins = fftfreq(len(spectrum) * 2)[:len(spectrum)] * sampling_rate
    matched_band_locations = {band: [find_nearest_bin(bins, rng[0]), find_nearest_bin(bins, rng[1])]
                              for band, rng in bands.items()}
    return matched_band_locations

def find_nearest_bin(bins: list, target: int) -> int:
    """ Compares given bin list to target value, returning the index that is closest.

        Args:
            - bins: frequency spectrum bin values.
            - target: target frequency.
    """
    return (absolute(bins-target)).argmin()
