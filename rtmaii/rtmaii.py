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
        LOGGER.debug('RTMAAI Initiliazed')

    def __stream_callback__(self, in_data, frame_count, time_info, status):
        """ Convert raw stream data into signal bin and put data on the coordinator's queue. """
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

    def pause(self):
        """ Pause the stream. Analogous to stop if analysing live music. """
        self.stream.stop_stream()

    def stop(self):
        """ Stop the stream & reset track's position (if set). """
        if hasattr(self, 'waveform'):
            self.waveform.setpos(0) # Reset wave file to initial position.
        self.stream.stop_stream()

    def set_config(self, **kwargs: dict):
        """ Change configuration options, i.e. what bands should be look at. """
        self.config.set_config(**kwargs)

    def set_source(self, source: object = None, **kwargs: dict):
        """ Change the analyzed source. By default this sets the stream to use your default input device with it's default configuration.

            When specifying an input device in which you have changed the configuration such as a higher sampling rate, please supply these in the kwargs.

            ```python
                set_source(**{'rate' : 96000, 'channels' : 3})
            ```
            If this is not set to match your system's configuration there may be artefacts in the analysis.

            **Args**:
                - `source`: Int (Index of input device to use) || String (Path of audio file to analyse)
                - `kwargs`: Additional configuration to be used in Pyaudio. (Please see our readme for more information.)
        """
        if hasattr(self, 'stream'): self.stop()
        if type(source) is int or source is None:
            # Extract relevant configuration to use in waveform.
            if source is None:
                device = self.audio.get_default_input_device_info()
            else:
                try:
                    device = self.audio.get_device_info_by_index(source)
                except Exception:
                    print ('Exception: Specified device index {} could not be set.'.format(source))
                    raise

            pyaudio_kwargs = {
                'format': pyaudio.paInt16,
                'input': True
            }
            # Grab relevant default settings to use as pyaudio args.
            pyaudio_kwargs.update({'input_device_index': device['index'], 'channels': device['maxInputChannels'], 'rate': int(device['defaultSampleRate'])})
        else:
            try:
                self.waveform = wave.open(source)
            except Exception:
                print ('Exception: Specified wav file {} could not be opened.'.format(source))
                raise

            pyaudio_kwargs = { # Extract relevant configuration from .wav file to use in Pyaudio.
                'format': self.audio.get_format_from_width(self.waveform.getsampwidth()),
                'output': True,
                'rate': self.waveform.getframerate(),
                'channels': self.waveform.getnchannels()
            }

        for key, value in kwargs.items(): # Add reconfigured settings.
            if key in pyaudio_kwargs:
                pyaudio_kwargs[key] = value
            else:
                raise KeyError('Key: {}, can not be set as it does not exist in the configuration.'.format(key))

        pyaudio_kwargs['frames_per_buffer'] = self.config.get_config('frames_per_sample')
        self.config.set_source(pyaudio_kwargs)

    def get_input_devices(self):
        """ Lists the names and IDs of the input devices on your system. """
        info = self.audio.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range(0, numdevices):
                if (self.audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                    print("Input Device index {} - {}".format(i, self.audio.get_device_info_by_host_api_device_index(0, i).get('name')))

    def set_callbacks(self, callbacks: list):
        """ Attach supplied callbacks to signals on the dispatcher.
            Dispatcher is a loose form of the observer pattern.
            When the dispatcher is sent a signal, each observee will have their callback run.
        """
        for callback in callbacks:
            dispatcher.connect(callback['function'], callback['signal'], sender=dispatcher.Any)
