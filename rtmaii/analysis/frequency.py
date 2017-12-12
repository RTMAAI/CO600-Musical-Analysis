# INPUTS spectrum
# OUTPUTS frequency_bands
# TODO: Comment the shit out of this.

def remove_noise(spectrum, noise_level):
    """ Remove any frequencies with an amplitude under the noise_level param when calculating balance """
    return list(map(lambda amp: 0 if amp < noise_level else amp, spectrum))

def constrain_bands(bands):
    """ Constrain Frequency bands to sum to 1 """
    pass

def frequency_bands(spectrum, bands=None):
    """
        Creates a Dictionary of the amplitude balance between each input frequency band.
        The sum of all values adds up to 1.
    """
    if not bands:
        # Default frequency bands
        bands = {"sub-bass":[20, 60],
                 "bass":[60, 250],
                 "low-mid":[250, 500],
                 "mid":[500, 2000],
                 "upper-mid":[2000, 4000],
                 "presence":[4000, 6000],
                 "brilliance":[6000, 20000]}
    filtered_spectrum = remove_noise(spectrum, 1)
    band_width = 19980 # Should be configurable
    # TODO: Scale values to add up to 1, remove noise i.e. frequencies with minute amplitudes
    band_presence = {band: sum(filtered_spectrum[int(values[0]):int(values[1])]) / band_width
                     for band, values in bands.items()}
    return band_presence

# NOTE: Could analyse other frequencies in spectrum, find overtones and harmonics
# Default configuration should be bass, lows, highs
# Possible add tracker for a set frequency yourself. configurable bands.