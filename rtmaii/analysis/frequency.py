"""
    Frequency analysis module.
    - Analyses parts of the frequency spectrum, including the presence of each band.
"""
# INPUTS spectrum
# OUTPUTS frequency_bands

def remove_noise(spectrum: list, noise_level: float):
    """ Remove any frequencies with an amplitude under the noise_level param when calculating balance. """
    return list(map(lambda amp: 0 if amp < noise_level else amp, spectrum))

def normalize_dict(dictionary: dict, dict_sum: float):
    """ Constrain dictionary values to continous range 0-1 based on the dictionary sum given.

        **Args**:
            - dictionary: the dictionary to be normalized.
            - dict_sum: the sum value to normalize with.
    """
    return { key: float(value)/dict_sum for key, value in dictionary.items() }


def get_band_power(spectrum: list, bands: dict):
    """ Get the summed power of each frequency range provided by bands.

        **Args**:
            - spectrum: the spectrum to be summed against.
            - bands: the bands to sum powers of.
    """
    return {band: sum(spectrum[int(values[0]):int(values[1])])
                     for band, values in bands.items()}

def frequency_bands(spectrum: list, bands: dict):
    """
        Creates a Dictionary of the amplitude balance between each input frequency band.

        **Args**:
            - spectrum: the spectrum to analyse.
            - bands: the band ranges to find the presence of.
    """
    filtered_spectrum = remove_noise(spectrum, 0.5)
    band_power = get_band_power(spectrum, bands)
    normalized_presence = normalize_dict(band_power, sum(filtered_spectrum))

    return normalized_presence

# NOTE: Could analyse other frequencies in spectrum, find overtones and harmonics
# Default configuration should be bass, lows, highs