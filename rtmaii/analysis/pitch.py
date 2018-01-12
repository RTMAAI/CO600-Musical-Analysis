"""

"""
# INPUTS Spectrum, Stream
# FUNCTIONS auto_correlation, harmonic_product_spectrum, FFT fundamental, zero_crossings
# OUTPUTS Fundamental Frequency
# TODO: Comment the shit out of this.
# TODO: Look into other areas i.e. harmonic product spectrum.
import logging
from numpy import argmax, mean, diff, ravel
from scipy.signal import fftconvolve
from matplotlib.mlab import find

def pitch_from_fft(spectrum, sampling_rate):
    """ Estimate pitch from the frequency spectrum """
    basic_frequency = argmax(spectrum)
    estimated_frequency = interpolate_peak(abs(spectrum), basic_frequency)
    return sampling_rate * estimated_frequency /len(spectrum)

def pitch_from_auto_correlation(convolved_spectrum, sampling_rate):
    """ Estimate pitch using autocorrelation """

    # Find the first low point of the fft
    spectrum_distances = diff(convolved_spectrum)
    first_low_point = next(i for i in range(len(spectrum_distances)) if spectrum_distances[i] > 0) # Finds first rising edge
    peak = argmax(convolved_spectrum[first_low_point:]) + first_low_point
    interpolated_peak = interpolate_peak(convolved_spectrum, peak)
    return sampling_rate / interpolated_peak

def pitch_from_zero_crossings(signal, sampling_rate):
    """ Estimate pitch by counting zero-crossings """
    indices = []
    for i in range(len(signal)) : # Find indices of zero-crossings
        if (signal[i - 1] > 0) and (signal[i] < 0):
            indices.append(i)
        elif (signal[i - 1] < 0) and (signal[i] > 0):
            indices.append(i)

    crossings = indices

    return sampling_rate / mean(diff(crossings))

def interpolate_peak(spectrum, peak):
    """
        Uses quadratic interpolation of spectral peaks to get a better estimate of the peak.
        As the peak can sometimes1
        Based off: https://ccrma.stanford.edu/~jos/sasp/Quadratic_Interpolation_Spectral_Peaks.html

    """
    prev_neighbour = spectrum[peak-1]
    next_neighbour = spectrum[peak+1]
    estimated_peak = 1/2 * (prev_neighbour  - next_neighbour / (prev_neighbour  - 2 * spectrum[peak] + next_neighbour)) # + peak 
    return estimated_peak