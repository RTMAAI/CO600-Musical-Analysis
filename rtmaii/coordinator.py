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
from rtmaii.config import configuration
from pydispatch import dispatcher
from numpy import arange
LOGGER = logging.getLogger(__name__)
PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(PATH)

class Base_Coordinator(threading.Thread):
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

class Coordinator(Base_Coordinator):
    """
        Sends data to other analyzers.
    """
    def __init__(self, config):
        Base_Coordinator.__init__(self, config)
        self.channels = []
        for channel in range(config.get_config('channels')):
            self.channels.append(FFT_Coordinator(config, channel))

    def run(self):
        signal = []
        channels = self.config.get_config('channels')
        fft_resolution = self.config.get_config('fft_resolution')
        merge_channels = self.config.get_config('merge_channels')

        while True:
            data = self.queue.get()
            if data is None:
                for channel in range(channels):
                    self.channels[channel].queue.put(None)
                LOGGER.info('Finishing up')
                break # No more data so cleanup and end thread

            signal.extend(data) # Build up more data before doing Frequency Analysis
            if len(signal) >= fft_resolution * channels:
                temp_sig = signal
                signal = []

                if merge_channels:
                    # TODO: merge channel data
                    pass
                else:
                    # 1024 standard frame count
                    time_step = 1.0/float(len(temp_sig)/channels) # sampling interval
                    time_span = arange(0, 1, time_step) # time vector
                    for channel in range(channels):
                        channel_signal = temp_sig[channel::channels]
                        self.channels[channel].queue.put(channel_signal)

class FFT_Coordinator(Base_Coordinator):
    def __init__(self, config, channel_name):
        Base_Coordinator.__init__(self, config)
        self.channel_name = channel_name

    def run(self):
        spectrogram_thread = spectrogram.Spectrogram_thread(Queue())
        sampling_rate = self.config.get_config('sampling_rate')
        bands_of_interest = self.config.get_config('bands')

        while True:
            data = self.queue.get()
            if data is None:
                LOGGER.info('{} FFT Coordinator finishing up'.format(self.channel_name))
                break # No more data so cleanup and end thread

            LOGGER.info('Thread %d started for channel %d!', threading.get_ident() ,self.channel_name)

            zero_crossings = pitch.pitch_from_zero_crossings(data, sampling_rate)
            frequency_spectrum, windowed_signal, filtered_signal = spectral.spectrum(data, sampling_rate)

            fft_frequency = pitch.pitch_from_fft(frequency_spectrum, sampling_rate)
            frequency_bands = frequency.frequency_bands(abs(frequency_spectrum), bands_of_interest)

            spectrogram_thread.queue.put(frequency_spectrum) # Push frequency_spectrum to spectrogram_thread for further processing.

            convolved_spectrum = spectral.convolve_spectrum(data)
            auto_correlation = pitch.pitch_from_auto_correlation(convolved_spectrum, sampling_rate)
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

            # Debug statements TODO: enable verbose mode
            LOGGER.info('Channel %d Results:', self.channel_name)
            LOGGER.info(' FFT Frequency: %d', fft_frequency)
            LOGGER.info(' Zero-Crossings Frequency: %f', zero_crossings)
            LOGGER.info(' Auto-Corellation Frequency: %f', auto_correlation)
            LOGGER.info(' Bands: %s', frequency_bands)
            LOGGER.info(' Pitch: %s', estimated_key)

            dispatcher.send(signal='frequency', sender=self.channel_name, data=estimated_key)

            LOGGER.debug('%d finished!', threading.get_ident())


class BPM_Coordinator(Base_Coordinator):
    def __init__(self, config):
        Base_Coordinator.__init__(self, config)

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
