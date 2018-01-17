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
from numpy import arange
LOGGER = logging.getLogger(__name__)
PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(PATH)

class BaseCoordinator(threading.Thread):
    """
        Conducts the initiliazation of coordinator threads to analyse queued song data.
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
        BaseCoordinator.__init__(self, config)
        self.channels = []
        for channel in range(config.get_config('channels')):
            self.channels.append(FrequencyCoordinator(config, channel))

    def run(self):
        channels = self.config.get_config('channels')
        merge_channels = self.config.get_config('merge_channels')

        while True:
            data = self.queue.get()
            if data is None:
                for channel in range(channels):
                    self.channels[channel].queue.put(None)
                LOGGER.info('Finishing up')
                break # No more data so cleanup and end thread

            # BPM Thread creation, passing through data.
            # Send

            # Merge channels
            # 1024 standard frame count
            time_step = 1.0/float(len(data)/channels) # sampling interval
            time_span = arange(0, 1, time_step) # time vector

            for channel in range(channels):
                channel_signal = data[channel::channels]
                self.channels[channel].queue.put(channel_signal)


class FrequencyCoordinator(BaseCoordinator):
    def __init__(self, config, channel_name):
        BaseCoordinator.__init__(self, config)
        self.spectrogram_thread = SpectrogramCoordinator(config)
        self.channel_name = channel_name
        self.debugger = Locator.get_debugger()


    def analyze_pitch(self):
        pass
    def analyze_frequencies(self):
        pass

    def run(self):
        fft_resolution = self.config.get_config('fft_resolution')
        start_analysis = False
        signal = []
        sampling_rate = self.config.get_config('sampling_rate')
        bands_of_interest = self.config.get_config('bands')

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

            zero_crossings = pitch.pitch_from_zero_crossings(signal, sampling_rate)
            frequency_spectrum = spectral.spectrum(signal, sampling_rate)

            fft_frequency = pitch.pitch_from_fft(frequency_spectrum, sampling_rate)
            frequency_bands = frequency.frequency_bands(abs(frequency_spectrum), bands_of_interest)

            self.spectrogram_thread.queue.put(frequency_spectrum) # Push frequency_spectrum to spectrogram_thread for further processing.

            convolved_spectrum = spectral.convolve_spectrum(signal)
            auto_correlation = pitch.pitch_from_auto_correlation(convolved_spectrum, sampling_rate)
            hps = pitch.pitch_from_hps(frequency_spectrum, sampling_rate, 5)
            estimated_key = key.note_from_pitch(auto_correlation)


            # Write Anaylsis to JSON file for debugging
            debug_file = '{}/debug/channel-{} data.json'.format(DIR_PATH, self.channel_name)

            try:
                with open(debug_file, 'w') as json_data:
                    json_data.write(json.dumps({'channel': self.channel_name,
                                                'key': estimated_key,
                                                'zc': str(zero_crossings),
                                                'fft': str(fft_frequency),
                                                'autocorr': str(auto_correlation),
                                                'bands': frequency_bands}))
            except IOError:
                LOGGER.error('Could not open debug file: %s', debug_file, exc_info=True)

            LOGGER.info('Channel %d Results:', self.channel_name)
            LOGGER.info(' FFT Frequency: %d', fft_frequency)
            LOGGER.info(' Zero-Crossings Frequency: %f', zero_crossings)
            LOGGER.info(' Auto-Corellation Frequency: %f', auto_correlation)
            LOGGER.info(' HPS Frequency: %f', hps)
            LOGGER.info(' Bands: %s', frequency_bands)
            LOGGER.info(' Pitch: %s', estimated_key)

            dispatcher.send(signal='frequency', sender=self.channel_name, data=estimated_key)

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
