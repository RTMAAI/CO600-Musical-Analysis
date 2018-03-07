import threading
import os
from rtmaii.workqueue import WorkQueue
from rtmaii.analysis import frequency, pitch, key, spectral
from pydispatch import dispatcher
from numpy import arange, mean, int16, resize, column_stack, power, log10, absolute, reshape
from matplotlib import pyplot as plt
from tensorflow.contrib import predictor


class Worker(threading.Thread):
    """ Base worker class, responsible for initializing shared attributes.

        **Attributes**:
            - `queue`: queue of data to be processed by a worker.
            - `channel_id`: id of channel being analysed.
            - `queue_length`: length of queue structure. [Default = 1] Workers are greedy and will only consider the latest item.
    """
    def __init__(self, channel_id: int, queue_length: int = 1):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.queue = WorkQueue(queue_length)
        self.channel_id = channel_id
        self.setDaemon(True)
        self.start()

    def run(self):
        raise NotImplementedError("Run should be implemented")

class PitchWorker(Worker):
    """ Specialised worker that has a method to analyse the key given the pitch. """
    def __init__(self, channel_id: int):
        Worker.__init__(self, args=(), kwargs=None)

    def analyse_key(self, pitch):
        estimated_key = key.note_from_pitch(pitch)
        dispatcher.send(signal='key', sender=self.channel_id, data=estimated_key)

class GenrePredictorWorker(Worker):
    """ Worker responsible for creating spectograms ... .

        **Args**:
            - `sampling_rate`: sampling_rate of source being analysed.
            - `channel_id`: id of channel being analysed.
    """
    def __init__(self, sampling_rate: int, channel_id: int):
        Worker.__init__(self, channel_id)
        self.sampling_rate = sampling_rate
        self.predict_fn = predictor.from_saved_model(os.path.join(os.path.dirname(__file__), 'model'))
        self.dict = {}
        self.dict[0] = 'Folk'
        self.dict[1] = 'Hip-Hop'
        self.dict[2] = 'Pop'
        self.dict[3] = 'Rock'
    
    def run(self):
        
        while True:
            spectrogram = self.queue.get()[2]
            spectrogram = reshape(spectrogram, (1,128,128,1))
            predictions = self.predict_fn({'x': spectrogram})
            predictionClass = predictions['classes'][0]
            print(predictionClass)
            
            prediction = self.dict[predictionClass]

            print(predictions['probabilities'])

            dispatcher.send(signal='genre', sender=self.channel_id, data=prediction)

class BandsWorker(Worker):
    """ Worker responsible for analysing interesting frequency bands.

        **Args**:
            - `bands_of_interest`: dictionary of frequency bands to analyse.
            - `channel_id`: id of channel being analysed.
    """
    def __init__(self, bands_of_interest: dict, sampling_rate: int, channel_id: int):
        Worker.__init__(self, channel_id)
        self.bands_of_interest = bands_of_interest
        self.sampling_rate = sampling_rate

    def run(self):
        while True:
            spectrum = self.queue.get()
            frequency_bands = frequency.frequency_bands(abs(spectrum), self.bands_of_interest, self.sampling_rate)
            dispatcher.send(signal='bands', sender=self.channel_id, data=frequency_bands) #TODO: Move to a locator.

class Key(object):
    """ Abstract class that has a method to analyse the key given the pitch. """
    @staticmethod
    def analyse_key(pitch, channel_id):
        estimated_key = key.note_from_pitch(pitch)
        dispatcher.send(signal='key', sender=channel_id, data=estimated_key)

class ZeroCrossingWorker(Worker, Key):
    """ Worker responsible for analysing the fundamental pitch using the zero-crossings method.

        **Args**:
            - `sampling_rate`: sampling_rate of source being analysed.
            - `channel_id`: id of channel being analysed.
    """
    def __init__(self, sampling_rate: int, channel_id: int):
        Worker.__init__(self, channel_id)
        self.sampling_rate = sampling_rate

    def run(self):
        while True:
            signal = self.queue.get()
            estimated_pitch = pitch.pitch_from_zero_crossings(signal, self.sampling_rate)
            dispatcher.send(signal='pitch', sender=self.channel_id, data=estimated_pitch)
            self.analyse_key(estimated_pitch, self.channel_id)

class AutoCorrelationWorker(Worker, Key):
    """ Worker responsible for analysing the fundamental pitch using the auto-corellation method.

        **Args**:
            - `sampling_rate`: sampling_rate of source being analysed.
            - `channel_id`: id of channel being analysed.
    """
    def __init__(self, sampling_rate: int, channel_id: int):
        Worker.__init__(self, channel_id)
        self.sampling_rate = sampling_rate

    def run(self):
        while True:
            signal = self.queue.get()
            convolved_spectrum = spectral.convolve_spectrum(signal)
            estimated_pitch = pitch.pitch_from_auto_correlation(convolved_spectrum, self.sampling_rate)
            dispatcher.send(signal='pitch', sender=self.channel_id, data=estimated_pitch)
            self.analyse_key(estimated_pitch, self.channel_id)

class HPSWorker(Worker, Key):
    """ Worker responsible for analysing the fundamental pitch using the harmonic-product-spectrum method.

        **Args**:
            - `sampling_rate`: sampling_rate of source being analysed.
            - `channel_id`: id of channel being analysed.
    """
    def __init__(self, sampling_rate: int, channel_id: int):
        Worker.__init__(self, channel_id)
        self.sampling_rate = sampling_rate

    def run(self):
        while True:
            spectrum = self.queue.get()
            estimated_pitch = pitch.pitch_from_hps(spectrum, self.sampling_rate, 7)
            dispatcher.send(signal='pitch', sender=self.channel_id, data=estimated_pitch)
            self.analyse_key(estimated_pitch, self.channel_id)

class FFTWorker(Worker, Key):
    """ Worker responsible for analysing the fundamental pitch using the FFT method.

        **Args**:
            - `sampling_rate`: sampling_rate of source being analysed.
            - `channel_id`: id of channel being analysed.
    """
    def __init__(self, sampling_rate: int, channel_id: int):
        Worker.__init__(self, channel_id)
        self.sampling_rate = sampling_rate

    def run(self):
        while True:
            spectrum = self.queue.get()
            estimated_pitch = pitch.pitch_from_fft(spectrum, self.sampling_rate)
            dispatcher.send(signal='pitch', sender=self.channel_id, data=estimated_pitch)
            self.analyse_key(estimated_pitch, self.channel_id)