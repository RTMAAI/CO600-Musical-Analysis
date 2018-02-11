# INPUTS spectrum
# OUTPUTS frequency_bands
# TODO: Comment the shit out of this.

def remove_noise(spectrum, noise_level):
    """ Remove any frequencies with an amplitude under the noise_level param when calculating balance """
    return list(map(lambda amp: 0 if amp < noise_level else amp, spectrum))

def normalize_dict(dictionary):
    """ Constrain dictionary values to continous range 0-1. """
    dict_sum = sum(dictionary.values())
    norm = { key: float(value)/dict_sum for key, value in dictionary.items() }
    return norm

def frequency_bands(spectrum, bands):
    """
        Creates a Dictionary of the amplitude balance between each input frequency band.
        The sum of all values adds up to 1.
    """
    filtered_spectrum = remove_noise(spectrum, 0.5)

    band_presence = {band: sum(filtered_spectrum[int(values[0]):int(values[1])])
                     for band, values in bands.items()}

    normalized_presence = normalize_dict(band_presence)

    return normalized_presence

# NOTE: Could analyse other frequencies in spectrum, find overtones and harmonics
# Default configuration should be bass, lows, highs