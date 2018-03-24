""" BASIC USER IMPLEMENTATION """
from rtmaii import rtmaii # Replace with just import rtmaii in actual implementation.


def main():
    """ """
    def pitch_callback(_, **kwargs):
        """ Basic signal callback, retrieving pitch data from analysis.
            Kwargs will be passed information about the signal.
            kwargs['signal'] = name of signal that called this function.
        """
        print(kwargs)
        print("Frequency event happened")

    def spectrogram_callback(_):
        """ """
        print("Spectrogram event happened")

    analyser = rtmaii.Rtmaii([{'function': pitch_callback, 'signal':'pitch'},
                              {'function': spectrogram_callback, 'signal':'spectrogram'}],
                             track=r'C:\Users\RalphRaulePC\Music\OwnDataset\Music\rock_part1.wav',
                             mode='DEBUG')
    analyser.start()

    while analyser.is_active():
        # Runs forever whilst analyser is active, when a track is used will run until it's finished.
        # Keeps script running, similar to Pyaudio's is_active()
        pass

if __name__ == '__main__':
    main()
