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
from rtmaii.analysis import spectral, spectrogram
from rtmaii.tasks import worker
from rtmaii.debugger import Locator
from pydispatch import dispatcher
from numpy import arange, mean, int16, resize, fft
LOGGER = logging.getLogger(__name__)
PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(PATH)
import time

class BaseCoordinator(threading.Thread):
    """ Parent class of all coordinator threads.

        Conducts the initiliazation of coordinator threads and their *required* attributes.

        **Attributes**:
            - queue (Queue): Coordinators queue of data to be processed.
            - peer_list (list): List of peer threads to communicate processed data with.
            - config (Config): Configuration options to use.

    """
    def __init__(self, config: object):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.setDaemon(True)
        self.queue = Queue()
        self.peer_list = []
        self.config = config
        self.start()

    def run(self):
        """ Executed after the thread is started, holds tasks for the thread to run. """
        raise NotImplementedError("Run should be implemented")

    def message_peers(self, data: object):
        """ Sends input data to each peered thread.

            **Args**:
                - data: The data to communicate.
        """
        for peer in self.peer_list:
            peer.queue.put(data)

class Coordinator(BaseCoordinator):
    """ First-line coordinator responsible for sending signal data to other threads.

        **Attributes**:
            - channels (List):
    """
    def __init__(self, config: object):
        self.channels = []
        LOGGER.info('Coordinator Initialized.')
        BaseCoordinator.__init__(self, config)

    def single_channel(self, config: object, channels: int):
        self.channels.append(FrequencyCoordinator(config, 1))

        while True:
            data = self.queue.get()

            if data is None:
                self.channels[0].queue.put(None)
                LOGGER.info('Coordinator Finishing Up.')
                break # No more data so cleanup and end thread.

            channel_signals = []

            for channel in range(channels):
                    channel_signals.append(data[channel::channels])

            averaged_signal = mean(channel_signals, axis=0, dtype=int16)

            dispatcher.send(signal='signal', sender=channel, data=averaged_signal) #TODO: Move to a locator.
            self.channels[0].queue.put(averaged_signal)

    def multi_channel(self, config: object, channels: int):
        for channel in range(config.get_config('channels')):
            self.channels.append(FrequencyCoordinator(config, channel))

        while True:
            data = self.queue.get()

            if data is None:
                for channel in range(channels):
                    self.channels[channel].queue.put(None)
                LOGGER.info('Coordinator Finishing Up.')
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
    def __init__(self, config: object, channel_name: int):
        BaseCoordinator.__init__(self, config)
        sampling_rate = config.get_config('sampling_rate')
        pitch_method = config.get_config('pitch_algorithm')

        if pitch_method == 'zero-crossings':
            self.peer_list.append(worker.ZeroCrossingWorker(sampling_rate, channel_name))
        elif pitch_method == 'auto-corellation':
            self.peer_list.append(worker.AutoCorrelationWorker(sampling_rate, channel_name))

        self.peer_list.append(SpectrumCoordinator(config, channel_name))
        self.channel_name = channel_name

    def run(self):

        fft_resolution = self.config.get_config('fft_resolution')
        start_analysis = False
        signal = []

        while not start_analysis:
            signal.extend(self.queue.get())
            if len(signal) >= fft_resolution:
                start_analysis = True

        while start_analysis:
            data = self.queue.get()
            if data is None:
                LOGGER.info('{} Frequency Coordinator finishing up'.format(self.channel_name))
                break # No more data so cleanup and end thread
            signal.extend(data)
            signal = signal[-fft_resolution:]
            print(len(signal))
            self.message_peers(signal)

class SpectrumCoordinator(BaseCoordinator):
    def __init__(self, config, channel_name):
        BaseCoordinator.__init__(self, config)
        self.sampling_rate = config.get_config('sampling_rate')
        pitch_method = config.get_config('pitch_algorithm')
        bands_of_interest = config.get_config('bands')
        self.channel_name = channel_name

        if pitch_method == 'hps':
            self.peer_list.append(worker.HPSWorker(self.sampling_rate, channel_name))
        elif pitch_method == 'fft':
            self.peer_list.append(worker.FFTWorker(self.sampling_rate, channel_name))

        self.peer_list.append(worker.BandsWorker(bands_of_interest, channel_name))

    def run(self):
        while True:
            signal = self.queue.get()
            if signal is None:
                break
            initial = time.time()
            frequency_spectrum = spectral.spectrum(signal, self.sampling_rate)
            print("spectrum conversion took {}".format(time.time()-initial))
            self.message_peers(frequency_spectrum)
            dispatcher.send(signal='spectrum', sender=self.channel_name, data=frequency_spectrum)


class SpectrogramCoordinator(BaseCoordinator):
    def __init__(self, config):
        BaseCoordinator.__init__(self, config)

    def run(self):
        ffts = []
        spectrogram_resolution = 10
        while True:
            fft = self.queue.get()
            if fft is None:
                break
            ffts.append(fft)
            ffts = ffts[-spectrogram_resolution:]

            if len(ffts) > spectrogram_resolution:
                dispatcher.send(signal='spectrogram', sender='spectrogram', data=ffts)
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
