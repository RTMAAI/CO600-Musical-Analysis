"""
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
from numpy.linalg import norm

def normalize(v):
    Norm = norm(v)
    #print(norm)
    if Norm == 0: 
       return v
    return v / Norm



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
        self.reset_attributes()
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

    def reset_attributes(self):
        """ Inherited method, used for resetting any attributes on configuration changes. """
        pass

class RootCoordinator(Coordinator):
    """ First-line coordinator responsible for sending signal data to other threads with unique channel data.

        **Attributes**:
            - `channels` (List): list of channel threads to transmit signal to.
            - `peer_list` (list): List of peer threads to communicate processed data with.
    """
    def __init__(self, config: object, peer_list: list):
        LOGGER.info('Coordinator Initialized.')
        Coordinator.__init__(self, config, peer_list)

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

    def reset_attributes(self):
        """ Reset object attributes, to latest config values. """
        self.frequency_resolution = self.config.get_config('frequency_resolution')
        self.signal = []

    def run(self):
        """ Extend signal data to configured resolution before transmitting to peers. """
        while True:
            data = self.queue.get_all()
            self.signal.extend(data)
            self.signal = self.signal[-self.frequency_resolution:]
            if len(self.signal) >= self.frequency_resolution:
                self.message_peers(self.signal)

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
        self.channel_id = channel_id
        Coordinator.__init__(self, config, peer_list, 1)

    def reset_attributes(self):
        """ Reset object attributes, to latest config values. """
        frequency_resolution = self.config.get_config('frequency_resolution')
        self.sampling_rate = self.config.get_config('sampling_rate')
        self.window = spectral.new_window(frequency_resolution, 'hanning')
        self.filter = spectral.butter_bandpass(60, 18000, self.sampling_rate, 5)

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

                fft = normalize(fft)
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
            ffts = absolute(ffts) * 2.0 / sum(self.window)
            ffts = ffts / power(2.0, 8* 0)
            ffts = (20 * log10(ffts)).clip(-120)
            #print(ffts)

            time = arange(0, ffts.shape[1], dtype=float) * self.window / self.sampling_rate / 2
            frequecy = arange(0, self.window / 2, dtype=float) * self.sampling_rate / self.window
            
            smallerFFTS = []
            smallerF = []

            for i in range(0, len(ffts), 4):
                if i + 4 > len(ffts):
                    break
                
                meanFreq = (frequecy[i] + frequecy[i+1] + frequecy[i + 2] + frequecy[i + 3])
                meanffts = (ffts[i] + ffts[i+1] + ffts[i+2] + ffts[i+3])/4
                smallerFFTS.append(meanffts)
                smallerF.append(meanFreq)
                #print(meanffts)

            

            # for i in range(0, len(ffts), 4):
            #     if i + 4 > len(ffts):
            #         break

            #     meanF = 0
            #     meanFFTS = 0

            #     for j in range(i , i + 3):
            #         meanF = meanF + frequecy[j] 
            #         meanFFTS = meanFFTS + ffts[j]

            #     meanF = meanF + frequecy[j]/4 
            #     meanFFTS = meanFFTS + ffts[j]/4
            #     #print(meanFFTS)

            #     smallerF.append(meanF)
            #     smallerFFTS.append(meanFFTS)

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
                threshold = beat;
                dispatcher.send(signal='beats', sender=self, data=True)
            else:
                dispatcher.send(signal='beats', sender=self, data=False)
            #       add timeinterval from previous occurence of a beat to beats list.
            #       bpm = calculate average time interval