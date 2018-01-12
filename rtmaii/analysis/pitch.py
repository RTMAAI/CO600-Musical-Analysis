"""
    This module handles any pitch based analysis.

    **INPUTS**:
        Spectrum: a bin of frequencies and their amplitudes.
        Signal: temporal wave form.

    **OUTPUTS**:
        Pitch (Fundamental Frequency): the pitch of the input.

    **Example**:

    TODO:
        * Look into other areas i.e. harmonic product spectrum.
        * Finish comments and documentation.
"""
from numpy import argmax, mean, diff

def pitch_from_fft(spectrum: list, sampling_rate: int):
    """ Estimate pitch from the frequency spectrum """
    basic_frequency = argmax(spectrum)
    estimated_frequency = interpolate_peak(abs(spectrum), basic_frequency)
    return sampling_rate * estimated_frequency /len(spectrum)

def pitch_from_auto_correlation(convolved_spectrum: list, sampling_rate: int):
    """ Estimate pitch using autocorrelation """

    spectrum_distances = diff(convolved_spectrum)
    first_low_point = next(
        i for i, _ in enumerate(spectrum_distances) if spectrum_distances[i] > 0
    ) # Finds first rising edge
    peak = argmax(convolved_spectrum[first_low_point:]) + first_low_point
    interpolated_peak = interpolate_peak(convolved_spectrum, peak)
    return sampling_rate / interpolated_peak

def pitch_from_zero_crossings(signal: list, sampling_rate: int):
    """ Estimate pitch by counting zero-crossings """
    indices = []
    for i, _ in enumerate(signal): # Find indices of zero-crossings
        if (signal[i - 1] > 0) and (signal[i] < 0):
            indices.append(i)
        elif (signal[i - 1] < 0) and (signal[i] > 0):
            indices.append(i)

    crossings = indices

    return sampling_rate / mean(diff(crossings))

def interpolate_peak(spectrum: list, peak: int):
    """
        Uses quadratic interpolation of spectral peaks to get a better estimate of the peak.
        Based off: https://ccrma.stanford.edu/~jos/sasp/Quadratic_Interpolation_Spectral_Peaks.html
    """
    prev_neighbour = spectrum[peak-1]
    next_neighbour = spectrum[peak+1]
    estimated_peak = 1/2 * (
        prev_neighbour  - next_neighbour /
        (prev_neighbour  - 2 * spectrum[peak] + next_neighbour)
    ) # + peak
    return estimated_peak
