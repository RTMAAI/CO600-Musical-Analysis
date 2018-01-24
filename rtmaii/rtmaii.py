'''
    Main script that is imported with the library.
'''
import wave
import json
import logging
import os
from rtmaii.coordinator import Coordinator
from rtmaii.configuration import Config
from rtmaii.debugger import Locator, Debugger
from numpy import fromstring, int16
from pydispatch import dispatcher
import pyaudio

PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(PATH)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s')
LOGGER = logging.getLogger(__name__)

class Rtmaii(object):
    ''' Interface for real-time musical analysis library.

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
    '''
    def __init__(self, callbacks: list, track: str = None, config: dict = {}, mode: str = 'ERROR'):
        self.config = Config(**config)
        self.audio = pyaudio.PyAudio()
        self.set_source(track)
        self.set_callbacks(callbacks)
        LOGGER.setLevel(mode)

        pyaudio_settings = self.config.get_config('pyaudio_settings')
        pyaudio_settings['stream_callback'] = self.__stream_callback__

        self.stream = self.audio.open(**pyaudio_settings)
        self.coordinator = Coordinator(self.config)

        LOGGER.debug('RTMAII Initiliazed')

    def __stream_callback__(self, in_data, frame_count, time_info, status):
        '''
            Convert raw stream data into signal bin and put data on the coordinator's queue.
        '''
        data = fromstring(
            self.waveform.readframes(frame_count) if hasattr(self, 'waveform') else in_data,
            dtype=int16)

        self.coordinator.queue.put(data)
        if status == 4: # Push finish request to coordinator when stream has ended.
            self.coordinator.queue.put(None)
        return (data, pyaudio.paContinue)

    def is_active(self):
        ''' Check that coordinator thread is still running.

            **Returns**
                - bool: True is alive, False otherwise.
        '''
        return self.coordinator.is_alive()

    def start(self):
        ''' Set up debugger and '''
        self.stream.start_stream()

        debug_info = open('{}/debug/Channel Info.json'.format(DIR_PATH), 'w')

        channel_info = [{'id': '{}'.format(channel),
                         'img1':'Channel {}.png'.format(channel),
                         'img2': 'Channel {}-filtered.png'.format(channel),
                         'data':'Channel {} data.json'.format(channel)}
                        for channel in range(1, self.config.get_config('channels') + 1)]

        debug_info.write(json.dumps(channel_info))
        LOGGER.info('Stream started')

    def stop(self):
        ''' Stop the stream & close the track (if set) '''
        self.stream.stop_stream()
        self.stream.close()
        if hasattr(self, 'waveform'):
            self.waveform.close()

    def set_config(self, **kwargs):
        ''' Change configuration options, i.e. what bands should be look at. '''
        self.config.set_config(**kwargs)

    def set_source(self, source=None, sampling_rate=None, channels=None):
        ''' Change the analyzed source '''
        # Stop stream, reinitialize with new settings, fire kill command to coordinator.

        if source is None:
            pyaudio_kwargs = {
                'rate': 44100,
                'channels': 2,
                'format': pyaudio.paInt16,
                'input': True,
                'frames_per_buffer': 1024
            }
            self.config.set_source(pyaudio_kwargs)
        else:
            self.waveform = wave.open(source)
            pyaudio_kwargs = {
                'format': self.audio.get_format_from_width(self.waveform.getsampwidth()),
                'output': True,
                'rate': self.waveform.getframerate(),
                'channels': self.waveform.getnchannels()
            }
            self.config.set_source(pyaudio_kwargs)

    def set_callbacks(self, callbacks):
        '''
            Attach supplied callbacks to signals on the dispatcher.
            Dispatcher is a loose form of the observer pattern.
            When the dispatcher is sent a signal, each observee will have their callback run.
        '''
        for callback in callbacks:
            dispatcher.connect(callback['function'], callback['signal'], sender=dispatcher.Any)
