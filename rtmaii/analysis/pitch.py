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
    true_frequency = parabolic(abs(spectrum), basic_frequency)[0]
    return sampling_rate * true_frequency /len(spectrum)

def pitch_from_auto_correlation(convolved_spectrum, sampling_rate):
    """ Estimate pitch using autocorrelation """

    # Find the first low point of the fft
    d = diff(convolved_spectrum)
    first_low_point = next(i for i in range(len(d)) if d[i] > 0) # Finds first rising edge

    peak = argmax(convolved_spectrum[first_low_point:]) + first_low_point
    px, py = parabolic(convolved_spectrum, peak)

    return sampling_rate / px

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

def parabolic(f, x):
    """ """
    xv = 1/2 * (f[x-1] - f[x+1]) / (f[x-1] - 2 * f[x] + f[x+1]) + x
    yv = f[x] - 1/4 * (f[x-1] - f[x+1]) * (xv - x)
    return (xv, yv)