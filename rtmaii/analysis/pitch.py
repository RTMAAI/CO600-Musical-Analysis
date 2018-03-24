""" PITCH MODULE
    This module handles any pitch based analysis.

    INPUTS:
        Spectrum: a bin of frequencies and their amplitudes.
        Signal: temporal wave form.

    OUTPUTS:
        Pitch (Fundamental Frequency): the pitch of the input.
"""
from numpy import argmax, mean, diff, real
from scipy.signal import decimate

def pitch_from_fft(spectrum: list, sampling_rate: int) -> float:
    """ Estimate pitch from the frequency spectrum.

        Args:
            - spectrum: the frequency bin to analyze.
            - sampling_rate: the sampling rate of the audio source.

        Advantages:
            - More accurate than Zero-crossings.

        Disadvantages:
            - Not great at detecting pitch with multiple harmonics that
              have a higher amplitude than the fundamental frequency.
    """
    basic_frequency = argmax(spectrum)
    interpolated_peak = interpolate_peak(spectrum, basic_frequency)
    return sampling_rate * interpolated_peak / (len(spectrum) * 2) # Convert to Hz

def pitch_from_auto_correlation(convolved_signal: list, sampling_rate: int) -> float:
    """ Estimate pitch using the autocorrelation method.

        Args:
            - convolved_spectrum: the convolved frequency bin to analyze.
            - sampling_rate: the sampling rate of the audio source.

        Advantages:
            - Good for repetitive wave forms, i.e. sine waves/saw tooths.
            - Represents a pitch closer to what humans hear.

        Disadvantages:
            - Requires a convolution to be applied which can be expensive.
            - Not great with inharmonics i.e. Guitars/Pianos.
    """
    signal_distances = diff(convolved_signal)
    first_low_point = next(
        i for i, _ in enumerate(signal_distances) if signal_distances[i] > 0
    ) # Finds first rising edge
    peak = argmax(convolved_signal[first_low_point:]) + first_low_point
    interpolated_peak = interpolate_peak(convolved_signal, peak)
    return sampling_rate / interpolated_peak # Convert to Hz

def pitch_from_zero_crossings(signal: list, sampling_rate: int) -> float:
    """ Estimate pitch by simply counting the amount of zero-crossings.

        Args:
            - signal: the signal bin to analyze.
            - sampling_rate: the sampling rate of the audio source.

        Advantages:
            - Good for intermittent stable frequencies, i.e. Guitar Tuners.
            - Fast to compute, don't need to apply an FFT.

        Disadvantages:
            - If there is lots of noise or multiple frequencies doesn't work.
    """
    indices = []
    for i, _ in enumerate(signal): # Find indices of zero-crossings
        if (signal[i - 1] > 0) and (signal[i] < 0):
            indices.append(i)
    # Linear interpolation, gives a more accurate result, to a few decimal places.
    crossings = [i - signal[i] / (signal[i + 1] - signal[i]) for i in indices]

    return sampling_rate / mean(diff(crossings)) # Convert to Hz

def pitch_from_hps(spectrum: list, sampling_rate: int, max_harmonics: int) -> float:
    """ Estimate pitch using the harmonic product spectrum (HPS) Algorithm

        Args:
            - spectrum: the frequency bin to analyze.
            - sampling_rate: the sampling rate of the audio source.
            - max_framonics the sampling rate of the audio source.
    """
    harmonic_spectrum = spectrum.copy()

    for harmonic_level in range(2, max_harmonics):
        # Downsample using anti-aliasing, = better results
        downsampled_spectrum = decimate(spectrum, harmonic_level)
        # Amplify any frequencies based on harmonics.
        harmonic_spectrum[:len(downsampled_spectrum)] *= downsampled_spectrum

    pitch = argmax(harmonic_spectrum)

    interpolated_pitch = interpolate_peak(harmonic_spectrum, pitch)

    return sampling_rate * interpolated_pitch / (len(spectrum) * 2) # Convert to Hz

def interpolate_peak(spectrum: list, peak: int) -> float:
    """ Uses quadratic interpolation of spectral peaks to get a better estimate of the peak.

        Args:
            - spectrum: the frequency bin to analyze.
            - peak: the location of the estimated peak in the spectrum list.

        Based off: https://ccrma.stanford.edu/~jos/sasp/Quadratic_Interpolation_Spectral_Peaks.html
    """
    prev_neighbour = spectrum[peak-1]
    next_neighbour = spectrum[peak+1]
    peak_value = spectrum[peak]
    estimated_peak = (next_neighbour
                      - prev_neighbour) / (2 * peak_value - prev_neighbour - next_neighbour) + peak
    return real(estimated_peak) # Only return real component.
