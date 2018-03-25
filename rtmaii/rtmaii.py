""" RTMA API MODULE

    - This module contains any API based methods that users interact with.

    When the library is installed, this is the module users should interact with.

    For detailed information on the methods and configuring the library,
    please see our Readme on our Github.
    https://github.com/RTMAAI/CO600-Musical-Analysis
"""
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

        Args:
            - Callbacks: List of dicts with a callback and the signal to will trigger it.
            - Source: The path of a track to be played, defaults to microphone input.
            - Config: Dict of settings to change. (See our Readme for a list of options.)
            - Custom_Nodes: List of custom nodes to add to Hierarchy. (See Readme for details.)

        Kwargs:
            - Mode: Logging mode, options = {'DEBUG','WARNING','CRITICAL','INFO','ERROR'}

        Example:
            ```python
                source = r'.\\Tracks\\LetItGo.wav'
                callbacks = [{'function': callback_function, 'signal':'frequency'}]
                config = {
                    "bands": {
                        "bass": {min: 200, max: 2000}
                    },
                    "tasks": {
                        "genre": False,
                    }
                }
                custom_nodes = {
                    'Node1': {'class_name': 'NewWorker', 'parent': 'SpectrumCoordinator',
                              'args': (), 'kwargs':{}}
                }
                analyser = rtmaii.Rtmaii(callbacks, source, config, custom_nodes)
                analyser.start()

                while analyser.is_active():
                    pass #Keep main thread running.
            ```
    """
    def __init__(self, callbacks: list = (), source: str = None,
                 config: dict = None, custom_nodes: dict = None, **kwargs):

        self.config = Config()
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.set_source(source)
        self.set_callbacks(callbacks)
        if config:
            self.config.set_config(**config)

        self.hierarchy = Hierarchy(self.config, custom_nodes)
        mode = 'ERROR' if 'mode' not in kwargs else kwargs['mode']
        SH.setLevel(mode)
        LOGGER.debug('RTMAAI Initiliazed')

    def __stream_callback__(self, in_data, frame_count, _, __):
        """ Convert raw stream data into signal bin and put data on the coordinator's queue. """
        data = self.waveform.readframes(frame_count) if hasattr(self, 'waveform') else in_data
        self.hierarchy.put(frombuffer(data, int16))
        return (data, pyaudio.paContinue)

    def is_active(self) -> bool:
        """ Check that coordinator thread is still running.

            Returns
                - bool: True is alive, False otherwise.
        """
        return bool(self.stream and self.stream.is_active())

    def start(self):
        """ Start audio stream and analysis. """
        pyaudio_settings = self.config.get_config('pyaudio_settings')
        pyaudio_settings['stream_callback'] = self.__stream_callback__

        if hasattr(self, 'waveform'):
            min_start = self.waveform.getnframes() - self.config.get_config('frames_per_sample')
            # Reset wav file to start, if next sample would retrieve less than the frame count.
            if self.waveform.tell() >= min_start:
                self.waveform.rewind() # Reset wave file to initial position.

        self.stream = self.audio.open(**pyaudio_settings)
        self.stream.start_stream()

        LOGGER.info('Stream started')

    def pause(self):
        """ Pause the stream. Analogous to stop if analysing live music. """
        if self.stream:
            self.stream.stop_stream()
        else:
            LOGGER.warning('Stream is not active, pausing has no effect.')

    def stop(self):
        """ Stop the stream & reset track's position (if set). """
        if hasattr(self, 'waveform'):
            self.waveform.setpos(0) # Reset wave file to initial position.
        if self.stream:
            self.stream.stop_stream()
        else:
            LOGGER.warning('Stream is not active, stopping has no effect.')

    def set_config(self, **kwargs: dict):
        """ Change configuration options, i.e. what bands should be look at.

            Note:
                - Please see our Readme for a detailed list of configuration options.
        """
        self.config.set_config(**kwargs)
        if hasattr(self, 'hierarchy'):
            if 'merge_channels' in kwargs:
                self.hierarchy.reset_hierarchy()
            else:
                self.hierarchy.update_nodes()

    def set_source(self, source: object = None, **kwargs: dict):
        """ Change the analyzed source. By default this sets the stream to use
            your default input device with it's default configuration.

            When specifying an input device in which you have changed the configuration
            such as a higher sampling rate/channels, please supply these in the kwargs.

            ```python
                set_source(**{'rate' : 96000, 'channels' : 3})
            ```
            If this is not set to match your system's configuration
            artefacts may arise in the analysis.

            Args:
                - source: Int (Index of input device) || String (Path of audio file)
                - kwargs: Additional configuration to be used in Pyaudio.

            Please see our readme for more information.
        """
        if not isinstance(source, (type(None), int, str)):
            raise TypeError('Provided source {}, should be a str, int or None type. '
                            .format(source))

        if isinstance(source, int) or source is None:
            if hasattr(self, 'waveform'):
                delattr(self, 'waveform')
            # Extract relevant configuration to use in waveform.
            try:
                device = (self.audio.get_device_info_by_index(source) if source
                          else self.audio.get_default_input_device_info())
            except Exception:
                print('Exception: Input device could not be found.')
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

        self.config.set_source(pyaudio_kwargs, **kwargs)
        LOGGER.debug('Audio source has been successfully configured.')

        if hasattr(self, 'hierarchy'):
            if self.config.get_config('merge_channels'):
                # Only update nodes instead of reconstructing.
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

    @staticmethod
    def set_callbacks(callbacks: list):
        """ Attach supplied callbacks to signals on the dispatcher.
            Dispatcher is a loose form of the observer pattern.
            When the dispatcher is sent a signal, each observee will have their callback run.

            Example:
            ```python
                set_callbacks([{'function': callback_method, 'signal':'frequency'}])
            ```
        """
        if isinstance(callbacks, (tuple, list)):
            for callback in callbacks:
                __validate_callback__(callback)
                dispatcher.connect(callback['function'], callback['signal'], sender=dispatcher.Any)
        else:
            raise TypeError('Provided callbacks {}, should be in the form of a list. '
                            .format(callbacks))


    @staticmethod
    def remove_callbacks(callbacks: list):
        """ Remove supplied callbacks from the dispatcher.

            Example:
            ```python
                remove_callbacks([{'function': callback_method, 'signal':'frequency'}])
            ```
        """
        if isinstance(callbacks, (tuple, list)):
            for callback in callbacks:
                __validate_callback__(callback)
                dispatcher.disconnect(callback['function'], callback['signal'],
                                      sender=dispatcher.Any)
        else:
            raise TypeError('Provided callbacks {}, should be in the form of a list/tuple. '
                            .format(callbacks))

    def add_node(self, class_name: str, node_id: str = None, parent: str = 'root',
                 init_args: list = (), **kwargs: dict):
        """ Add a new node to the hierarchy on each channel tree.

            When adding a custom node, you will need to make sure they inherit from,
            either the base Worker or Coordinator in rtmaii.worker||rtmaii.coordinator.

            Args:
                - class_name: class_name of object to add to hierarchy.
                - node_id: unique id to give node in hierarchy, if not set, class_name is used.
                - parent: Parent node's class_name to attach to.
                - init_args: Tuple of arguments needed to initialise the node.
                - **kwargs: Any extra arguments to pass to the node initialisation.
        """
        self.hierarchy.add_custom_node(class_name, node_id, parent, *init_args, **kwargs)

    def remove_node(self, node_id: str):
        """ Remove a node from the hierarchy.

            If you are analysing multiple channels independently,
            the node will be removed from every channels hierarchy.

            Args:
                - node_id: id of object to add to hierarchy.

            To remove inbuilt nodes, use the class name of the node.
            I.e. 'SpectrumCoordinator'
        """
        self.hierarchy.remove_node(node_id)

def __validate_callback__(callback: dict):
    """ Validate that a given callbacks parameters.

        Expected signature:
            {'function': callback_method, 'signal':'frequency'}

        Args:
            - callback: callback signature to validate.
    """
    if 'function' in callback and 'signal' in callback:
        if not callable(callback['function']):
            raise TypeError('Provided function {} is not callable.'
                            .format(callback['function']))
        if not isinstance(callback['signal'], str):
            raise TypeError('Provided signal {} is not of type str'
                            .format(callback['signal']))
    else:
        raise ValueError('Callback {}, missing required attribute signal or function.'
                         .format(callback))
