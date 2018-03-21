'''
    Main script that is imported with the library.
'''
import wave
import logging
from rtmaii.hierarchy import Hierarchy
from rtmaii.configuration import Config
from numpy import int16, frombuffer
from pydispatch import dispatcher
import pyaudio

FORMATTER = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
SH = logging.StreamHandler()
FH = logging.FileHandler('rtma-log.log', mode='w')
FH.setLevel(logging.DEBUG)
FH.setFormatter(FORMATTER)
SH.setFormatter(FORMATTER)
LOGGER.addHandler(FH)
LOGGER.addHandler(SH)

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
    def __init__(self, callbacks: list = None, track: str = None, config: dict = {}, custom_tasks: dict = None, mode: str = 'DEBUG'):

        self.config = Config(**config)
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.set_source(track)
        self.set_callbacks(callbacks)
        self.hierarchy = Hierarchy(self.config, custom_tasks)
        SH.setLevel(mode)
        LOGGER.debug('RTMAAI Initiliazed')

    def __stream_callback__(self, in_data, frame_count, time_info, status):
        """ Convert raw stream data into signal bin and put data on the coordinator's queue. """
        data = self.waveform.readframes(frame_count) if hasattr(self, 'waveform') else in_data
        self.hierarchy.put(frombuffer(data, int16))
        return (data, pyaudio.paContinue)

    def is_active(self):
        """ Check that coordinator thread is still running.

            **Returns**
                - bool: True is alive, False otherwise.
        """
        return self.stream and self.stream.is_active()

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
        if self.stream:
            self.stream.stop_stream()

    def stop(self):
        """ Stop the stream & reset track's position (if set). """
        if hasattr(self, 'waveform'):
            self.waveform.setpos(0) # Reset wave file to initial position.
        if self.stream:
            self.stream.stop_stream()

    def set_config(self, **kwargs: dict):
        """ Change configuration options, i.e. what bands should be look at. """
        self.config.set_config(**kwargs)
        if hasattr(self, 'hierarchy'):
            if 'merge_channels' in kwargs:
                self.hierarchy.reset_hierarchy()
            else:
                self.hierarchy.update_nodes()

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
        if isinstance(source, int) or source is None:
            if hasattr(self, 'waveform'):
                delattr(self, 'waveform')
            # Extract relevant configuration to use in waveform.
            if source is None:
                device = self.audio.get_default_input_device_info()
            else:
                try:
                    device = self.audio.get_device_info_by_index(source)
                except Exception:
                    print('Exception: Specified device index {} could not be set.'.format(source))
                    raise

            pyaudio_kwargs = {
                'format': pyaudio.paInt16,
                'input': True
            }
            # Grab relevant default settings to use as pyaudio args.
            pyaudio_kwargs.update({'input_device_index': device['index'],
                                   'channels': device['maxInputChannels'],
                                   'rate': int(device['defaultSampleRate'])
                                  })
        else:
            try:
                self.waveform = wave.open(source)
            except Exception:
                print('Exception: Specified wav file {} could not be opened.'.format(source))
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

        if hasattr(self, 'hierarchy'):
            if self.config.get_config('merge_channels'):
                self.hierarchy.update_nodes()
            else:
                self.hierarchy.reset_hierarchy()

    def get_input_devices(self):
        """ Lists the names and IDs of the input devices on your system. """
        info = self.audio.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range(0, numdevices):
            audio_device = self.audio.get_device_info_by_host_api_device_index(0, i)
            if (audio_device.get('maxInputChannels')) > 0:
                print("Input Device index {} - {}".format(i, audio_device.get('name')))

    def set_callbacks(self, callbacks: list):
        """ Attach supplied callbacks to signals on the dispatcher.
            Dispatcher is a loose form of the observer pattern.
            When the dispatcher is sent a signal, each observee will have their callback run.
        """
        for callback in callbacks:
            dispatcher.connect(callback['function'], callback['signal'], sender=dispatcher.Any)

    def remove_callbacks(self, callbacks: list):
        """ TODO: Implement this. """
        pass

    def add_node(self, node_name: str, parent: str = None, **kwargs: dict):
        """ Add a new node to the hierarchy on each channel tree.

            When adding a custom node, you will need to make sure they inherit from,
            either the base Worker or Coordinator in rtmaii.worker||rtmaii.coordinator.

            **Args**:
                - `node_name`: class_name of object to add to hierarchy.
                - `parent`: Parent node's class_name to attach to.
                - `kwargs`: The arguments needed to initialise the node.
        """
        self.hierarchy.add_node(node_name, parent, **kwargs)

    def remove_node(self, node_name: str):
        """ Remove a node from the hierarchy.

            If you are analysing multiple channels independently,
            the node will be removed from every channels hierarchy.

            **Args**:
                - `node_name`: class_name of object to add to hierarchy.
        """
        self.hierarchy.remove_node(node_name)
