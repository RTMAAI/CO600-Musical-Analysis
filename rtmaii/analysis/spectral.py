# INPUTS stream
# FUNCTIONS FFT, Windows, band-pass filter
# OUTPUTS frequency_spectrum, spectrogram
# TODO: Comment the shit out of this.

from scipy.signal import butter, lfilter, blackmanharris, hanning, hamming, spectrogram, fftconvolve
from scipy.fftpack import rfft,fft

def butter_bandpass(low_cut_off, high_cut_off, sampling_rate, order=5):
    """ Cut out any frequencies out of the range we are interested in. """
    nyquist_frequency = 0.5 * sampling_rate
    low = low_cut_off / nyquist_frequency
    high = high_cut_off / nyquist_frequency
    numerator, denominator = butter(order, [low, high], btype='bandpass')
    return numerator, denominator

def band_pass_filter(signal, low_cut_off, high_cut_off, sampling_rate, order=5):
    """ Cut out any frequencies out of the range we are interested in. """
    numerator, denominator = butter_bandpass(low_cut_off, high_cut_off, sampling_rate, order=order)
    filtered_signal = lfilter(numerator, denominator, signal)
    return filtered_signal

def window_signal(signal, window):
    """ Apply a given smoothing window to input signal. """
    return signal * window(len(signal))

def convolve_spectrum(signal):
    """ Apply convolution to the input signal. """
    convol = fftconvolve(signal, signal[::-1], mode='full')
    convol = convol[len(convol)//2:]
    return convol

def spectrum_transform(signal):
    """ Performs FFT on input signal """
    signal_length = len(signal)
    return fft(signal)/signal_length

def spectrum(signal, sampling_rate, window=blackmanharris, low_cut_off=20, high_cut_off=20000, order=5):
    """

    """
    windowed_signal = window_signal(signal, window)
    filtered_signal = band_pass_filter(windowed_signal, low_cut_off, high_cut_off, sampling_rate, order)
    frequency_spectrum = spectrum_transform(filtered_signal)
    return frequency_spectrum, windowed_signal, filtered_signal


def spectro(signal, sampling_rate):
    """ Basic form of creating a spectrogram, can create our own using FFT bins """
    return spectrogram(signal, sampling_rate)
