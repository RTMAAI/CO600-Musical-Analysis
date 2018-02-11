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


def frequency_bands(spectrum: list, bands: dict):
    """
        Creates a Dictionary of the amplitude balance between each input frequency band.
    """
    filtered_spectrum = remove_noise(spectrum, 0.5)

    band_presence = {band: sum(filtered_spectrum[int(values[0]):int(values[1])])
                     for band, values in bands.items()}

    normalized_presence = normalize_dict(band_presence, sum(filtered_spectrum))

    return normalized_presence

# NOTE: Could analyse other frequencies in spectrum, find overtones and harmonics
# Default configuration should be bass, lows, highs