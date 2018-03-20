""" BASIC USER IMPLEMENTATION """
import time
from rtmaii import rtmaii # Replace with just import rtmaii in actual implementation.
from rtmaii.worker import Worker

class NewWorker(Worker):
    def __init__(self, channel_id: int):
        Worker.__init__(self, channel_id)

    def run(self):
        data = self.queue.get()
        print("I'm a new worker running on the library.")


def main():
    def frequency_callback(data):
        print("Frequency event happened")

    def spectrogram_callback(data):
        print("Spectrogram event happened")

    analyser = rtmaii.Rtmaii([{'function': frequency_callback, 'signal':'frequency'},
                              {'function': spectrogram_callback, 'signal':'spectrogram'}],
                              track=r'C:\Users\RalphRaulePC\Music\OwnDataset\Music\rock_part1.wav',
                              mode='DEBUG')

    analyser.add_node('NewWorker')

    analyser.start()

    # while analyser.is_active():
    #     # Runs forever whilst analyser is active, when a track is used will run until it's finished.
    #     # Keeps script running, similar to Pyaudio's is_active()
    #     pass

    end_time = time.time() + 30 # run for 10 seconds
    while time.time() < end_time:
        pass

if __name__ == '__main__':
    main()
