import threading
from queue import Queue
import time
from rtmaii.analysis import frequency, pitch, key, spectral, spectrogram
from pydispatch import dispatcher
from numpy import arange, mean, int16, resize

class BaseWorker(threading.Thread):
    def __init__(self, channel_name):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.channel_name = channel_name
        self.setDaemon(True)
        self.queue = Queue()
        self.start()

    def run(self):
        raise NotImplementedError("Run should be implemented")


class Frequency_Worker(threading.Thread):

    def __init__(self, data, config, channel_name):
        initial = time.time()
        sampling_rate = config.get_config('sampling_rate')
        bands_of_interest = config.get_config('bands')
        pitch_algorithm = config.get_config('pitch_algorithm')
        spectrum = self.get_spectrum(data, sampling_rate)
        dispatcher.send(signal='spectrum', sender=channel_name, data=spectrum) #TODO: Move to a locator.
        estimated_pitch = self.get_pitch(data, spectrum, sampling_rate, pitch_algorithm)
        dispatcher.send(signal='pitch', sender=channel_name, data=estimated_pitch) #TODO: Move to a locator.
        frequency_bands = self.get_bands(abs(spectrum), bands_of_interest)
        dispatcher.send(signal='bands', sender=channel_name, data=frequency_bands) #TODO: Move to a locator.
        # estimated_key = self.get_key(estimated_pitch)
        # dispatcher.send(signal='key', sender=channel_name, data=estimated_key) #TODO: Move to a locator.
        print("Worker took {} seconds".format(time.time() - initial))
        # LOGGER.info(' Channel %d Results:', self.channel_name)
        # LOGGER.info(' Pitch: %f', estimated_pitch)
        # LOGGER.info(' Bands: %s', frequency_bands)
        # LOGGER.info(' Key: %s', estimated_key)

    def get_spectrum(self, signal, sampling_rate):
        # If hps, fft, bands or genre enabled:
        frequency_spectrum = spectral.spectrum(signal, sampling_rate)
        return frequency_spectrum

    def get_pitch(self, signal, spectrum, sampling_rate, pitch_algorithm):
        # TODO: Shouldn't be in a loop should be initialized to use a certain algorithm.
        if pitch_algorithm == 'zero-crossings':
            estimated_pitch = pitch.pitch_from_zero_crossings(signal, sampling_rate)
        elif pitch_algorithm == 'hps':
            estimated_pitch = pitch.pitch_from_hps(spectrum, sampling_rate, 5)
        elif pitch_algorithm == 'auto-correlation':
            convolved_spectrum = spectral.convolve_spectrum(signal)
            estimated_pitch = pitch.pitch_from_auto_correlation(convolved_spectrum, sampling_rate)
        elif pitch_algorithm == 'fft':
            estimated_pitch = pitch.pitch_from_fft(spectrum, sampling_rate)
        return estimated_pitch

    def get_bands(self, spectrum, bands_of_interest):
        bands = frequency.frequency_bands(abs(spectrum), bands_of_interest)
        return bands

    def get_key(self, pitch):
        estimated_key = key.note_from_pitch(pitch)
        return estimated_key

class BandsWorker(BaseWorker):

    def __init__(self, bands_of_interest, channel_name):
        BaseWorker.__init__(self, channel_name)
        self.bands_of_interest = bands_of_interest

    def run(self):
        while True:
            spectrum = self.queue.get()
            if spectrum is None:
                break # No more data so cleanup and end thread.

            frequency_bands = frequency.frequency_bands(abs(spectrum), self.bands_of_interest)
            dispatcher.send(signal='bands', sender=self.channel_name, data=frequency_bands) #TODO: Move to a locator.

class ZeroCrossingWorker(BaseWorker):

    def __init__(self, sampling_rate, channel_name):
        BaseWorker.__init__(self, channel_name)
        self.sampling_rate = sampling_rate

    def run(self):
        while True:
            signal = self.queue.get()
            if signal is None:
                break # No more data so cleanup and end thread.

            estimated_pitch = pitch.pitch_from_zero_crossings(signal, self.sampling_rate)
            dispatcher.send(signal='pitch', sender=self.channel_name, data=estimated_pitch)

class AutoCorrelationWorker(BaseWorker):

    def __init__(self, sampling_rate, channel_name):
        BaseWorker.__init__(self, channel_name)
        self.sampling_rate = sampling_rate

    def run(self):
        while True:
            signal = self.queue.get()
            if signal is None:
                break # No more data so cleanup and end thread.

            convolved_spectrum = spectral.convolve_spectrum(signal)
            estimated_pitch = pitch.pitch_from_auto_correlation(convolved_spectrum, self.sampling_rate)
            dispatcher.send(signal='pitch', sender=self.channel_name, data=estimated_pitch)

class HPSWorker(BaseWorker):

    def __init__(self, sampling_rate, channel_name):
        BaseWorker.__init__(self, channel_name)
        self.sampling_rate = sampling_rate

    def run(self):
        while True:
            spectrum = self.queue.get()
            if spectrum is None:
                break # No more data so cleanup and end thread.

            estimated_pitch = pitch.pitch_from_hps(spectrum, self.sampling_rate, 5)
            dispatcher.send(signal='pitch', sender=self.channel_name, data=estimated_pitch)

class FFTWorker(BaseWorker):

    def __init__(self, sampling_rate, channel_name):
        BaseWorker.__init__(self, channel_name)
        self.sampling_rate = sampling_rate

    def run(self):
        while True:
            spectrum = self.queue.get()
            if spectrum is None:
                break # No more data so cleanup and end thread.

            estimated_pitch = pitch.pitch_from_fft(spectrum, self.sampling_rate)
            dispatcher.send(signal='pitch', sender=self.channel_name, data=estimated_pitch)