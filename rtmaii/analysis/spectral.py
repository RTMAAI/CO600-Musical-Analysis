'''
    This module handles temporal to spectral signal conversion.

    **INPUTS**:
        Signal: Temporal wave form.

    **OUTPUTS**:
        Spectrum: Frequency spectrum of the input sample.

    **Example**:

    TODO:
        - Finish comments
'''
from scipy.signal import butter, lfilter, blackmanharris, hanning, hamming, spectrogram, fftconvolve
from scipy.fftpack import rfft,fft

def butter_bandpass(low_cut_off: int, high_cut_off: int, sampling_rate: int, order: int = 5):
    """ Cut out any frequencies out of the range we are interested in. """
    nyquist_frequency = 0.5 * sampling_rate
    low = low_cut_off / nyquist_frequency
    high = high_cut_off / nyquist_frequency
    numerator, denominator = butter(order, [low, high], btype='bandpass')
    return numerator, denominator

def band_pass_filter(signal: list,
                     low_cut_off: int,
                     high_cut_off: int,
                     sampling_rate: int,
                     order: int = 5):
    """ Cut out any frequencies out of the range we are interested in. """
    numerator, denominator = butter_bandpass(low_cut_off, high_cut_off, sampling_rate, order=order)
    filtered_signal = lfilter(numerator, denominator, signal)
    return filtered_signal

def window_signal(signal: list, window: object):
    """ Apply a given smoothing window to input signal. """
    return signal * window(len(signal))

def convolve_spectrum(signal: list):
    """ Apply convolution to the input signal. """
    convol = fftconvolve(signal, signal[::-1], mode='full')
    convol = convol[len(convol)//2:]
    return convol

def spectrum_transform(signal: list):
    """ Performs FFT on input signal """
    signal_length = len(signal)
    return fft(signal)/signal_length

def spectrum(signal: list,
             sampling_rate: int,
             window: object = blackmanharris,
             low_cut_off: int = 20,
             high_cut_off: int = 20000,
             order: int = 5):
    """ Return the frequency spectrum of an input signal.

    **Args**
        - `signal`: the temporal signal to be converted to a spectrum.
        - `sampling_rate`: the sampling rate of the source.
        - `window`: the smoothing window to be applied.
        - `low_cut_off`: the lowest frequency to be observed.
        - `high_cut_off`: the highest frequency to be observed.
        - `order`: the order of the filter to be applied.
    """
    windowed_signal = window_signal(signal, window)
    filtered_signal = band_pass_filter(windowed_signal,
                                       low_cut_off,
                                       high_cut_off,
                                       sampling_rate,
                                       order)
    frequency_spectrum = spectrum_transform(filtered_signal)
    return frequency_spectrum, windowed_signal, filtered_signal


def spectro(signal, sampling_rate):
    """ Basic form of creating a spectrogram, can create our own using FFT bins """
    return spectrogram(signal, sampling_rate)
