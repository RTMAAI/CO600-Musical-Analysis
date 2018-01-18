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
from numpy import argmax, mean, diff, arange

def pitch_from_fft(spectrum: list, sampling_rate: int):
    """ Estimate pitch from the frequency spectrum """
    basic_frequency = argmax(spectrum)
    estimated_frequency = interpolate_peak(abs(spectrum), basic_frequency)
    return sampling_rate * estimated_frequency / len(spectrum)

def pitch_from_auto_correlation(convolved_spectrum: list, sampling_rate: int):
    """ Estimate pitch using the autocorrelation method.

        *Advantages*:
            - Good for repetitive wave forms, i.e. sine waves/saw tooths.
            - Represents a pitch closer to what humans hear.

        *Disadvantages*:
            - Requires an FFT which can be expensive.
            - Not great with inharmonics i.e. Guitars/Pianos.

    """

    spectrum_distances = diff(convolved_spectrum)
    first_low_point = next(
        i for i, _ in enumerate(spectrum_distances) if spectrum_distances[i] > 0
    ) # Finds first rising edge
    peak = argmax(convolved_spectrum[first_low_point:]) + first_low_point
    interpolated_peak = interpolate_peak(convolved_spectrum, peak)
    return sampling_rate / interpolated_peak

def pitch_from_zero_crossings(signal: list, sampling_rate: int):
    """ Estimate pitch by simply counting the amount of zero-crossings.

        *Advantages*:
            - Good for intermittent stable frequencies, i.e. Guitar Tuners.
            - Fast to compute, don't need to apply an FFT.

        *Disadvantages*:
            - If there is lots of noise or multiple frequencies doesn't work.

    """
    indices = []
    for i, _ in enumerate(signal): # Find indices of zero-crossings
        if (signal[i - 1] > 0) and (signal[i] < 0):
            indices.append(i)

    crossings = [i - signal[i] / (signal[i + 1] - signal[i]) for i in indices]

    return sampling_rate / mean(diff(crossings))

def pitch_from_hps(spectrum: list, sampling_rate: int, max_harmonics: int):
    """ Estimate pitch using the harmonic product spectrum (HPS) Algorithm """
    harmonic_spectrum = abs(spectrum) # Keep positive values

    for harmonic_level in range(2, max_harmonics):
        downsampled_spectrum = harmonic_spectrum [::harmonic_level]
        harmonic_spectrum = harmonic_spectrum [:len(downsampled_spectrum)]
        pitch = argmax(harmonic_spectrum)
        harmonic_spectrum *= downsampled_spectrum

    interpolated_pitch = interpolate_peak(harmonic_spectrum, pitch)

    return sampling_rate * interpolated_pitch / len(spectrum)

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
    ) + peak
    return estimated_peak
