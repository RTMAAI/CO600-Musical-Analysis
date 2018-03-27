""" COORDINATOR MODULE
  TODO: Fill in docstring.
"""
import threading
import logging
import time
from rtmaii.workqueue import WorkQueue
from rtmaii.analysis import spectral, bpm
from pydispatch import dispatcher
from numpy import mean, int16, pad, hanning, column_stack, absolute, power, log10, arange, sum
from numpy.fft import fft as numpyFFT

LOGGER = logging.getLogger()
class Coordinator(threading.Thread):
    """ Parent class of all coordinator threads.

        Conducts the initiliazation of coordinator threads and their attributes.

        Attributes:
            - queue (WorkQueue): Coordinators queue of data to be processed.
            - peer_list (list): List of peer threads to communicate processed data with.
            - channel_id (int): id of channel being analysed.
            - config (Config): Configuration object of library to fetch analysis values from.
            - queue_length (int): Maximum length of a coordinator's queue, helps to cull items.
    """
    def __init__(self, config: object = None, channel_id: int = None, queue_length: int = None):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.setDaemon(True)
        self.channel_id = channel_id
        self.queue = WorkQueue(queue_length)
        self.peer_list = []
        self.config = config
        self.reset_attributes()
        self.start()

    def run(self):
        """ Executed after the thread is started, holds tasks for the thread to run. """
        raise NotImplementedError("Run should be implemented")

    def message_peers(self, data: object):
        """ Sends input data to each peered thread.

            Args:
                - data: The data to send to each peer.
        """
        for peer in self.peer_list:
            peer.queue.put(data)

    def reset_attributes(self):
        """ Inherited method, override to reset attributes on configuration changes. """
        pass

    def add_peer(self, thread_obj: str):
        """ Add a thread to the peer_list

            Args:
                - thread_obj: thread to add.
        """
        self.peer_list.append(thread_obj)

    def remove_peer(self, thread_id: str):
        """ Remove a thread from the peer_list

            Args:
                - thread: thread id to remove.
        """
        self.peer_list.remove(thread_id)

    def get_peer_list(self) -> list:
        """ Returns peer list of the coordinator. """
        return self.peer_list

class RootCoordinator(Coordinator):
    """ First-line coordinator responsible for managing and transmitting channel data.

        If multi channel analysis is enabled, the root coordinator will message each,
        channel hierarchy with their own channel data, otherwise the data is merged.

        Attributes:
            - config (obj): Configuration object to fetch analysis settings from. (Inherited)
            - merge_channels (bool): Merge channel data by averaging.
            - channels (int): number of channels of the audio source being analysed.
            - frame_size (int): size of frames received in each sample.
    """
    def __init__(self, **kwargs: dict):
        LOGGER.info('Coordinator Initialized.')
        Coordinator.__init__(self, kwargs['config'])

    def reset_attributes(self):
        """ Reset object attributes, to latest config values. """
        self.merge_channels = self.config.get_config('merge_channels')
        self.channels = self.config.get_config('channels')
        self.frame_size = self.config.get_config('frames_per_sample') * self.channels

    def run(self):
        """ RUN PROCESS
            1. Get signal data.
            2. Zero pad signal data to be equal to frame_size.
            3. Extract each channel's signal.
            4. (Optional): Average channel data, controlled by config.
            5. Send channel signals to peers.
        """
        while True:
            signal = self.queue.get()
            signal = pad(signal, (0, self.frame_size - len(signal)), 'constant')

            channel_signals = [signal[channel::self.channels] for channel in range(self.channels)]

            if self.merge_channels:
                channel_signals = [mean(channel_signals, axis=0, dtype=int16)]

            for index, channel_signal in enumerate(channel_signals):
                for peer in self.peer_list[index]:
                    peer.queue.put(channel_signal)
                dispatcher.send(signal='signal', sender=index, data=channel_signal)

class FrequencyCoordinator(Coordinator):
    """ Frequency coordinator responsible for extending signal data before further analysis.

        Attributes:
            - channel_id (int): The ID of the channel being analysed. (Inherited)
            - peer_list (list): List of peer threads to communicate processed data with. (Inherited)
            - config (obj): Configuration object to fetch analysis settings from. (Inherited)
            - extended_signal (list): Aggregated signal samples over time.
            - frequency_resolution (int): Threshold of extended_signal length, before messaging.

        Notes:
            - Peers created are dependent on configured tasks and algorithms.
    """
    def __init__(self, **kwargs: dict):
        Coordinator.__init__(self, kwargs['config'], kwargs['channel_id'])
        self.extended_signal = []

    def reset_attributes(self):
        """ Reset object attributes, to latest config values. """
        self.frequency_resolution = self.config.get_config('frequency_resolution')
        self.extended_signal = []

    def run(self):
        """ Extend signal data to configured resolution before transmitting to peers. """
        while True:
            data = self.queue.get_all()
            self.extended_signal.extend(data)
            self.extended_signal = self.extended_signal[-self.frequency_resolution:]
            if len(self.extended_signal) >= self.frequency_resolution:
                self.message_peers(self.extended_signal)

class SpectrumCoordinator(Coordinator):
    """ Spectrum coordinator responsible for creating spectrum data and transmitting to dependants.

        Attributes:
            - channel_id (int): The ID of the channel being analysed. (Inherited)
            - peer_list (list): List of peer threads to communicate processed data with. (Inherited)
            - config (obj): Configuration object to fetch analysis settings from. (Inherited)
            - sampling_rate (int): Sampling rate of audio source (Hz)
            - window (list): pre-processing smoothing window to apply to signal.
            - filter (dict): pre-processing filter coefficients to use against signal.

        Notes:
            - Peers created are dependent on configured tasks and algorithms.
    """
    def __init__(self, **kwargs: dict):
        Coordinator.__init__(self, kwargs['config'], kwargs['channel_id'], 1)

    def reset_attributes(self):
        """ Reset object attributes, to latest config values. """
        frequency_resolution = self.config.get_config('frequency_resolution')
        self.sampling_rate = self.config.get_config('sampling_rate')
        self.window = spectral.new_window(frequency_resolution, 'hanning')
        self.filter = spectral.butter_bandpass(60, 18000, self.sampling_rate, 5)

    def run(self):
        """ Convert input signal into it's frequency spectrum equivalent. """
        while True:
            signal = self.queue.get()
            frequency_spectrum = spectral.spectrum(signal, self.window, self.filter)
            self.message_peers(frequency_spectrum)
            dispatcher.send(signal='spectrum', sender=self.channel_id, data=frequency_spectrum)

class FFTSCoordinator(Coordinator):
    """ FFTS coordinator responsible for creating and collect 128 spectrums for creating a spectrogram.

        Attributes:
            - channel_id (int): The ID of the channel being analysed. (Inherited)
            - peer_list (list): List of peer threads to communicate processed data with. (Inherited)
            - config (obj): Configuration object to fetch analysis settings from. (Inherited)
            - window (list): pre-processing smoothing window to apply to signal.
            - spectrogram_resolution (int): 

        Notes:
            - Peers created are dependent on configured tasks and algorithms.
    """

    def __init__(self, **kwargs: dict):
        """ Reset object attributes, to latest config values. """
        Coordinator.__init__(self, kwargs['config'], kwargs['channel_id'])
        self.window = spectral.new_window(1024, 'hanning')
        self.spectrogram_resolution = 128

    def run(self):
        """ Reset object attributes, to latest config values. """
        ffts = []
        while True:
            fft = self.queue.get()
            if fft is not None:
                fft = spectral.spectrum(fft, self.window, None)
                fft = spectral.normalizorFFT(fft)

                if fft is None:
                    self.message_peers(None)
                    break

                ffts.append(fft)
                ffts = ffts[-self.spectrogram_resolution:]
                if len(ffts) ==  self.spectrogram_resolution:

                    self.message_peers(ffts)       
                    dispatcher.send(signal='spectrogram', sender='spectrogram', data=ffts)

class SpectrogramCoordinator(Coordinator):
    """ Spectrogram coordinator responsible for creating a spectrogram.

        Attributes:
            - channel_id (int): The ID of the channel being analysed. (Inherited)
            - peer_list (list): List of peer threads to communicate processed data with. (Inherited)
            - config (obj): Configuration object to fetch analysis settings from. (Inherited)
            - sampling_rate (int): Sampling rate of audio source (Hz)
            - window (list): pre-processing smoothing window to apply to signal.

        Notes:
            - Peers created are dependent on configured tasks and algorithms.
    """
    def __init__(self, **kwargs: dict):
        Coordinator.__init__(self, kwargs['config'], kwargs['channel_id'])
        self.window = 1024

    def reset_attributes(self):
        self.sampling_rate = self.config.get_config('sampling_rate')

    def run(self):
        while True:
            ffts = self.queue.get()
            if ffts is None:
                break 
            
            ffts = column_stack(ffts)
            ffts = spectral.convertingMagnitudeToDecibel(ffts, self.window)          
            
            time = arange(0, 128, dtype=float) * self.window / self.sampling_rate / 2
            frequecy = arange(0, self.window / 2, dtype=float) * self.sampling_rate / self.window
            
            smallerffts = []
            smallerfreq = []

            for i in range(0, len(ffts), 4):
                if i + 4 > len(ffts) and len(smallerffts) == 128:
                    break
                
                meanfreq = (frequecy[i] + frequecy[i+1] + frequecy[i + 2] + frequecy[i + 3])
                meanffts = (ffts[i] + ffts[i+1] + ffts[i+2] + ffts[i+3])/4
                smallerffts.append(meanffts)
                smallerfreq.append(meanfreq)

            spectrodata = [time, smallerfreq, smallerffts]
            self.message_peers(spectrodata)
            dispatcher.send(signal='spectogramData', sender=self.channel_id, data=spectrodata)


class BPMCoordinator(Coordinator):
    """Coordinator responsible for finding beats and estimating bpm


    """
    def __init__(self, **kwargs: dict):
        Coordinator.__init__(self, kwargs['config'], kwargs['channel_id'])
        LOGGER.info('BPM Initialized.')

    def run(self):
        beats = [] # List of beat intervals
        hbeats = [] # placeholder
        timelast = time.clock()
        threshold = 0
        descrate = 100

        while True:
            threshold -= descrate
            data = self.queue.get()
            beat = bpm.beatdetectionnew(data, threshold)
            if(beat != False):
                beattime = time.clock()
                beats.append(beattime - timelast)
                timelast = beattime
                beatdata = [beats, hbeats]
                self.message_peers(beatdata)
                threshold = beat
                dispatcher.send(signal='beats', sender=self, data=True)
            else:
                dispatcher.send(signal='beats', sender=self, data=False)
            #       add timeinterval from previous occurence of a beat to beats list.
            #       bpm = calculate average time interval
