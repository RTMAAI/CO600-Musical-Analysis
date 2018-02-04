"""
  TODO: Fill in docstring.
  TODO: Come up with a better name than coordinator.
  TODO: Insert BPM Thread here.
  TODO: Implement Spectrogram creation.
"""
from queue import Queue
import threading
import json
import logging
import os
from rtmaii.analysis import frequency, pitch, key, spectral, spectrogram
from rtmaii.debugger import Locator
from pydispatch import dispatcher
from numpy import arange, mean, int16
LOGGER = logging.getLogger(__name__)
PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(PATH)

class BaseCoordinator(threading.Thread):
    """
        Conducts the initiliazation of coordinator threads to analyse queued input data.

    """
    def __init__(self, config):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.setDaemon(True)
        self.queue = Queue()
        self.config = config
        self.start()

    def run(self):
        raise NotImplementedError("Run should be implemented")

class Coordinator(BaseCoordinator):
    """
        Sends data to other analyzers.
    """
    def __init__(self, config):
        self.channels = []
        BaseCoordinator.__init__(self, config)

    def single_channel(self, config, channels):
        self.channels.append(FrequencyCoordinator(config, 1))

        while True:
            data = self.queue.get()

            if data is None:
                for channel in range(channels):
                    self.channels[channel].queue.put(None)
                LOGGER.info('Finishing up')
                break # No more data so cleanup and end thread.

            channel_signals = []

            for channel in range(channels):
                    channel_signals.append(data[channel::channels])

            averaged_signal = mean(channel_signals, axis=0, dtype=int16)

            dispatcher.send(signal='signal', sender=channel, data=averaged_signal) #TODO: Move to a locator.
            self.channels[0].queue.put(averaged_signal)

    def multi_channel(self, config, channels):
        for channel in range(config.get_config('channels')):
            self.channels.append(FrequencyCoordinator(config, channel))

        while True:
            data = self.queue.get()

            if data is None:
                for channel in range(channels):
                    self.channels[channel].queue.put(None)
                LOGGER.info('Finishing up')
                break # No more data so cleanup and end thread.

            # BPM Thread creation, passing through data.
            for channel in range(channels):
                channel_signal = data[channel::channels]
                dispatcher.send(signal='signal', sender=channel, data=channel_signal) #TODO: Move to a locator.
                self.channels[channel].queue.put(channel_signal)

    def run(self):
        channels = self.config.get_config('channels')
        merge_channels = self.config.get_config('merge_channels')

        if merge_channels:
            self.single_channel(self.config, channels)
        else:
            self.multi_channel(self.config, channels)

class FrequencyCoordinator(BaseCoordinator):
    def __init__(self, config, channel_name):
        BaseCoordinator.__init__(self, config)
        self.spectrogram_thread = SpectrogramCoordinator(config)
        self.channel_name = channel_name
        self.debugger = Locator.get_debugger()
        # Decorate run method based on what is actually needed?

    def get_spectrum(self, signal, sampling_rate):
        # If hps, fft, bands or genre enabled:
        frequency_spectrum = spectral.spectrum(signal, sampling_rate)
        dispatcher.send(signal='spectrum', sender=self.channel_name, data=frequency_spectrum) #TODO: Move to a locator.
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

        dispatcher.send(signal='pitch', sender=self.channel_name, data=estimated_pitch) #TODO: Move to a locator.
        return estimated_pitch

    def get_bands(self, spectrum, bands_of_interest):
        bands = frequency.frequency_bands(abs(spectrum), bands_of_interest)
        dispatcher.send(signal='bands', sender=self.channel_name, data=bands) #TODO: Move to a locator.
        return bands

    def get_key(self, pitch):
        estimated_key = key.note_from_pitch(pitch)
        dispatcher.send(signal='key', sender=self.channel_name, data=estimated_key) #TODO: Move to a locator.
        return estimated_key

    def run(self):

        # Abstract to just a basic call to get_pitch and get_frequency_bands.
        fft_resolution = self.config.get_config('fft_resolution')
        start_analysis = False
        signal = []
        sampling_rate = self.config.get_config('sampling_rate')
        bands_of_interest = self.config.get_config('bands')
        pitch_algorithm = self.config.get_config('pitch_algorithm')

        while not start_analysis:
            signal.extend(self.queue.get())
            if len(signal) >= fft_resolution:
                start_analysis = True

        while start_analysis:

            data = self.queue.get()
            if data is None:
                LOGGER.info('{} FFT Coordinator finishing up'.format(self.channel_name))
                break # No more data so cleanup and end thread
            signal.extend(data)
            signal = signal[-fft_resolution:]
            LOGGER.info('Thread %d started for channel %d!', threading.get_ident() ,self.channel_name)

            spectrum = self.get_spectrum(data, sampling_rate)
            estimated_pitch = self.get_pitch(data, spectrum, sampling_rate, pitch_algorithm)
            frequency_bands = self.get_bands(abs(spectrum), bands_of_interest)
            estimated_key = self.get_key(estimated_pitch)
            self.spectrogram_thread.queue.put(spectrum) # Push frequency_spectrum to spectrogram_thread for further processing.

            LOGGER.info('Channel %d Results:', self.channel_name)
            LOGGER.info(' Pitch: %f', estimated_pitch)
            LOGGER.info(' Bands: %s', frequency_bands)
            LOGGER.info(' Key: %s', estimated_key)

            dispatcher.send(signal='key', sender=self.channel_name, data=estimated_key) #TODO: Move to a locator.

            LOGGER.debug('%d finished!', threading.get_ident())

class SpectrogramCoordinator(BaseCoordinator):
    def __init__(self, config):
        BaseCoordinator.__init__(self, config)

    def run(self):
        ffts = []
        while True:
            fft = self.queue.get()
            if fft is None:
                print("Broken")
                break
            ffts.append(fft)
            # Also need to remove previous set of FFTs once there is enough data
            # dispatcher.send(signal='spectrogram', sender='spectrogram', data=ffts)
            # Create spectrogram when enough FFTs generated


class BPMCoordinator(BaseCoordinator):
    def __init__(self, config):
        BaseCoordinator.__init__(self, config)

    def run(self):
        beats = [] # List of beat intervals
        bpm = 0
        while True:
            pass
            # data = self.queue.get()
            # checkForBeat
            #   if beat:
            #       dispatcher.send(signal='bpm', sender=self)
            #       add timeinterval from previous occurence of a beat to beats list.
            #       bpm = calculate average time interval
