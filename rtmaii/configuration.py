""" CONFIGURATION MODULE

    Module for handling & storing configuring different analysis and audio settings.
"""
class Config(object):
    """ Configuration class to be passed around and read during program execution.

        Attributes:
            - settings (dict): contains each setting detailed below.
                    - bands (dict): frequency bands that the user is interested in.
                      In the form of "name": [minFrequency, maxFrequency].

                    - merge_channels (bool): analyze all channel signals as a single signal.

                    - fft_resolution (int): the size a sample needs to be before fft analysis.

                    - pitch_algorithm (string): the frequency algorithm to be performed.
                      Please see the pitch module for more information on the algorithms.

        TODO: Finish docstring and add other settings
    """
    def __init__(self: object, **kwargs: dict):
        """ Inititialize a configuration object to hold runtime library settings.

            Args:
                - kwargs: the initial settings to configure.

            Note:
                - Please see the base Config class docstring for more information on settings.
        """
        self.defaults = {
            "merge_channels": True,
            "bands": {
                "sub-bass":[20, 60],
                "bass":[60, 250],
                "low-mid":[250, 500],
                "mid":[500, 2000],
                "upper-mid":[2000, 4000],
                "presence":[4000, 6000],
                "brilliance":[6000, 20000]
            },
            "tasks": {
                "pitch": True,
                "genre": True,
                "beat": True,
                "export_spectrograms" : True,
                "bands": True
            },
            # Size of sample to take before performing pitch tasks
            # (Higher = More accurate, but more computationally expensive.)
            "block_size": 16384, # Power of 2 for efficiency.
            "pitch_algorithm": "ac",
            #beat algorithm is either ed=energydetect or dc=descendingthreshold
            "beat_algorithm": "ed",
            "beat_desc_rate": 20,
            "beat_low_cut": 60,
            "beat_low_pass": 1000,
            "frames_per_sample": 1024,
        }

        self.settings = self.defaults
        self.set_config(**kwargs)

    def set_config(self: object, **kwargs: dict):
        """
            Given a set of keyword arguments, update the config settings.

            Args:
                - kwargs: a dictionary of settings to configure.

            Example
            ```python
                config.set_config({
                    'merge_channels': True,
                    'fft_resolution': 5120
                })
            ```

            Note:
                - See the base config class for possible config settings.
        """
        for key, setting in kwargs.items():
            if key in self.settings:
                if key == 'tasks':
                    self.__validate_tasks__(setting)
                    self.settings[key].update(setting)
                else:
                    if key == 'bands':
                        self.__validate_bands__(setting)
                    elif key == 'block_size':
                        if setting < 4096:
                            raise ValueError("Block size must be above 4096 frames.")
                        if setting < self.settings['frames_per_sample']:
                            raise ValueError("Block size can't be lower than frames per sample.")
                    else:
                        self.__validate_type__(key, setting)
                        if key == 'pitch_algorithm':
                            self.__validate_pitch__(setting)
                        if key == 'beat_desc_rate':
                            self.__validate_beat__(setting)
                    self.settings[key] = setting
            else:
                raise KeyError("{} is not a valid configuration setting".format(key))

    def get_config(self: object, key: str) -> object:
        """ Retreive a setting from the config object.

            If setting doesn't exist returns None object.

            Args:
                - setting: the key of the setting.
        """
        if key in self.settings:
            return self.settings[key]
        return None

    def set_source(self: object, source_config: dict, **kwargs):
        """
            Change the processing related settings based on the audio source set.

            I.e. different audio sources have different sampling_rates and channel counts.
            RTMAII's processing needs to know this before analysis.

            Args:
                - source_config: the source configuration settings.
        """
        for key, value in kwargs.items(): # Add reconfigured settings.
            if key in source_config:
                source_config[key] = value
            else:
                raise KeyError('Key: {}, can not be set as it does not exist in the configuration.'
                               .format(key))

        source_config['frames_per_buffer'] = self.get_config('frames_per_sample')
        self.settings['pyaudio_settings'] = source_config
        self.settings['sampling_rate'] = source_config['rate']
        self.settings['channels'] = source_config['channels']

    def __validate_tasks__(self, tasks):
        """ Perform validation on supplied tasks settings.

            Args:
                - tasks: tasks being set.
        """
        for task, val in tasks.items():
            if not task in self.settings['tasks']:
                raise KeyError("{} is not a valid task key".format(task))
            value_type = type(val)
            if not value_type == bool:
                raise TypeError("Task {} given a value {} with type {}, this should be a bool."
                                .format(task, val, value_type))

    @staticmethod
    def __validate_bands__(bands):
        """ Perform validation on supplied bands settings.

            Args:
                - bands: bands config that was passed in.
        """
        for band, rng in bands.items():
            value_type = type(rng)
            if not isinstance(rng, (list, tuple)):
                raise TypeError("Band {} given a value {} with type {}, should be a tuple or list."
                                .format(band, rng, value_type))
            if not len(rng) == 2:
                raise ValueError("Band {} with value {} should only contain two values."
                                 .format(band, rng))
            for value in rng:
                if not isinstance(value, (int, float)):
                    raise TypeError("Band {} has a range value {} which is not numeric"
                                    .format(band, value))

    @staticmethod
    def __validate_pitch__(setting):
        """ Perform validation that pitch method exists.
            NOTE: this is hard-coded at the moment, but we could do this based on Key subclasses.

            Args:
                - setting: pitch method that was passed in.
        """
        pitch_methods = ['zc', 'fft', 'ac', 'hps']
        if not setting in pitch_methods:
            raise ValueError("The pitch method {} set doesn't exist".format(setting))

    def __validate_beat__(setting):
        if setting <= 0:
            raise ValueError("The beat threshold descenscion rate can't be lower or equal to 0")


    def __validate_type__(self, key, value):
        """ Perform type validation on supplied setting.

            Args:
                - key: key of setting.
                - value: value of setting.
        """
        expected = type(self.settings[key])
        actual = type(value)
        if not expected == actual:
            raise TypeError("Key {} should be of type {}, whilst type {} was used."
                            .format(key, expected, actual))
