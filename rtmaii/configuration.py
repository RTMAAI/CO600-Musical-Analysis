"""
    Module for handling & storing configuring different analysis and audio settings.

    TODO:
        - Handle adding to existing settings i.e. bands of interest/removal?
"""
class Config(object):
    """
        
    """
    def __init__(self, **kwargs):

        self.defaults = {
            "merge_channels": False,
            "bands": {
                "bass": [60, 250],
                "low-mid": [250, 500],
                "mid": [500, 2000]
            },
            "fft_resolution": 20480
        }

        self.settings = self.defaults
        self.set_config(**kwargs)

    def set_config(self, **kwargs):
        """
            Given a set of keyword arguments, update the config settings.

            **Example**
            ```python
                config.set_config({
                    'merge_channels': True,
                    'fft_resolution': 5120
                })
            ```
        """
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                self.settings[key] = value
            else:
                raise KeyError("{} is not a valid configuration setting".format(key))

    def get_config(self, setting):
        """
            Retreive a setting from the config object.
        """
        return self.settings[setting]

    def set_source(self, args):
        """
            Change the audio source settings.
        """
        self.settings['pyaudio_settings'] = args
        self.settings['sampling_rate'] = args['rate']
        self.settings['channels'] = args['channels']
