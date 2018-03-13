"""
  TODO: Fill in docstring.
"""
import threading
import logging
from rtmaii.workqueue import WorkQueue
from rtmaii.analysis import spectral, bpm
from pydispatch import dispatcher
from numpy import mean, int16, pad, hanning, column_stack, absolute, power, log10, arange
from numpy.fft import fft as numpyFFT

LOGGER = logging.getLogger()
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
            - `channels` (List): list of channel threads to transmit signal to.
            - `peer_list` (list): List of peer threads to communicate processed data with.
    """
    def __init__(self, config: object, peer_list: list):
        LOGGER.info('Coordinator Initialized.')
        Coordinator.__init__(self, config, peer_list)
        self.update_attributes()

    def update_attributes(self):
        """ Update attributes of a hierarchy object using latest config values. """
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
        signal = []

        while len(signal) < frequency_resolution:
            signal.extend(self.queue.get_all())

        while True:
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
    """ Coordinator responsible for creating spectograms ... .

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
    """Coordinator responsible for finding beats and estimating bpm


    """
    def __init__(self, config, peer_list: list, channel_id):
        Coordinator.__init__(self, config, peer_list)
        LOGGER.info('BPM Initialized.')

    def run(self):
        beats = [] # List of beat intervals
        hbeats = [] # placeholder
        #bpmestimate = 0
        while True:
            data = self.queue.get()
            beat = bpm.beatdetection(data)
            if(beat == True):
                timedif = bpm.gettimedif()
                beats.append(timedif)
                beatdata = [beats, hbeats]
                self.message_peers(beatdata)

            dispatcher.send(signal='beats', sender=self, data=beat)
            #       add timeinterval from previous occurence of a beat to beats list.
            #       bpm = calculate average time interval