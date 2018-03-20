""" RTMA PROFILER/BENCHMARK

    This module is a commandline script, which can run the library tasks in a sandboxed setting.
"""
import argparse
import time
import statistics
import json
from rtmaii import hierarchy, configuration
from numpy import arange, int16, frombuffer
from pydispatch import dispatcher

class Tracker(object):
    """ Tracks signal responses from library, storing response times over numerous runs.

        Attributes:
            - reset [dict]: dictionary containing initial state of tracker, each key value is set to None.
            - tracker [dict]: copy of reset, When threads respond with results, these are set to the time taken for the response.
            - time_taken [dict]: Stores repsonse times over numerous runs for statisitical analysis.
    """
    def __init__(self):
        dispatcher.connect(self.set_switch, sender=0)
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
        """ Store response times from current run. """
        for signal, end_time in self.tracker.items():
            self.time_taken[signal].append(end_time-start_time)

    def reset_tracker(self):
        """ Reset tracker to default unfilled state """
        self.tracker = self.reset.copy()

    def set_switch(self, data, **kwargs):
        """ Set switch on tracker to signify that signal has been recieved. """
        self.tracker[kwargs['signal']] = time.time()

    def print_times(self):
        """ Loop through tracker times printing average response time of threads. """
        for signal, times in self.time_taken.items():
            print('{} Average Retrieval Benchmark '.format(signal))
            print('\tMEDIAN ', statistics.median(times))
            print('\tMEAN ', statistics.mean(times))
            print('\tSTDEV ', statistics.stdev(times))

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
PARSER.add_argument("-r", "--frequencyresolution",
                    help="Resolution of signal before performing frequency analysis. Default is 20480.",
                    type=int, default=20480)
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
PARSER.add_argument("-m", "--mergechannels",
                    help="Whether channel data should be analysed as one channel.",
                    type=bool, default=True)
ARGS = PARSER.parse_args()

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

    stub_wave = arange(ARGS.framespersample * ARGS.channelcount, dtype=int16).tobytes()
    stub_count = ARGS.frequencyresolution// ARGS.framespersample

    tracker = Tracker()
    config = configuration.Config(
        **{'bands': ARGS.bands,
           'frames_per_sample': ARGS.framespersample,
           'pitch_algorithm': ARGS.pitchmethod,
           'merge_channels': ARGS.mergechannels,
           'tasks': ARGS.tasks
          }
        )
    config.set_source(
        {'channels': ARGS.channelcount,
         'rate': ARGS.samplingrate
        })
    root = hierarchy.Hierarchy(config, [])

    # Prepare workers, hitting thresholds for frequency coordinator and spectrogram.
    for _ in range(stub_count):
        # As some tasks have a threshold before running, we need to feed them a couple of stubs.
        root.put(frombuffer(stub_wave, dtype=int16))
    tracker.wait_for_signals()

    # Run the analysis N times.
    for _ in range(ARGS.noruns):
        tracker.reset_tracker()
        start_time = time.time()
        # The root conversion time is taken into account.
        root.put(frombuffer(stub_wave, dtype=int16))
        tracker.wait_for_signals()
        tracker.store_times(start_time)
    tracker.print_times()

if __name__ == '__main__':
    main()