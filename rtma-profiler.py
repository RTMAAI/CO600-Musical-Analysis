""" RTMA PROFILER/BENCHMARK

    This module is a commandline script, which can run the library tasks in a sandboxed setting.
"""
from rtmaii import hierarchy, configuration
from numpy import arange, sin, pi, ndarray, int16, frombuffer
from pydispatch import dispatcher
import argparse
import time
import statistics

parser = argparse.ArgumentParser(description="Benchmark each task based on configuration options used in a sandbox simulation.")

## DEFAULTS ##
BANDS = {
    "sub-bass":[20, 60],
    "bass":[60, 250],
    "low-mid":[250, 500],
    "mid":[500, 2000],
    "upper-mid":[2000, 4000],
    "presence":[4000, 6000],
    "brilliance":[6000, 20000]
}

parser.add_argument("-b", "--bands", help="Frequency bands to analyse as a dictionary.", type=dict, default=BANDS)
parser.add_argument("-s", "--samplingrate", help="Sampling rate in Hertz, i.e. 44100", type=int, default=44100)
parser.add_argument("-f", "--framespersample", help="Frames per buffer sample, default is 1024", type=int, default=1024)
parser.add_argument("-r", "--frequencyresolution", help="Resolution of signal before performing frequency analysis. Default is 20480.", type=int, default=20480)
parser.add_argument("-t", "--tasks", help="Analysis Tasks to run.", type=dict, default=1024)
parser.add_argument("-p", "--pitchmethod", help="Pitch method to use for analysis.", type=str, default='hps')
parser.add_argument("-n", "--noruns", help="Number of runs to perform.", type=int, default=10)
parser.add_argument("-c", "--channelcount", help="Number of channels to be analysed.", type=int, default=10)
args = parser.parse_args()

bands_of_interest = args.bands
sampling_rate = args.samplingrate
frames_per_sample = args.framespersample
frequency_resolution = args.frequencyresolution
no_runs = args.noruns
pitch_algorithm = args.pitchmethod
stub_wave = arange(frames_per_sample, dtype=int16).tobytes()
stub_count = frequency_resolution // frames_per_sample

class Tracker(object):
    def __init__(self):
        self.reset = {
            'pitch': None,
            'note': None,
            'bands': None,
            'spectrum': None,
            'signal': None,
            'bpm': None
        }
        self.tracker = self.reset.copy()
        self.time_taken = {key: [] for key, _ in self.reset.items()}

    def store_times(self, start_time):
        for signal, end_time in self.tracker.items():
            self.time_taken[signal].append(end_time-start_time)

    def reset_tracker(self):
        self.tracker = self.reset.copy()

    def set_switch(self, data, **kwargs):
        tr.tracker[kwargs['signal']] = time.time()

    def print_times(self):
        for signal, times in self.time_taken.items():
            print('{} retrieval benchmark (Average time taken for signal to reach endpoint.)'.format(signal))
            print('\tMEDIAN ', statistics.median(times))
            print('\tMEAN ', statistics.mean(times))
            #print('\tSTDEV ', statistics.stdev(times))

    def wait_for_signals(self):
        while None in self.tracker.values():
            pass

tr = Tracker()
config = configuration.Config(**{'bands': bands_of_interest, 'frames_per_sample': frames_per_sample, 'pitch_algorithm': pitch_algorithm})
config.set_source({'channels': 1, 'rate': sampling_rate})
root = hierarchy.new_hierarchy(config)
dispatcher.connect(tr.set_switch, sender=0)
for i in range(stub_count + 1):
    # As some tasks have a threshold before running, we need to feed them a couple of stubs.
    root.queue.put(frombuffer(stub_wave, dtype=int16))
tr.wait_for_signals()
time.sleep(1)


print('Config options used in this benchmark are:')
print('\tBands: {}'.format(bands_of_interest))
print('\tSampling rate: {}'.format(sampling_rate))
print('\tFrames per buffer: {}'.format(frames_per_sample))

print('On average {} buffer samples will be retrieved from the audio source a second.'.format(sampling_rate // frames_per_sample))
def profile_hierarchy(number):
    for _ in range(number):
        tr.reset_tracker()
        start_time = time.time()
        root.queue.put(frombuffer(stub_wave, dtype=int16)) # The root conversion time is taken into account.
        tr.wait_for_signals()
        tr.store_times(start_time)
    tr.print_times()

profile_hierarchy(no_runs)