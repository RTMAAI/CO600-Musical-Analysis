""" BASIC USER IMPLEMENTATION """
import time
from rtmaii import rtmaii # Replace with just import rtmaii in actual implementation.

def main():
    def frequency_callback(data):
        print("Frequency event happened")

    def spectrogram_callback(data):
        print("Spectrogram event happened")

    # Default is sample_config
    #config_path = r'.\config\sample_config.json'

    analyser = rtmaii.Rtmaii([{'function': frequency_callback, 'signal':'frequency'},
                              {'function': spectrogram_callback, 'signal':'spectrogram'}])

    analyser.start()

    # while analyser.is_active():
    #     # Runs forever whilst analyser is active, when a track is used will run until it's finished.
    #     # Keeps script running, similar to Pyaudio's is_active()
    #     pass

    end_time = time.time() + 10 # run for 10 seconds
    while time.time() < end_time:
        pass

if __name__ == '__main__':
    main()
