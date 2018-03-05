'''
    Main script that is imported with the library.
'''
import wave
import json
import threading
import logging
import os
import time
from rtmaii.hierarchy import new_hierarchy
from rtmaii.configuration import Config
from numpy import int16
from pydispatch import dispatcher
import pyaudio

PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(PATH)
logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s')
LOGGER = logging.getLogger(__name__)

class Rtmaii(object):
    """ Interface for real-time musical analysis library.

        **Args**
            - `Callbacks`: List of dicts with a `callback` and the `signal` to will trigger it.
            - `Track`: The path of a track to be played, defaults to microphone input.
            - `Config`: Dict of settings to change.
            - `Mode`: Logging mode, options = {'DEBUG','WARNING','CRITICAL','INFO','ERROR'}

        **Example**
            ```python
                track = r'.\\Tracks\\LetItGo.wav'
                callbacks = [{'function': callback_function, 'signal':'frequency'}]
                config = {
                    "bands": {
                        "bass": {min: 200, max: 2000}
                    }
                }
                analyser = rtmaii.Rtmaii(callbacks, track, config)
                analyser.start()

                while analyser.is_active():
                    pass #Keep main thread running.
            ```
    """
    def __init__(self, callbacks: list, track: str = None, config: dict = {}, mode: str = 'ERROR'):

        self.config = Config(**config)
        self.audio = pyaudio.PyAudio()
        self.set_source(track)
        self.set_callbacks(callbacks)
        self.root = new_hierarchy(self.config)
        LOGGER.setLevel(mode)
        LOGGER.debug('RTMAII Initiliazed')

    def __stream_callback__(self, in_data, frame_count, time_info, status):
        """
            Convert raw stream data into signal bin and put data on the coordinator's queue.
        """
        data = self.waveform.readframes(frame_count) if hasattr(self, 'waveform') else in_data
        self.root.queue.put(data)
        return (data, pyaudio.paContinue)

    def is_active(self):
        """ Check that coordinator thread is still running.

            **Returns**
                - bool: True is alive, False otherwise.
        """
        return hasattr(self, 'stream') and self.stream.is_active()

    def start(self):
        """ Start audio stream. """

        pyaudio_settings = self.config.get_config('pyaudio_settings')
        pyaudio_settings['stream_callback'] = self.__stream_callback__

        if hasattr(self, 'waveform'):
            if self.waveform.tell() >= self.waveform.getnframes() - self.config.get_config('frames_per_sample'):
                self.waveform.setpos(0) # Reset wave file to initial position.

        self.stream = self.audio.open(**pyaudio_settings)
        self.stream.start_stream()

        LOGGER.info('Stream started')

    def stop(self):
        """ Stop the stream & close the track (if set). """
        self.stream.stop_stream()

    def set_config(self, **kwargs):
        """ Change configuration options, i.e. what bands should be look at. """
        self.config.set_config(**kwargs)

    def set_source(self, source=None, sampling_rate=None, channels=None):
        """ Change the analyzed source """
        # Stop stream, reinitialize with new settings, fire kill command to coordinator.
        if hasattr(self, 'stream'): self.stop()
        if source is None:
            if hasattr(self, 'waveform'): del self.waveform
            pyaudio_kwargs = {
                'rate': 44100,
                'channels': 2,
                'format': pyaudio.paInt16,
                'input': True
            }
        else:
            self.waveform = wave.open(source)
            pyaudio_kwargs = {
                'format': self.audio.get_format_from_width(self.waveform.getsampwidth()),
                'output': True,
                'rate': self.waveform.getframerate(),
                'channels': self.waveform.getnchannels()
            }
        pyaudio_kwargs['frames_per_buffer'] = self.config.get_config('frames_per_sample')
        self.config.set_source(pyaudio_kwargs)

    def set_callbacks(self, callbacks):
        """
            Attach supplied callbacks to signals on the dispatcher.
            Dispatcher is a loose form of the observer pattern.
            When the dispatcher is sent a signal, each observee will have their callback run.
        """
        for callback in callbacks:
            dispatcher.connect(callback['function'], callback['signal'], sender=dispatcher.Any)
