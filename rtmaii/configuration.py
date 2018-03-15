"""
    Module for handling & storing configuring different analysis and audio settings.

    TODO:
        - Handle adding to existing settings i.e. bands of interest/removal?
"""
class Config(object):
    """ Configuration class to be passed around and read during program execution.

        **Attributes**:
            - **settings** (dict): contains each setting detailed below.
                    - **bands** (dict): frequency bands that the user is interested in.
                      In the form of "name": [minFrequency, maxFrequency].

                    - **merge_channels** (bool): analyze all channel signals as a single signal.

                    - **fft_resolution** (int): the size a sample needs to be before fft analysis.

                    - **pitch_algorithm** (string): the frequency algorithm to be performed.
                      Please see the pitch module for more information on the algorithms.

        TODO: Finish docstring and add other settings
    """
    def __init__(self: object, **kwargs: dict):
        """ Inititialize a configuration object to hold runtime library settings.

            **Args**:
                - kwargs: the initial settings to configure.
=
            **Note**:
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
                "bands": True
            },

            # Size of sample to take before performing pitch tasks
            # (Higher = More accurate, but more computationally expensive.)
            "frequency_resolution": 20480,

            "pitch_algorithm": "auto-correlation",
            "frames_per_sample": 1024,
        }

        self.settings = self.defaults
        self.set_config(**kwargs)

    def set_config(self: object, **kwargs: dict):
        """
            Given a set of keyword arguments, update the config settings.

            **Args**:
                - kwargs: a dictionary of settings to configure.

            **Example**
            ```python
                config.set_config({
                    'merge_channels': True,
                    'fft_resolution': 5120
                })
            ```

            **Note**:
                - See the base config class for possible config settings.
        """
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                self.settings[key] = value
            else:
                raise KeyError("{} is not a valid configuration setting".format(key))

    def get_config(self: object, setting: str):
        """
            Retreive a setting from the config object.

            **Args**:
                - setting: the key of the setting.
        """
        return self.settings[setting]

    def set_source(self: object, source_config: dict):
        """
            Change the processing related settings based on the audio source set.

            I.e. different audio sources have different sampling_rates and channel counts.
            *RTMAII's* processing needs to know this before analysis.

            **Args**:
                - source_config: the source configuration settings.
        """
        self.settings['pyaudio_settings'] = source_config
        self.settings['sampling_rate'] = source_config['rate']
        self.settings['channels'] = source_config['channels']
