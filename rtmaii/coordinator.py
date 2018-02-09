"""
  TODO: Fill in docstring.
  TODO: Come up with a better name than coordinator.
  TODO: Insert BPM Thread here.
  TODO: Implement Spectrogram creation.
"""
from queue import Queue
import threading
import logging
from rtmaii.analysis import spectral, spectrogram
from rtmaii.worker import FFTWorker, AutoCorrelationWorker, BandsWorker, HPSWorker, ZeroCrossingWorker
from rtmaii.debugger import Locator
from pydispatch import dispatcher
from numpy import mean, int16
LOGGER = logging.getLogger(__name__)
class BaseCoordinator(threading.Thread):
    """ Parent class of all coordinator threads.

        Conducts the initiliazation of coordinator threads and their *required* attributes.

        **Attributes**:
            - `queue` (Queue): Coordinators queue of data to be processed.
            - `peer_list` (list): List of peer threads to communicate processed data with.
            - `config` (Config): Configuration options to use.

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
                - `data`: The data to send to each peer.
        """
        for peer in self.peer_list:
            peer.queue.put(data)

class Coordinator(BaseCoordinator):
    """ First-line coordinator responsible for sending signal data to other threads.

        **Attributes**:
            - channels (List): list of channel threads to transmit signal to.
    """
    def __init__(self, config: object):
        LOGGER.info('Coordinator Initialized.')
        BaseCoordinator.__init__(self, config)

        self.channels = []

    def single_channel(self, config: object, channels: int):
        """ Task configuration to handle analysis of an averaged single channel.

            **Args**:
                - `config` : configuration to be passed to peers.
                - `channels` : number of channels of input source.
        """
        self.peer_list.append(FrequencyCoordinator(config, 1))
        # self.peer_list.append(BPMCoordinator(config, 1)) PLACEHOLDER

        while True:
            data = self.queue.get()

            if data is None:
                self.message_peers(None)
                LOGGER.info('Coordinator Finishing Up.')
                break # No more data so cleanup and end thread.

            channel_signals = []

            for channel in range(channels):
                    channel_signals.append(data[channel::channels])
            averaged_signal = mean(channel_signals, axis=0, dtype=int16) # Average all channels.

            self.message_peers(averaged_signal)
            dispatcher.send(signal='signal', sender=channel, data=averaged_signal) #TODO: Move to a locator.

    def multi_channel(self, config: object, channels: int):
        """ Task configuration to handle analysis of multiple channels at the same time.

            **Args**:
                - `config` : configuration to be passed to peers.
                - `channels` : number of channels of input source.
        """

        for channel in range(config.get_config('channels')):
            self.peer_list.append(FrequencyCoordinator(config, channel))
            # self.peer_list.append(BPMCoordinator(config, channel)) PLACEHOLDER

        while True:
            data = self.queue.get()

            if data is None:
                self.message_peers(None)
                LOGGER.info('Coordinator Finishing Up.')
                break # No more data so cleanup and end thread.

            for channel in range(1, channels + 1):
                channel_signal = data[channel::channels]
                dispatcher.send(signal='signal', sender=channel, data=channel_signal) #TODO: Move to a locator.
                self.message_peers(channel_signal)

    def run(self):
        channels = self.config.get_config('channels')
        merge_channels = self.config.get_config('merge_channels')

        if merge_channels:
            self.single_channel(self.config, channels)
        else:
            self.multi_channel(self.config, channels)

class FrequencyCoordinator(BaseCoordinator):
    """ Frequency coordinator responsible for extending signal data before further analysis.

        **Attributes**:
            - `channel_id` (int): The ID of the channel being analysed.
            - `peer_list` (list): List of peer threads to communicate processed data with.
            - `config` (Config): Configuration options to use.

        **Notes**:
            - `Peers` created are dependent on configured tasks and algorithms.
    """
    def __init__(self, config: object, channel_id: int):
        BaseCoordinator.__init__(self, config)
        sampling_rate = config.get_config('sampling_rate')
        pitch_method = config.get_config('pitch_algorithm')

        self.peer_list.append(SpectrumCoordinator(config, channel_id))
        self.channel_id = channel_id

        if pitch_method == 'zero-crossings':
            self.peer_list.append(ZeroCrossingWorker(sampling_rate, channel_id))
        elif pitch_method == 'auto-correlation':
            self.peer_list.append(AutoCorrelationWorker(sampling_rate, channel_id))

    def run(self):
        """ Extend signal data to configured resolution before transmitting to peers. """

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
                LOGGER.info('{} Frequency Coordinator finishing up'.format(self.channel_id))
                self.message_peers(None)
                break # No more data so cleanup and end thread
            signal = signal[1024:]
            signal.extend(data)
            self.message_peers(signal)

class SpectrumCoordinator(BaseCoordinator):
    """ Spectrum coordinator responsible for creating spectrum data and transmitting to dependants.

        **Attributes**:
            - `channel_id` (int): The ID of the channel being analysed.
            - `peer_list` (list): List of peer threads to communicate processed data with.
            - `config` (Config): Configuration options to use.

        **Notes**:
            - `Peers` created are dependent on configured tasks and algorithms.
    """
    def __init__(self, config, channel_id):
        BaseCoordinator.__init__(self, config)

        pitch_method = config.get_config('pitch_algorithm')
        bands_of_interest = config.get_config('bands')
        tasks = config.get_config('tasks')
        fft_resolution = self.config.get_config('fft_resolution')

        self.sampling_rate = config.get_config('sampling_rate')
        self.channel_id = channel_id
        self.window = spectral.new_window(fft_resolution, 'blackmanharris')
        self.filter = spectral.butter_bandpass(10, 20000, self.sampling_rate, 5)

        if pitch_method == 'hps':
            self.peer_list.append(HPSWorker(self.sampling_rate, channel_id))
        elif pitch_method == 'fft':
            self.peer_list.append(FFTWorker(self.sampling_rate, channel_id))
        if tasks['genre']:
            self.peer_list.append(SpectrogramCoordinator(config, channel_id))
        if tasks['bands']:
            self.peer_list.append(BandsWorker(bands_of_interest, channel_id))

    def run(self):
        while True:
            signal = self.queue.get()
            if signal is None:
                self.message_peers(None)
                break

            frequency_spectrum = spectral.spectrum(signal, self.window, self.filter)
            self.message_peers(frequency_spectrum)
            dispatcher.send(signal='spectrum', sender=self.channel_id, data=frequency_spectrum)

class SpectrogramCoordinator(BaseCoordinator):
    def __init__(self, config, channel_id):
        BaseCoordinator.__init__(self, config)

    def run(self):
        ffts = []
        spectrogram_resolution = 10
        while True:
            fft = self.queue.get()
            if fft is None:
                self.message_peers(None)
                break
            ffts.append(fft)
            ffts = ffts[-spectrogram_resolution:]

            if len(ffts) > spectrogram_resolution:
                dispatcher.send(signal='spectrogram', sender='spectrogram', data=ffts)
            # Also need to remove previous set of FFTs once there is enough data
            # dispatcher.send(signal='spectrogram', sender='spectrogram', data=ffts)
            # Create spectrogram when enough FFTs generated

class BPMCoordinator(BaseCoordinator):
    def __init__(self, config, channel_id):
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
