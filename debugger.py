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

#matplotlib.pyplot.ion() # Enables interactive plotting.
CHUNK_LENGTH = 1024 # Length of sampled data
SPECTRUM_LENGTH = int(CHUNK_LENGTH*10) # Default config is set to wait until 10*1024 before analysing the spectrum.
SAMPLING_RATE = 44100 # Default sampling rate 44.1 khz
FRAME_DELAY = 1000 # How long between each frame update (ms)
XPADDING = 20
BACKGROUND_COLOR = '#3366cc'
ACCENT_COLOR = '#6633cc'
TEXT_COLOR = '#fff'
TRIM_COLOR = '#33cc99'
HEADER_SIZE = 20
VALUE_SIZE = 15

class Listener(threading.Thread):
    """ Starts analysis and holds a state of analysed results.
        TODO: Store state over time to allow for rewinding through results.
    """
    def __init__(self):

        self.state = {
            'pitch': 0,
            'key': "A",
            'bands': { #TODO: Should build labels initially based on config bands.
                'sub-bass': 0,
                'bass': 0,
                'low-mid': 0,
                'mid': 0,
                'upper-mid': 0,
                'presence': 0,
                'brilliance': 0
            },
            'spectrum': zeros(SPECTRUM_LENGTH),
            'signal': zeros(CHUNK_LENGTH),
            'spectogram':zeros([128,128,128])

        }

        callbacks = []
        for key, _ in self.state.items():
            callbacks.append({'function': self.callback, 'signal': key})

        self.analyser = rtmaii.Rtmaii(callbacks,
                                      mode='INFO',
                                      track=r'.\test_data\spectogramTest.wav',
                                     )

        threading.Thread.__init__(self, args=(), kwargs=None)

        self.start()

    def start_analysis(self):
        """ Start analysis. """
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
        self.config(bg=BACKGROUND_COLOR)
        self.listener = Listener()
        self.setup()
        self.update()

    def setup(self):
        """Create UI elements and assign configurable elements. """
        # --- INIT SETUP --- #
        self.timeframe = arange(0, CHUNK_LENGTH) # split x axis up to 1
        self.title("RTMAII DEBUGGER")
        #self.pack_propagate(0) # Disables auto-resizing of elements.

        # --- CONTROL FRAME --- #
        control_frame = tk.Frame(self, borderwidth=1, bg=BACKGROUND_COLOR, highlightbackground=TRIM_COLOR, highlightthickness=4)
        control_frame.pack(side=tk.TOP, pady=10)

        # --- CONTROLS --- #
        self.play = tk.Button(control_frame, text="PLAY", command=self.listener.start_analysis, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE))
        self.play.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)

        self.stop = tk.Button(control_frame, text="STOP", command=self.listener.stop_analysis, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE))
        self.stop.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)

        # --- LEFT FRAME---- #
        left_frame = tk.Frame(self, borderwidth=1, width=500, height=500, bg=BACKGROUND_COLOR, highlightbackground='#33cc99', highlightthickness=2)
        left_frame.pack(side=tk.LEFT)

        # --- SIGNAL GRAPH --- #
        signal_frame = Figure(figsize=(10, 4), dpi=100)
        self.signal_plot = signal_frame.add_subplot(111)
        self.signal_plot.plot(self.timeframe, self.timeframe)
        self.signal_plot.set_ylim([100, 20000])
        self.signal_canvas = FigureCanvasTkAgg(signal_frame, left_frame)
        self.signal_canvas.show()
        self.signal_canvas.get_tk_widget().pack(padx=XPADDING)

        # --- SPECTRUM GRAPH --- #
        self.frequencies = arange(SPECTRUM_LENGTH)/(CHUNK_LENGTH/SAMPLING_RATE)/2 # Possible range of frequencies
        spectrum_frame = Figure(figsize=(10, 4), dpi=100)
        self.spectrum_plot = spectrum_frame.add_subplot(111)
        self.spectrum_plot.plot(self.frequencies, self.frequencies)
        self.spectrum_plot.set_xlim([0, 20000]) # TODO Fix this
        self.spectrum_canvas = FigureCanvasTkAgg(spectrum_frame, left_frame)
        self.spectrum_canvas.show()
        self.spectrum_canvas.get_tk_widget().pack(padx=XPADDING)

        # --- RIGHT FRAME --- #
        right_frame = tk.Frame(self, borderwidth=1, width=500, height=500, bg=BACKGROUND_COLOR)
        right_frame.pack(side=tk.RIGHT)

        # --- SPECTROGRAM GRAPH --- #
        spectrogram_frame = Figure(figsize=(10, 4), dpi=100)
        self.spectrogram_plot = spectrogram_frame.add_subplot(111)
        self.spectrogram_plot.plot(self.frequencies, self.frequencies)
        self.spectrogram_canvas = FigureCanvasTkAgg(spectrogram_frame, right_frame)
        self.spectrogram_canvas.show()
        self.spectrogram_canvas.get_tk_widget().pack(padx=XPADDING, side=tk.BOTTOM)

        # --- VALUE FRAME --- #
        value_frame = tk.LabelFrame(right_frame, borderwidth=1, width=500, height=500, text="Analysed Values", bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE), highlightbackground=TRIM_COLOR, highlightthickness=4)
        value_frame.pack(side=tk.TOP, pady=20)

        # --- PITCH LABEL --- #
        self.pitch = tk.StringVar()
        pitch_frame = tk.Frame(value_frame, borderwidth=1, bg=ACCENT_COLOR)
        pitch_frame.pack(padx=10)
        pitch_label = tk.Label(pitch_frame, text=str('Pitch:'), bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, VALUE_SIZE))
        pitch_label.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
        pitch_value = tk.Label(pitch_frame, textvariable=self.pitch, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, VALUE_SIZE))
        pitch_value.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)

        # --- KEY LABEL --- #
        self.key = tk.StringVar()
        key_frame = tk.Frame(value_frame, borderwidth=1, bg=ACCENT_COLOR)
        key_frame.pack(padx=10)
        key_label = tk.Label(key_frame, text=str('Key:'), bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, VALUE_SIZE))
        key_label.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
        key_value = tk.Label(key_frame, textvariable=self.key, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, VALUE_SIZE))
        key_value.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)

        # --- BANDS LABEL --- #
        self.bands = {}
        chosen_bands = self.listener.get_item('bands')
        bands_frame = tk.LabelFrame(value_frame, borderwidth=1, text="Analysed Bands", bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE), highlightbackground=TRIM_COLOR, highlightthickness=4)
        bands_frame.pack(padx=10)

        for key, _ in chosen_bands.items():
            self.bands[key] = tk.IntVar()
            band_frame = tk.Frame(bands_frame, borderwidth=1, bg=ACCENT_COLOR)
            band_frame.pack()
            key_label = tk.Label(band_frame, text='{}: '.format(key), foreground=TEXT_COLOR, bg=ACCENT_COLOR, font=(None, VALUE_SIZE))
            key_label.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
            value_label = tk.Label(band_frame, textvariable=self.bands[key], foreground=TEXT_COLOR, bg=ACCENT_COLOR, font=(None, VALUE_SIZE))
            value_label.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)

    def update(self):
        """ Update UI every FRAME_DELAY milliseconds """
        # --- UPDATE GRAPHS --- #
        self.signal_plot.clear()
        self.signal_plot.set_title('Signal')
        self.signal_plot.set_xlabel('Time (Arbitary)')
        self.signal_plot.set_ylabel('Amplitude')
        signal = self.listener.get_item('signal') #TODO: Shouldn't need to splice timeframe to len of sig.
        self.signal_plot.plot(self.timeframe[:len(signal)], signal)

        self.spectrum_plot.clear()
        self.spectrum_plot.set_title('Spectrum')
        self.spectrum_plot.set_xlabel('Frequency (Hz)')
        self.spectrum_plot.set_ylabel('Power')
        self.spectrum_plot.plot(self.frequencies, self.listener.get_item('spectrum'))

        self.spectrogram_plot.clear()
        self.spectrogram_plot.set_title('Spectrogram')
        self.spectrogram_plot.set_xlabel('Time')
        self.spectrogram_plot.set_ylabel('Frequency (Hz)')
        data = self.listener.get_item('spectogram')
        
        print(len(data[0]), 'time')
        print(len(data[1]), 'freq')
        print(len(data[2]), 'intensity')

        self.spectrogram_plot.pcolormesh(data[0],data[1],data[2], vmin=-120, vmax=0)

        self.signal_canvas.draw()
        self.spectrum_canvas.draw()
        self.spectrogram_canvas.draw()

        # --- UPDATE LABELS --- #
        self.pitch.set(self.listener.get_item('pitch'))
        self.key.set(self.listener.get_item('key'))
        bands = self.listener.get_item('bands')
        # Update each band value.
        for key, value in bands.items():
            self.bands[key].set(value)

        # --- UPDATE PLAY --- #
        if self.listener.is_active():
            self.play.config(state='disabled')
            self.stop.config(state='normal')
        else:
            self.play.config(state='normal')
            self.stop.config(state='disabled')

        self.after(FRAME_DELAY, self.update)

def main():
    debugger = Debugger()
    debugger.mainloop()

if __name__ == '__main__':
    main()
