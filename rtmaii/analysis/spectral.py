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
from scipy.signal import butter, lfilter, blackmanharris, hanning, hamming, spectrogram, fftconvolve, get_window
from scipy.fftpack import rfft, fft

def butter_bandpass(low_cut_off: int, high_cut_off: int, sampling_rate: int, order: int = 5):
    """ Cut out any frequencies out of the range we are interested in. """
    nyquist_frequency = 0.5 * sampling_rate
    low = low_cut_off / nyquist_frequency
    high = high_cut_off / nyquist_frequency
    numerator, denominator = butter(order, [low, high], btype='bandpass')
    return {'numerator': numerator, 'denominator': denominator}

def band_pass_filter(signal: list, numerator: list, denominator: list):
    """ Cut out any frequencies out of the range we are interested in. """
    filtered_signal = lfilter(numerator, denominator, signal)
    return filtered_signal

def new_window(N: int, window: str):
    """ Generate a new smoothing window for use.

        **Args**
            - `N`: the temporal signal to be converted to a spectrum.
            - `window`: the smoothing window to be applied.
    """
    window = get_window(window, N, True)
    return window

def convolve_spectrum(signal: list):
    """ Apply convolution to the input signal. """
    convol = fftconvolve(signal, signal[::-1], mode='full')
    convol = convol[len(convol)//2:] # Split bin in half removing negatives.
    return convol

def spectrum_transform(signal: list):
    """ Performs FFT on input signal """
    signal_length = len(signal)
    normalized_spectrum = fft(signal) / signal_length # Normalization
    return abs(normalized_spectrum[:int(signal_length/2)]) # Only need half of fft

def spectrum(signal: list,
             window: list,
             bp_filter: dict):
    """ Return the frequency spectrum of an input signal.

    **Args**
        - `signal`: the temporal signal to be converted to a spectrum.
        - `window`: the smoothing window to be applied.
        - `bp_filter`: the bandpass filter polynomials to apply to the signal.
             In the form of {'numerator': list, 'denominator': list}
    """
    windowed_signal = signal * window
    filtered_signal = band_pass_filter(windowed_signal, bp_filter['numerator'], bp_filter['denominator'])
    frequency_spectrum = spectrum_transform(filtered_signal)
    return frequency_spectrum


def spectro(signal, sampling_rate):
    """ Basic form of creating a spectrogram, can create our own using FFT bins """
    return spectrogram(signal, sampling_rate)
