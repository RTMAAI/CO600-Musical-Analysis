""" SPECTRAL MODULE
    This module handles temporal to spectral signal conversion.

    **INPUTS**:
        Signal: Temporal wave form.

    **OUTPUTS**:
        Spectrum: Frequency spectrum of the input sample.
"""
from scipy.signal import butter, lfilter, fftconvolve, get_window
from scipy.fftpack import fft

def butter_bandpass(low_cut_off: int, high_cut_off: int, sampling_rate: int, order: int = 5) -> dict:
    """ Cut out any frequencies out of the range we are interested in.

        **Args**
            - `low_cut_off`: lower end of bandpass filter.
            - `high_cut_off`: upper end of bandpass filter.
            - `sampling_rate`: sampling rate of the signal being analysed.
            - `order`: magnitude of the filter created.
    """
    nyquist_frequency = 0.5 * sampling_rate
    low = low_cut_off / nyquist_frequency
    high = high_cut_off / nyquist_frequency
    numerator, denominator = butter(order, [low, high], btype='bandpass')
    return {'numerator': numerator, 'denominator': denominator}

def band_pass_filter(signal: list, numerator: list, denominator: list) -> list:
    """ Cut out any frequencies out of the range we are interested in.

        **Args**
            - `signal`: length of window to create.
            - `numerator`: numerator of filter.
            - `denominator`: denominator of filter.
    """
    filtered_signal = lfilter(numerator, denominator, signal)
    return filtered_signal

def new_window(window_length: int, window: str) -> list:
    """ Generate a new smoothing window for use.

        **Args**
            - `window_length`: length of window to create.
            - `window`: the smoothing window to be applied.
    """
    window = get_window(window, window_length, True)
    return window

def convolve_signal(signal: list) -> list:
    """ Apply convolution to the input signal.

        **Args**
            - `signal`: the signal to convolve.
    """
    convol = fftconvolve(signal, signal[::-1], mode='full')
    return convol[len(convol) // 2:] # Split bin in half removing negative lags.

def spectrum_transform(signal: list) -> list:
    """ Performs FFT on input signal, returns only positive half of spectrum.

        **Args**
            - `signal`: the signal to perform a fourier transform on.
    """
    signal_length = len(signal)
    normalized_spectrum = fft(signal) / signal_length # Normalization
    return normalized_spectrum[:signal_length // 2] # Only need half of fft output.

def spectrum(signal: list,
             window: list,
             bp_filter: dict = None) -> list:
    """ Return the frequency spectrum of an input signal.

        **Args**
            - `signal`: the temporal signal to be converted to a spectrum.
            - `window`: the smoothing window to be applied.
            - `bp_filter`: the bandpass filter polynomial coefficents to apply to the signal.
                In the form of {'numerator': list, 'denominator': list}
    """
    windowed_signal = signal * window
    filtered_signal = windowed_signal if bp_filter is None else band_pass_filter(windowed_signal, bp_filter['numerator'], bp_filter['denominator'])
    frequency_spectrum = spectrum_transform(filtered_signal)
    return frequency_spectrum
