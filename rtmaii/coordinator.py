"""
  TODO: Fill in docstring.
"""
from queue import Queue
import threading
import logging
from rtmaii.analysis import spectral, spectrogram
from pydispatch import dispatcher
from numpy import mean, int16, zeros, append
LOGGER = logging.getLogger(__name__)
class Coordinator(threading.Thread):
    """ Parent class of all coordinator threads.

        Conducts the initiliazation of coordinator threads and their *required* attributes.

        **Attributes**:
            - `queue` (Queue): Coordinators queue of data to be processed.
            - `peer_list` (list): List of peer threads to communicate processed data with.
            - `config` (Config): Configuration options to use.

    """
    def __init__(self, config: object, peer_list: list):
        threading.Thread.__init__(self, args=(), kwargs=None)

        self.setDaemon(True)
        self.queue = Queue()
        self.peer_list = peer_list
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

class RootCoordinator(Coordinator):
    """ First-line coordinator responsible for sending signal data to other threads.

        **Attributes**:
            - channels (List): list of channel threads to transmit signal to.
            - `peer_list` (list): List of peer threads to communicate processed data with.
    """
    def __init__(self, config: object, peer_list: list):
        LOGGER.info('Coordinator Initialized.')
        Coordinator.__init__(self, config, peer_list)
        self.frames_per_sample = self.config.get_config('frames_per_sample')
        self.channels = []

    def single_channel(self, config: object, channels: int):
        """ Task configuration to handle analysis of an averaged single channel.

            **Args**:
                - `config` : configuration to be passed to peers.
                - `channels` : number of channels of input source.
        """

        while True:
            data = self.queue.get()
            channel_signals = []

            for channel in range(channels):
                    # Extract individual channel signals.
                    signal_data = data[channel::channels]
                    # Zero pad array as the data length is not always guaranteed to be == frames_per_sample (i.e. end of recording.)
                    padded_signal_data = append(signal_data, zeros(self.frames_per_sample - len(signal_data)))
                    channel_signals.append(padded_signal_data)

            averaged_signal = mean(channel_signals, axis=0, dtype=int16) # Average all channels.

            self.message_peers(averaged_signal)
            dispatcher.send(signal='signal', sender=channel, data=averaged_signal) #TODO: Move to a locator.

    def multi_channel(self, config: object, channels: int):
        """ Task configuration to handle analysis of multiple channels at the same time.

            **Args**:
                - `config` : configuration to be passed to peers.
                - `channels` : number of channels of input source.
        """

        while True:
            data = self.queue.get()

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

class FrequencyCoordinator(Coordinator):
    """ Frequency coordinator responsible for extending signal data before further analysis.

        **Attributes**:
            - `channel_id` (int): The ID of the channel being analysed.
            - `peer_list` (list): List of peer threads to communicate processed data with.
            - `config` (Config): Configuration options to use.

        **Notes**:
            - `Peers` created are dependent on configured tasks and algorithms.
    """
    def __init__(self, config: object, peer_list: list, channel_id: int):
        Coordinator.__init__(self, config, peer_list)

        self.channel_id = channel_id

    def run(self):
        """ Extend signal data to configured resolution before transmitting to peers. """

        frequency_resolution = self.config.get_config('frequency_samples') * self.config.get_config('frames_per_sample')
        start_analysis = False
        signal = []

        while not start_analysis:
            signal.extend(self.queue.get())
            if len(signal) >= frequency_resolution:
                start_analysis = True

        while start_analysis:
            data = self.queue.get()
            signal = signal[len(data):]
            signal.extend(data)
            self.message_peers(signal)

class SpectrumCoordinator(Coordinator):
    """ Spectrum coordinator responsible for creating spectrum data and transmitting to dependants.

        **Attributes**:
            - `channel_id` (int): The ID of the channel being analysed.
            - `peer_list` (list): List of peer threads to communicate processed data with.
            - `config` (Config): Configuration options to use.

        **Notes**:
            - `Peers` created are dependent on configured tasks and algorithms.
    """
    def __init__(self, config: object, peer_list: list, channel_id: int):
        Coordinator.__init__(self, config, peer_list)
        frequency_samples = config.get_config('frequency_samples')
        frames_per_sample = config.get_config('frames_per_sample')

        self.sampling_rate = config.get_config('sampling_rate')
        self.channel_id = channel_id
        self.window = spectral.new_window(frequency_samples * frames_per_sample, 'hanning')
        self.filter = spectral.butter_bandpass(10, 20000, self.sampling_rate, 5)

    def run(self):
        while True:
            signal = self.queue.get()
            frequency_spectrum = spectral.spectrum(signal, self.window, self.filter)
            self.message_peers(frequency_spectrum)
            dispatcher.send(signal='spectrum', sender=self.channel_id, data=frequency_spectrum)

class SpectrogramCoordinator(Coordinator):
    def __init__(self, config, peer_list: list, channel_id):
        Coordinator.__init__(self, config, peer_list)

    def run(self):
        spectrum_list = []
        spectrogram_resolution = 10
        while True:
            fft = self.queue.get()
            spectrum_list.append(fft)

            if len(spectrum_list) > spectrogram_resolution:
                spectrum_list = spectrum_list[-spectrogram_resolution:]
                dispatcher.send(signal='spectrogram', sender='spectrogram', data=spectrum_list)
            # Also need to remove previous set of FFTs once there is enough data
            # dispatcher.send(signal='spectrogram', sender='spectrogram', data=ffts)
            # Create spectrogram when enough FFTs generated

class BPMCoordinator(Coordinator):
    def __init__(self, config, peer_list: list, channel_id):
        Coordinator.__init__(self, config, peer_list)

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