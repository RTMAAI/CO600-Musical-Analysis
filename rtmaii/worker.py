""" WORKER MODULE

    - This module contains our inbuilt Workers and the base Worker.

    All Workers inherit the Worker base class.

    Users wanting to create their own custom Worker, should inherit from Worker.

    For detailed information on Workers, please see our Readme on our Github.
    https://github.com/RTMAAI/CO600-Musical-Analysis
"""
import threading
import os
import logging
from rtmaii.workqueue import WorkQueue
from scipy.signal import resample
from rtmaii.analysis import frequency, pitch, key, spectral, bpm
from pydispatch import dispatcher
from numpy import reshape, array
from tensorflow.contrib import predictor

LOGGER = logging.getLogger()
class Worker(threading.Thread):
    """ Base worker class, responsible for initializing shared attributes.

        Attributes:
            - queue: queue of data to be processed by a worker.
            - channel_id: id of channel being analysed.

        Args:
            - queue_length: length of queue structure. [Default = 1]
                Workers are greedy and will only consider the latest item.
    """
    def __init__(self, config: dict = None, channel_id: int = None, queue_length: int = 1):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.queue = WorkQueue(queue_length)
        self.config = config
        self.channel_id = channel_id
        self.setDaemon(True)
        self.reset_attributes()
        self.start()

    def run(self):
        raise NotImplementedError("Run should be implemented")

    def reset_attributes(self):
        """ Inherited method, used for resetting any attributes on configuration changes. """
        pass

class GenrePredictorWorker(Worker):
    """ Worker responsible for analysing Spectrogram intensities for a genre.

        Kwargs:
            - config (Config): Configuration options to use.
            - channel_id: id of channel being analysed.

        Attributes:
            - exporter: Exports spectrograms to an external file for use future training set
            - predict_fn: Loads the 'predict' function of trained tensorflow model 
            - genredict: The dictionary from converting the number labels of predicted genre
    """
    def __init__(self, exporter: object, **kwargs: dict):
        Worker.__init__(self, kwargs['config'], kwargs['channel_id'])
        self.exporter = exporter
        
        self.predict_fn = predictor.from_saved_model(os.path.join(os.path.dirname(__file__), 'model'))
        self.accuracyChecker = []
        self.genredict = {}
        self.genredict[0] = 'Rock'
        self.genredict[1] = 'Folk'
        self.genredict[2] = 'Hip-Hop'
        self.genredict[3] = 'Electric'
        self.prediction = 'N/A'

    def run(self):
        
        while True:
            spectrogram = self.queue.get()
            spectrodata = spectrogram[2]
            testphoto = array(spectrodata)
            testphoto = testphoto.astype('float32')   
            
            try:
                testphoto = reshape(testphoto, (1,128,128,1))
                predictions = self.predict_fn({'x': testphoto})
                predictionclass = predictions['classes'][0]
                self.prediction = self.genredict[predictionclass]
                self.accuracyChecker.append(self.prediction)
               
                if(len(self.accuracyChecker) > 3):
                    self.accuracyChecker.pop(0)
                    print(self.accuracyChecker)
                    self.prediction = max(set(self.accuracyChecker), key=self.accuracyChecker.count)

                export_data = [spectrodata,self.prediction]
                self.exporter.queue.put(export_data)
            except:
                pass
            
            spectrogram = []

            dispatcher.send(signal='genre', sender=self.channel_id, data=self.prediction)

class BandsWorker(Worker):
    """ Worker responsible for analysing interesting frequency bands.

        Kwargs:
            - config (Config): Configuration options to use.
            - channel_id: id of channel being analysed.

        Attributes:
            - bands_of_interest: dictionary of frequency bands to analyse.
            - sampling_rate: sampling_rate of source being analysed.
    """
    def __init__(self, **kwargs: dict):
        Worker.__init__(self, kwargs['config'], kwargs['channel_id'])

    def reset_attributes(self):
        self.bands_of_interest = self.config.get_config('bands')
        self.sampling_rate = self.config.get_config('sampling_rate')

    def run(self):
        while True:
            spectrum = self.queue.get()
            frequency_bands = frequency.frequency_bands(spectrum,
                                                        self.bands_of_interest,
                                                        self.sampling_rate)
            dispatcher.send(signal='bands', sender=self.channel_id, data=frequency_bands)

class Key(object):
    """ Abstract class that has methods to analyse the key/note given a pitch. """
    @staticmethod
    def analyse_note(freq: float, channel_id: int):
        """ Extract the note of a given frequency..

            Args
                - freq: estimated frequency to analyse.
                - channel_id: channel the frequency was analysed from.
        """
        estimated_note = key.note_from_pitch(freq)
        dispatcher.send(signal='note', sender=channel_id, data=estimated_note)

    @staticmethod
    def analyse_key(freq: float, channel_id: int):
        """ Extract the key of a given frequency.

            Args
                - freq: estimated frequency to analyse.
                - channel_id: channel the frequency was analysed from.
        """
        pass

class ZeroCrossingWorker(Worker, Key):
    """ Worker responsible for analysing the fundamental pitch using the zero-crossings method.

        Kwargs:
            - config (Config): Configuration options to use.
            - channel_id: id of channel being analysed.

        Attributes:
            - sampling_rate: sampling_rate of source being analysed.
    """
    def __init__(self, **kwargs: dict):
        Worker.__init__(self, kwargs['config'], kwargs['channel_id'])

    def reset_attributes(self):
        self.sampling_rate = self.config.get_config('sampling_rate')

    def run(self):
        while True:
            signal = self.queue.get()
            estimated_pitch = pitch.pitch_from_zero_crossings(signal, self.sampling_rate)
            dispatcher.send(signal='pitch', sender=self.channel_id, data=estimated_pitch)
            self.analyse_note(estimated_pitch, self.channel_id)

class AutoCorrelationWorker(Worker, Key):
    """ Worker responsible for analysing the fundamental pitch using the auto-corellation method.

        Kwargs:
            - config (Config): Configuration options to use.
            - channel_id: id of channel being analysed.

        Attributes:
            - sampling_rate: sampling_rate of source being analysed.
    """
    def __init__(self, **kwargs: dict):
        Worker.__init__(self, kwargs['config'], kwargs['channel_id'])

    def reset_attributes(self):
        self.sampling_rate = self.config.get_config('sampling_rate')

    def run(self):
        while True:
            signal = self.queue.get()
            convolved_signal = spectral.convolve_signal(signal)
            estimated_pitch = pitch.pitch_from_auto_correlation(convolved_signal,
                                                                self.sampling_rate)
            dispatcher.send(signal='pitch', sender=self.channel_id, data=estimated_pitch)
            self.analyse_note(estimated_pitch, self.channel_id)

class HPSWorker(Worker, Key):
    """ Worker responsible for analysing pitch using the harmonic-product-spectrum method.

        Kwargs:
            - config (Config): Configuration options to use.
            - channel_id: id of channel being analysed.

        Attributes:
            - sampling_rate: sampling_rate of source being analysed.
    """
    def __init__(self, **kwargs: dict):
        Worker.__init__(self, kwargs['config'], kwargs['channel_id'])

    def reset_attributes(self):
        self.sampling_rate = self.config.get_config('sampling_rate')

    def run(self):
        while True:
            spectrum = self.queue.get()
            estimated_pitch = pitch.pitch_from_hps(spectrum, self.sampling_rate, 7)
            dispatcher.send(signal='pitch', sender=self.channel_id, data=estimated_pitch)
            self.analyse_note(estimated_pitch, self.channel_id)

class FFTWorker(Worker, Key):
    """ Worker responsible for analysing the fundamental pitch using the FFT method.

        Kwargs:
            - config (Config): Configuration options to use.
            - channel_id: id of channel being analysed.

        Attributes:
            - sampling_rate: sampling_rate of source being analysed.
    """
    def __init__(self, **kwargs: dict):
        Worker.__init__(self, kwargs['config'], kwargs['channel_id'])

    def reset_attributes(self):
        self.sampling_rate = self.config.get_config('sampling_rate')

    def run(self):
        while True:
            spectrum = self.queue.get()
            estimated_pitch = pitch.pitch_from_fft(spectrum, self.sampling_rate)
            dispatcher.send(signal='pitch', sender=self.channel_id, data=estimated_pitch)
            self.analyse_note(estimated_pitch, self.channel_id)

#class BeatsWorker(Worker):
#    """ Worker responsible for determining beats happening.

#    """
#    def __init__(self, channel_id: int):
#        Worker.__init__(self, channel_id)
#
#    def run(self):
#        while True:
#            data = self.queue.get()
#            beat = bpm.beatdetection(data)
#            timedif = bpm.gettimedif()
#            dispatcher.send(signal='beat', sender=self.channel_id, data=beat)
#            self.analyse_bpm(timedif, self.channel_id)


class BPMWorker(Worker):
    """ Worker responsible for determining beats happening.

    """
    def __init__(self, **kwargs: dict):
        Worker.__init__(self, kwargs['config'], kwargs['channel_id'])

    def run(self):
        while True:
            data = self.queue.get()
            beats = data[0]
            if(len(data)>1):
                hbeats = data[1]
            beats = bpm.cleanbeatarray(beats)
            bpmestimate = bpm.bpmsimple(beats)

            dispatcher.send(signal='bpm', sender=self.channel_id, data=bpmestimate)
            #self.analyse_bpm(timedif, self.channel_id)

#class BPMWorker(Worker):
    #""" Analyse bpm based on beat times """
    #def __init__(self, channel_id: int):
    #    Worker.__init__(self, args=(), kwargs=None)

    #def analyse_bpm(self, timedif):
    #    estimated_bpm = bpm.bpmsimple()
        #dispatcher.send(signal='key', sender=self.channel_id, data=estimated_key)
