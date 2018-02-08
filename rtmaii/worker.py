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