""" NAIVE DEBUGGER IMPLEMENTATION

    TODO: library controls
    TODO: rewinding of analysis
    TODO: resetting analysis
    TODO: bpm debugging
    TODO: spectrogram debugging
    TODO: genre labels

"""
import threading
from rtmaii import rtmaii # Replace with just import rtmaii in actual implementation.
from numpy import arange, zeros

import matplotlib
matplotlib.use("TkAgg") # Fastest plotter backend.
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

matplotlib.pyplot.ion() # Enables interactive plotting.

CHUNK_LENGTH = 1024 # Length of sampled data
SPECTRUM_LENGTH = int(CHUNK_LENGTH/2) # Only need half of a spectrum to get all frequencies present.
SAMPLING_RATE = 44100 # Default sampling rate 44.1 khz
FRAME_DELAY = 200 # How long between each frame update (ms)

class Listener(threading.Thread):
    """ Starts analysis and holds a state of analysed results.
        TODO: Store state over time to allow for rewinding through results.
    """
    def __init__(self):

        self.state = {
            'pitch': 0,
            'key': "A",
            'bands': {},
            'spectrum': zeros(SPECTRUM_LENGTH),
            'signal': zeros(CHUNK_LENGTH),
        }

        callbacks = []
        for key, _ in self.state.items():
            callbacks.append({'function': self.callback, 'signal': key})

        self.analyser = rtmaii.Rtmaii(callbacks,
                                      track=r'.\test_data\sine_493.88.wav',
                                      mode='CRITICAL',
                                     )

        threading.Thread.__init__(self, args=(), kwargs=None)

        self.start()

    def start_analysis(self):
        """ Start analysis """
        self.analyser.start()

    def stop_analysis(self):
        """ Stop analysis and clear existing state. """
        self.analyser.stop()

    def is_active(self):
        """ Check that analyser is still running. """
        return self.analyser.is_active()

    def run(self):
        """ Keep thread alive. """
        while True:
            pass

    def callback(self, data, **kwargs):
        """ Set data for signal event. """
        signal = kwargs['signal']
        self.state[signal] = data

    def get_item(self, item):
        """ Get the latest value. """
        return self.state[item]


class Debugger(tk.Tk):
    """ Setup debugger UI to display analysis results from rtmaii.

    """
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.listener = Listener()
        self.setup()
        self.update()

    def setup(self):
        """Create UI elements and assign configurable elements. """
        # --- INIT SETUP --- #
        self.timeframe = arange(0, CHUNK_LENGTH) # split x axis up to 1

        # --- CONTROLS --- #
        play = tk.Button(self, text="PLAY", command=self.listener.start_analysis)
        play.pack(padx=10, side=tk.LEFT)

        stop = tk.Button(self, text="STOP", command=self.listener.stop_analysis)
        stop.pack(padx=10, side=tk.RIGHT)

        # --- BASE LABEL --- #
        channel_label = tk.Label(self, text=str('channel 1'))
        channel_label.pack()

        # --- SIGNAL GRAPH --- #
        signal_frame = Figure(figsize=(5, 5), dpi=30)
        self.signal_plot = signal_frame.add_subplot(111)
        self.signal_plot.plot(self.timeframe, self.timeframe)
        self.signal_plot.set_ylim([100, 20000])
        self.signal_canvas = FigureCanvasTkAgg(signal_frame, self)
        self.signal_canvas.show()
        self.signal_canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # --- SPECTRUM GRAPH --- #
        self.frequencies = arange(SPECTRUM_LENGTH)/(CHUNK_LENGTH/SAMPLING_RATE) # Possible range of frequencies
        spectrum_frame = Figure(figsize=(15, 5), dpi=100)
        self.spectrum_plot = spectrum_frame.add_subplot(111)
        self.spectrum_plot.plot(self.frequencies, self.frequencies)
        self.spectrum_plot.set_xlim([0, 20000]) # TODO Fix this
        self.spectrum_canvas = FigureCanvasTkAgg(spectrum_frame, self)
        self.spectrum_canvas.show()
        self.spectrum_canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # --- PITCH LABEL --- #
        self.pitch = tk.StringVar()
        pitch_label = tk.Label(self, text=str('Pitch'))
        pitch_label.pack(padx=5, side=tk.LEFT)
        pitch_value = tk.Label(self, textvariable=self.pitch)
        pitch_value.pack(padx=5, side=tk.LEFT)

        # --- KEY LABEL --- #
        self.key = tk.StringVar()
        key_label = tk.Label(self, text=str('Key'))
        key_label.pack()
        key_value = tk.Label(self, textvariable=self.key)
        key_value.pack()

        # --- BANDS LABEL --- #
        self.bands = tk.StringVar()
        bands_label = tk.Label(self, text=str('Bands'))
        bands_label.pack()
        bands_label = tk.Label(self, textvariable=self.bands)
        bands_label.pack()

    def update(self):
        """ Update UI every FRAME_DELAY milliseconds """
        # --- UPDATE GRAPHS --- #
        self.signal_plot.clear()
        self.signal_plot.plot(self.timeframe, self.listener.get_item('signal'))

        self.spectrum_plot.clear()
        self.spectrum_plot.plot(self.frequencies, self.listener.get_item('spectrum'))

        self.signal_canvas.draw()
        self.spectrum_canvas.draw()

        # --- UPDATE LABELS --- #
        self.pitch.set(self.listener.get_item('pitch'))
        self.key.set(self.listener.get_item('key'))
        self.bands.set(self.listener.get_item('bands'))

        self.after(FRAME_DELAY, self.update)

def main():
    debugger = Debugger()
    debugger.mainloop()

if __name__ == '__main__':
    main()