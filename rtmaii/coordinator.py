"""
  TODO: Fill in docstring.
"""
import threading
import logging
from rtmaii.workqueue import WorkQueue
from rtmaii.analysis import spectral
from pydispatch import dispatcher
from numpy import mean, int16, zeros, append, hanning, array, column_stack,fromstring, absolute, power, log10, arange
from numpy.fft import fft as numpyFFT

LOGGER = logging.getLogger(__name__)
class Coordinator(threading.Thread):
    """ Parent class of all coordinator threads.

        Conducts the initiliazation of coordinator threads and their *required* attributes.

        **Attributes**:
            - `queue` (Queue): Coordinators queue of data to be processed.
            - `peer_list` (list): List of peer threads to communicate processed data with.
            - `config` (Config): Configuration options to use.
            - `queue_length` (Int): Maximum length of a coordinator's queue, helps to cull items.

    """
    def __init__(self, config: object, peer_list: list, queue_length: int = None):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.setDaemon(True)
        self.queue = WorkQueue(queue_length)
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
    """ First-line coordinator responsible for sending signal data to other threads with unique channel data.

        **Attributes**:
            - channels (List): list of channel threads to transmit signal to.
            - `peer_list` (list): List of peer threads to communicate processed data with.
    """
    def __init__(self, config: object, peer_list: list):
        LOGGER.info('Coordinator Initialized.')
        Coordinator.__init__(self, config, peer_list)
        self.frames_per_sample = self.config.get_config('frames_per_sample')
        self.message_channel_data = self.single_channel if self.config.get_config('merge_channels') else self.multi_channel
        self.channels = []

    def message_channel_peer(self, data: object, channel: int = 0):
        for peer in self.peer_list[channel]:
            peer.queue.put(data)

    def pad_signal_length(self, data: object):
        return append(data, zeros(self.frames_per_sample - len(data)))

    def single_channel(self, data: object, channels: int):
        """ Task configuration to handle analysis of an averaged single channel.

            **Args**:
                - `data` : signal data to average and send to peered threads.
                - `channels` : number of channels of input source.
        """
        channel_signals = []

        for channel in range(channels):
                # Extract individual channel signals.
                signal_data = self.pad_signal_length(data[channel::channels])
                # Zero pad array as the data length is not always guaranteed to be == frames_per_sample (i.e. end of recording.)
                channel_signals.append(signal_data)

        averaged_signal = mean(channel_signals, axis=0, dtype=int16) # Average all channels.
        self.message_channel_peer(averaged_signal)
        dispatcher.send(signal='signal', sender=channel, data=averaged_signal)

    def multi_channel(self, data: object, channels: int):
        """ Task configuration to handle analysis of multiple channels at the same time.

            **Args**:
                - `data` : signal data to send to peered channel threads.
                - `channels` : number of channels of input source.
        """
        for channel in range(channels):
            channel_signal = self.pad_signal_length(data[channel::channels])
            dispatcher.send(signal='signal', sender=channel + 1, data=channel_signal)
            self.message_channel_peer(channel_signal, channel)

    def run(self):
        channels = self.config.get_config('channels')

        while True:
            data = fromstring(self.queue.get(), dtype=int16)
            self.message_channel_data(data, channels)

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

        frequency_resolution = self.config.get_config('frequency_resolution')
        start_analysis = False
        signal = []

        while not start_analysis:
            signal.extend(self.queue.get_all())
            if len(signal) >= frequency_resolution:
                start_analysis = True

        while start_analysis:
            data = self.queue.get_all()
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
        Coordinator.__init__(self, config, peer_list, 1)
        frequency_resolution = config.get_config('frequency_resolution')

        self.sampling_rate = config.get_config('sampling_rate')
        self.channel_id = channel_id
        self.window = spectral.new_window(frequency_resolution, 'hanning')
        self.filter = spectral.butter_bandpass(10, 20000, self.sampling_rate, 5)

    def run(self):
        while True:
            signal = self.queue.get()
            frequency_spectrum = spectral.spectrum(signal, self.window, self.filter)
            self.message_peers(frequency_spectrum)
            dispatcher.send(signal='spectrum', sender=self.channel_id, data=frequency_spectrum)

class FFTSCoordinator(Coordinator):
    def __init__(self, config, peer_list: list, channel_id):
        Coordinator.__init__(self, config, peer_list)
        self.window = hanning(1024)

    def run(self):
        spectrum_list = []
        spectrogram_resolution = 10
        ffts = []
        x = 0 
        spectrogram_resolution = 128
        
            
        while True:
            fft = self.queue.get()
            if fft is not None:
                fft = numpyFFT(fft * self.window)[:1024//2]
                #print("bar")
                if fft is None:
                    self.message_peers(None)
                    break

                ffts.append(fft)
                x = x + 1

                if x > spectrogram_resolution:
                    x = 0

                    ffts = ffts[-spectrogram_resolution:]            
                    self.message_peers(ffts)
                    
                    dispatcher.send(signal='spectrogram', sender='spectrogram', data=ffts)

                # Also need to remove previous set of FFTs once there is enough data
                #dispatcher.send(signal='spectrogram', sender='spectrogram', data=ffts)
                # Create spectrogram when enough FFTs generated

class SpectrogramCoordinator(Coordinator):
    """ Worker responsible for creating spectograms ... .

        **Args**:
            - `sampling_rate`: sampling_rate of source being analysed.
            - `channel_id`: id of channel being analysed.
    """
    def __init__(self, config, peer_list: list, channel_id, sampling_rate):
        Coordinator.__init__(self, channel_id, peer_list)
        self.sampling_rate = sampling_rate
        self.channel_id = channel_id


    def run(self):
        while True:
            ffts = self.queue.get()
            if ffts is None:
                break # No more data so cleanup and end thread.
            
            self.window = 1024
            
            ffts = column_stack(ffts)
            print(ffts.shape)
            ffts = absolute(ffts) * 2.0 / self.window
            ffts = ffts / power(2.0, 8* 2 - 1)
            ffts = (20 * log10(ffts)).clip(-120)

            time = arange(0, ffts.shape[1], dtype=float) * self.window / self.sampling_rate / 2
            frequecy = arange(0, self.window / 2, dtype=float) * self.sampling_rate / self.window
            
            smallerFFTS = []
            smallerF = []

            for i in range(0, len(ffts), 4):
                if i + 4 > len(ffts):
                    break

                meanF = 0
                meanFFTS = 0

                for j in range(i , i + 3):
                    meanF = meanF + frequecy[j] 
                    meanFFTS = meanFFTS + ffts[j]

                meanF = meanF + frequecy[j]/4 
                meanFFTS = meanFFTS + ffts[j]/4

                smallerF.append(meanF)
                smallerFFTS.append(meanFFTS)

            spectroData = [time, smallerF, smallerFFTS]
            self.message_peers(spectroData)
            dispatcher.send(signal='spectogramData', sender=self.channel_id, data=spectroData)


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