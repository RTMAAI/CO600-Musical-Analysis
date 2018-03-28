""" BASIC USER IMPLEMENTATION """
from rtmaii import rtmaii # Replace with just import rtmaii in actual implementation.

def main():
    """ This script gives a brief overview of some of the methods
        available and how to use our library.
    """
    def pitch_callback(**kwargs):
        """ Basic signal callback, retrieving pitch data from analysis.
            Kwargs will be passed information about the signal.
            kwargs['signal'] = name of signal that called this function.
        """
        print(kwargs)
        print("Pitch event happened")

    def note_callback(data):
        """ Prints the retrieved note each time a note event is sent.

            The callback arg must be named 'data' or you can grab the data from the kwargs.
        """
        print("Note: {}".format(data))

    config = {
        'tasks': {
            'bands': False,
            'genre': False,
            'export_spectrograms': False
        },
        'bands': {
            'low_band': [0, 2000],
            'mid_band': [2000, 4000]
        }
    }

    analyser = rtmaii.Rtmaii([{'function': pitch_callback, 'signal':'pitch'}],
                             source=r'./test_data/sine_493.88.wav',
                             config=config,
                             **{'mode': 'ERROR'})

    analyser.set_callbacks([{'function': note_callback, 'signal':'note'}])
    analyser.start() # Runs the analysis.

    while analyser.is_active():
        # Runs forever whilst analyser is active, when a track is used will run until it's finished.
        # Keeps script running, similar to Pyaudio's is_active()
        pass

    # Once analysis has stopped you can set up a new track to run.
    # Calling just set_source() with no args, with use your default input device.
    analyser.set_source('./test_data/sine_493.88.wav')

    # Any analysis parameters can be changed between audio sources.
    analyser.set_config(**{'tasks': {'beat': False}})

    analyser.start()

    while analyser.is_active():
        pass

if __name__ == '__main__':
    main()
