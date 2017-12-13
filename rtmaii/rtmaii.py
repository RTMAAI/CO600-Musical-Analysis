# RUNS MAIN LOOP RECORDING AND ORCHESTRATING PYAUDIO STREAM
from queue import Queue
import wave
import threading
import json
import logging
import os
from numpy import arange, fromstring, int16
from pydispatch import dispatcher
import pyaudio
import matplotlib
matplotlib.use("Agg") # TODO: Find thread-safe plotting library for debugger.
import matplotlib.pyplot as p
from .analysis import frequency, pitch, key, spectral, spectrogram

PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(PATH)
PLOT_LOCK = threading.Lock()
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
LOGGER = logging.getLogger(__name__)

# TODO: Change to a plotting Class
def plot(time_span, sig, sampling_rate, frequency_spectrum, windowed_signal, channel_name):
    """
        Plots frequency and time domain graphs of the current channel being analysed.
    """
    PLOT_LOCK.acquire() # Currently need lock as pyplot is not thread safe.
    # Plot basic time domain graph of signal.
    p.subplot(2, 1, 1)
    p.plot(time_span, sig[::100])
    p.xlabel('Time')
    p.ylabel('Amplitude')
    p.title('Signal')

    # Plot frequency domain graph of signal (After windowing and BP filter)
    p.subplot(2, 1, 2)
    k = arange(len(sig))
    frq = k/(len(sig)/sampling_rate)
    frq = frq[0:int(len(sig)/2)]
    frequency_spectrum = abs(frequency_spectrum[:int(len(sig)/2)])
    p.plot(frq, frequency_spectrum)
    p.xlabel('Freq (Hz)')
    p.ylabel('|Amplitude(freq)|')

    try:
        freq_time = "{}/debug/{}.png".format(DIR_PATH, channel_name)
        p.savefig(freq_time, dpi=50)
    except IOError:
        LOGGER.error('Could save time/spectrum graph to %s', freq_time, exc_info=True)

    p.close()

    # Plot basic time domain graph of signal after windowing.
    p.subplot(2, 1, 2)
    p.plot(time_span, windowed_signal)
    p.xlabel('Time')
    p.ylabel('Amplitude')

    try:
        window = "{}/debug/{}.png".format(DIR_PATH, channel_name)
        p.savefig("{}/debug/{}-filtered.png".format(DIR_PATH, channel_name), dpi=50)
    except IOError:
        LOGGER.error('Could save windowed graph to %s', window, exc_info=True)

    p.close()

    # Release lock for next thread to plot graph.
    # TODO: look into thread safe plotting library.
    PLOT_LOCK.release()

def analysis_thread(thread_id, sig, timespan, config, channel_name, spectrogram_thread):
    """
        Thread to analyse a channel's sampled signal.
        Args:
            identifier (str) :
            sig (:obj:`list` of :obj:`float`) :
            timespan (:obj:`list` of :obj:`float`) :
            sampling_rate (:obj:`int`) :
            channel_name (str) :
        Process:
            1. Get estimated zero-crossings of signal in time domain.
            2. Get frequency spectrum of signal (Signal is filtered and windowed beforehand)
                i. Use frequency bins to get balance of each frequency band.
                ii. Use frequency bins to estimate the pitch.
            3. Get estimated pitch using auto-correlation.
                i. Use estimated pitch from auto-correlation for key detection.

        TODO: More processing, create different threads for different purposes.
    """

    #print("Thread {} started for channel {}!".format(thread_id, channel_name))

    sampling_rate = config['sampling_rate']
    zero_crossings = pitch.pitch_from_zero_crossings(sig, sampling_rate)
    frequency_spectrum, windowed_signal, filtered_signal = spectral.spectrum(sig, sampling_rate)
    spectrogram_thread.queue.put(frequency_spectrum)
    convolved_spectrum = spectral.convolve_spectrum(sig)
    fft_frequency = pitch.pitch_from_fft(frequency_spectrum, sampling_rate)
    frequency_bands = frequency.frequency_bands(abs(frequency_spectrum), config['bands'])
    auto_correlation = pitch.pitch_from_auto_correlation(convolved_spectrum, sampling_rate)
    estimated_key = key.note_from_pitch(auto_correlation)
    #freq, time, Sxx = spectral.spectro(sig, sampling_rate) TODO: Implement Spectrogram creation.

    # Write Anaylsis to JSON file for debugging
    # TODO: Use UI for debugging instead of web server. Super slow.
    debug_file = '{}/debug/{} data.json'.format(DIR_PATH, channel_name)

    try:
        with open(debug_file, 'w') as json_data:
            json_data.write(json.dumps({'channel': channel_name,
                                        'key': estimated_key,
                                        'zc': str(zero_crossings),
                                        'fft': str(fft_frequency),
                                        'autocorr': str(auto_correlation),
                                        'bands': frequency_bands}))
    except IOError:
        LOGGER.error('Could not open debug file: %s', debug_file, exc_info=True)

    # Debug statements TODO: enable verbose mode
    LOGGER.info('%s Results:', channel_name)
    LOGGER.info(' FFT Frequency: %d', fft_frequency)
    LOGGER.info(' Zero-Crossings Frequency: %f', zero_crossings)
    LOGGER.info(' Auto-Corellation Frequency: %f', auto_correlation)
    LOGGER.info(' Bands: %s', frequency_bands)
    LOGGER.info(' Pitch: %s', estimated_key)

    dispatcher.send(signal='frequency', sender=channel_name, data=estimated_key)

    plot(timespan[::100], sig, sampling_rate, frequency_spectrum,
         windowed_signal[::100], channel_name) # Currently hangs here a lot due to locking

    #print("{} finished!".format(thread_id))

class Coordinator(threading.Thread):
    """

    """
    def __init__(self, queue, config):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.setDaemon(True)
        self.queue = queue
        self.config = config
        self.spectrogram_thread = spectrogram.Spectrogram_thread(Queue())
        self.spectrogram_thread.setDaemon(True)
        self.spectrogram_thread.start()
        self.sig = []

    def run(self):
        identifier = 0
        channels = self.config['channels']

        while True:
            data = self.queue.get()
            if data is None:
                LOGGER.info('Finishing up')
                self.spectrogram_thread.queue.put(None)
                break # No more data so cleanup and end thread

            # TODO: Insert BPM Thread here.

            self.sig.extend(data) # Build up more data before doing Frequency Analysis

            if len(self.sig) >= self.config['fft_resolution'] * channels:
                temp_sig = self.sig
                self.sig = []

                if self.config['merge_channels']:
                    # TODO: merge channel data
                    pass
                else:
                    # 1024 standard frame count
                    time_step = 1.0/float(len(temp_sig)/channels) # sampling interval
                    time_span = arange(0, 1, time_step) # time vector
                    identifier += 1
                    for channel in range(1, channels + 1):
                        channel_name = "Channel {}".format(channel)
                        channel_signal = temp_sig[channel-1::channels]
                        thread = threading.Thread(target=analysis_thread,
                                                  args=(identifier,
                                                        channel_signal,
                                                        time_span,
                                                        self.config,
                                                        channel_name,
                                                        self.spectrogram_thread))
                        thread.setDaemon(True)
                        thread.start()

class Rtmaii(object):
    """
        TODO: Add ability to have list of tracks and configs
    """
    def __init__(self, callbacks, track=None, config_path=r'{}\config\sample_config.json'.format(DIR_PATH)):

        try:
            with open(config_path, 'r') as config_file:
                self.config = json.load(config_file)
        except IOError:
            LOGGER.error('Could not open config file: %s', config_path, exc_info=True)

        self.audio = pyaudio.PyAudio()

        if not track: # Current implementation for handling live input/recorded track
            self.track = False
            self.config['sampling_rate'] = 44100
            self.config['channels'] = 2
            pyaudio_kwargs = {
                'format': pyaudio.paInt16,
                'input': True,
                'frames_per_buffer': 1024
            }
        else:
            self.track = True
            self.waveform = wave.open(track)
            self.config['sampling_rate'] = self.waveform.getframerate()
            self.config['channels'] = self.waveform.getnchannels()
            pyaudio_kwargs = {
                'format': self.audio.get_format_from_width(self.waveform.getsampwidth()),
                'output': True
            }

        LOGGER.info(self.config['channels'])

        for callback in callbacks:
            dispatcher.connect(callback['function'], callback['signal'], sender=dispatcher.Any)


        def stream_callback(in_data, frame_count, time_info, status):
            '''
                Convert raw stream data into signal bin and
            '''

            data = fromstring(self.waveform.readframes(frame_count), dtype=int16) if self.track else in_data
            self.coordinator.queue.put(data)
            if status == 4: # Send finish request to coordinator when stream is ended.
                self.coordinator.queue.put(None)
            return (data, pyaudio.paContinue)

        pyaudio_kwargs['stream_callback'] = stream_callback
        pyaudio_kwargs['rate'] = self.config['sampling_rate']
        pyaudio_kwargs['channels'] = self.config['channels']

        self.stream = self.audio.open(**pyaudio_kwargs)

        self.coordinator = Coordinator(Queue(), self.config)
        LOGGER.info('Coordinator Initialized')

    def is_active(self):
        return self.coordinator.is_alive()

    def start(self):
        self.stream.start_stream()
        self.coordinator.start()

        debug_info = open('{}/debug/Channel Info.json'.format(DIR_PATH), 'w')

        channel_info = [{'id': '{}'.format(channel),
                         'img1':'Channel {}.png'.format(channel),
                         'img2': 'Channel {}-filtered.png'.format(channel),
                         'data':'Channel {} data.json'.format(channel)}
                        for channel in range(1, self.config['channels'] + 1)]

        debug_info.write(json.dumps(channel_info))
        LOGGER.info('Stream started')

    def stop(self):
        # stop stream
        self.stream.stop_stream()
        self.stream.close()
        if self.track:
            self.waveform.close()
