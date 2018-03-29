""" RTMA PROFILER/BENCHMARK

    This module is a commandline script, which can run the library tasks in a sandboxed setting.
"""
import argparse
import time
import statistics
import json
from rtmaii import hierarchy, configuration
from numpy import arange, int16, frombuffer, sin, pi
from pydispatch import dispatcher

class Tracker(object):
    """ Tracks signal responses from library, storing response times over numerous runs.

        Args:
            - signals: Signals to be tracked.

        Attributes:
            reset (dict): contains initial state of tracker, each key value is set to None.
            tracker (dict): When threads respond with results, values set to time taken to respond.
            time_taken (dict): Stores response times over numerous runs for statisitical analysis.
    """
    def __init__(self, signals: list):
        dispatcher.connect(self.set_switch, sender=0) # Catch any signal from channel 0.
        # Could be extended to monitor delay of each channel when multi-channel analysis is enabled.
        self.reset = {key: None for key in signals}
        self.tracker = self.reset.copy()
        self.time_taken = {key: [] for key in signals}

    def store_times(self, start_time):
        """ Store response times from current run. """
        for signal, end_time in self.tracker.items():
            self.time_taken[signal].append(end_time-start_time)

    def reset_tracker(self):
        """ Reset tracker to default unfilled state """
        self.tracker = self.reset.copy()

    def set_switch(self, **kwargs):
        """ Set switch on tracker to signify that signal has been recieved. """
        if kwargs['signal'] in self.tracker:
            self.tracker[kwargs['signal']] = time.time()

    def print_times(self):
        """ Loop through tracker times printing average response time of threads. """
        for signal, times in self.time_taken.items():
            print('{} average retrieval benchmark: '.format(signal))
            print('\tMEDIAN ', statistics.median(times))
            print('\tMEAN ', statistics.mean(times))
            print('\tSTDEV ', statistics.stdev(times))

    def add_signal(self, signal):
        """ Adds signal for tracker to monitor. """
        self.reset[signal] = None
        self.time_taken[signal] = []

    def wait_for_signals(self):
        """ Wait for all values in the tracker to be filled with a return time. """
        while None in self.tracker.values():
            pass

##--- DEFAULT SETTINGS ---##
BANDS = {
    "sub-bass":[20, 60],
    "bass":[60, 250],
    "low-mid":[250, 500],
    "mid":[500, 2000],
    "upper-mid":[2000, 4000],
    "presence":[4000, 6000],
    "brilliance":[6000, 20000]
}
TASKS = {
    "pitch": True,
    "genre": True,
    "beat": True,
    "export_spectrograms" : True,
    "bands": True
}
PARSER = argparse.ArgumentParser(
    description="Benchmark each task based on configuration options used in a sandbox simulation."
    )

##--- PARSER ARGUMENTS ---##
PARSER.add_argument("-b", "--bands",
                    help="Frequency bands to analyse as a dictionary.",
                    type=json.loads, default=BANDS)
PARSER.add_argument("-s", "--samplingrate",
                    help="Sampling rate in Hertz, i.e. 44100",
                    type=int, default=44100)
PARSER.add_argument("-f", "--framespersample",
                    help="Frames per buffer sample, default is 1024",
                    type=int, default=1024)
PARSER.add_argument("-r", "--blocksize",
                    help="Size of signal before performing frequency based analysis.",
                    type=int, default=16384)
PARSER.add_argument("-t", "--tasks", help="Analysis Tasks to run.",
                    type=json.loads, default=TASKS)
PARSER.add_argument("-p", "--pitchmethod",
                    help="Pitch method to use for analysis.",
                    type=str, default='hps')
PARSER.add_argument("-n", "--noruns",
                    help="Number of runs to perform.",
                    type=int, default=10)
PARSER.add_argument("-c", "--channelcount",
                    help="Number of channels to mimic being analysed.",
                    type=int, default=1)
PARSER.add_argument('-mc', "--mergechannels", dest='mergechannels',
                    help="Merge channel data into one thread.",
                    type=bool, default=True)
PARSER.add_argument("-m", "--multichannelanalysis", dest='mergechannels',
                    help="Toggle multi channel analysis", action='store_false')
ARGS = PARSER.parse_args()

def generate_sine(sampling_rate, time_step):
    """ Generates a basic sine wave to send as a stub to hierarchy. """
    return sin(2 * pi * 440 * time_step / sampling_rate)

def main():
    """ BENCHMARKING PROCESS

        1. Creates dummy signal to send through hierarchy.
        2. Creates independent Hierarchy and Config, so audio is not needed. (Using passed args)
        3. Put dummy signal into Hierarchy X times to hit analysis threshold of some threads.
        4. Put dummy signal into Hierarchy N times (Specified by args)
        5. Print out average response times for threads.
    """
    print('Config options used in this benchmark are:')
    for key, value in ARGS.__dict__.items():
        print('\t{}: {}'.format(key, value))
    print('On average {} buffer samples will be retrieved from the audio source a second.'
          .format(ARGS.samplingrate // ARGS.framespersample))
    print('[Warning] This is only an approximation, Python can take a while to warm up.')

    time_step = arange(ARGS.framespersample * ARGS.channelcount, dtype=int16)
    stub_wave = (generate_sine(ARGS.samplingrate, time_step) * 1000).tobytes()
    stub_count = 127 # Amount needed to start genre predictions.
    ARGS.tasks['genre'] = False # Currently disabled, needs rework in order for benchmark to work

    config = configuration.Config(
        **{'bands': ARGS.bands,
           'frames_per_sample': ARGS.framespersample,
           'pitch_algorithm': ARGS.pitchmethod,
           'merge_channels': ARGS.mergechannels,
           'tasks': ARGS.tasks,
           'block_size': ARGS.blocksize
          }
        )
    config.set_source(
        {'channels': ARGS.channelcount,
         'rate': ARGS.samplingrate
        })
    root = hierarchy.Hierarchy(config, [])

    signals = []
    signals.append('signal')
    tasks = config.get_config('tasks')
    if tasks['pitch']:
        signals.append('pitch')
        signals.append('note')
    if tasks['bands']:
        signals.append('spectrum') # Used by both tasks.
        signals.append('bands')
    if tasks['beat']:
        # signals.append('bpm') Had to disable because of last minute changes from members.
        signals.append('beats')
    tracker = Tracker(signals)

    # Prepare workers, hitting thresholds for frequency coordinator and spectrogram.
    print("Preparing workers...")
    for _ in range(stub_count):
        # As some tasks have a threshold before running, we need to feed them a couple of stubs.
        root.put(frombuffer(stub_wave))
    tracker.wait_for_signals()

    if tasks['genre']: # Genre only runs once every 128 frames.
        print('[Warning] Genre is not currently supported for benchmarks.')
        # This would increase the timings of benchmarks substantially, so have currently disabled.
        #tracker.add_signal('genre')

    print("Running tests...")
    # Run the analysis N times.
    for _ in range(ARGS.noruns):
        tracker.reset_tracker()
        start_time = time.time()
        # The root conversion time is taken into account.
        root.put(frombuffer(stub_wave))
        tracker.wait_for_signals()
        tracker.store_times(start_time)
    tracker.print_times()

if __name__ == '__main__':
    main()
