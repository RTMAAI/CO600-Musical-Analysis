""" VISUALIZER IMPLEMENTATION

    TODO: bpm debugging

"""
import threading
import time
from functools import partial
from scipy.signal import resample
from scipy.fftpack import fftfreq
from rtmaii import rtmaii # Replace with just import rtmaii in actual implementation.
from numpy import arange, zeros
import matplotlib
matplotlib.use("TkAgg") # Fastest plotter backend.
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

SAMPLING_RATE = 44100 # Default sampling rate 44.1 khz
DOWNSAMPLE_RATE = 4 # Denominator to downsample length of signals by (Should be set according to system specs.)
FRAME_DELAY = 50 # How long between each frame update (ms)
XPADDING = 10
INNERPADDING = 5
BACKGROUND_COLOR = '#3366cc'
ACCENT_COLOR = '#6633cc'
TEXT_COLOR = '#fff'
TRIM_COLOR = '#33cc99'
HEADER_SIZE = 20
FONT_SIZE = 15
Y_PADDING = 0.3 # Amount to pad the maximum Y value of a graph by. (Percentage i.e. 0.1 = 10% padding.)
STATE_COUNT = 50 # Amount of states to store that can be moved through.
SPECTRO_DELAY = 2 # Seconds to wait between each spectrogram plot.

class Listener(threading.Thread):
    """ Starts analysis and holds a state of analysed results. """
    def __init__(self):

        self.state = {
            'pitch': [0],
            'key': [{'key':"N/A", 'cents_off': 0}],
            'bands': [{
                'sub-bass': 0,
                'bass': 0,
                'low-mid': 0,
                'mid': 0,
                'upper-mid': 0,
                'presence': 0,
                'brilliance': 0
            }],
            'genre': ["N/A"],
            'spectrum': [],
            'signal': [],
            'spectogramData': [[zeros(128), zeros(128), zeros([128, 128])]],
            'beats': [False],
            'bpm': [0]
        }

        self.max_index = STATE_COUNT - 1
        self.condition = threading.Condition()
        self.current_index = 0

        callbacks = []
        for key, _ in self.state.items():
            callbacks.append({'function': self.callback, 'signal': key})

        self.analyser = rtmaii.Rtmaii(callbacks,
                                      mode='INFO',
                                      track=r'./test_data/spectogramTest.wav',
                                     )

        self.state['spectrum'].append(arange(self.analyser.config.get_config('frequency_resolution') // 2))
        self.state['signal'].append(arange(self.analyser.config.get_config('frames_per_sample')))

        for key, _ in self.state.items():
            self.state[key] = self.state[key] * STATE_COUNT

        threading.Thread.__init__(self, args=(), kwargs=None)
        self.setDaemon(True)
        self.start()

    def start_analysis(self):
        """ Start analysis. """
        self.current_index = 0
        self.analyser.start()

    def pause_analysis(self):
        """ Pauses analysis. """
        self.analyser.pause()

    def stop_analysis(self):
        """ Stop analysis and clear existing state. """
        self.analyser.stop()

    def change_analysis(self, amount):
        """ Rewind through one state of the analysis. """
        new_value = self.current_index + amount
        self.current_index = 0 if new_value < 0 else self.max_index if new_value > self.max_index else new_value

    def set_source(self, track):
        """ Change the source. """
        self.analyser.set_source(track)

    def is_active(self):
        """ Check that analyser is still running. """
        return self.analyser.is_active()

    def run(self):
        """ Keep thread alive. """
        while True:
            self.condition.acquire()
            self.condition.wait() # Non-blocking sleep.
            self.condition.release()

    def callback(self, data, **kwargs):
        """ Set data for signal event. """
        signal = kwargs['signal']
        self.state[signal].insert(0, data)
        self.state[signal] = self.state[signal][:STATE_COUNT]

    def get_item(self, item):
        """ Get the latest value. """
        return self.state[item][self.current_index]


class SpectrogramCompression(threading.Thread):
    """ Compresses the data in the spectrogram, making plotting faster. """
    def __init__(self, listener):
        self.listener = listener

        threading.Thread.__init__(self, args=(), kwargs=None)
        self.compressed_data = [zeros(64), zeros(64), zeros([64, 64])]
        self.setDaemon(True)
        self.start()

    def run(self):
        while True:
            data = self.listener.get_item('spectogramData')
            compr_length = len(data[0]) // 2
            color_resample = resample(resample(data[2], compr_length), compr_length, axis=1)
            x_resample = resample(data[0], compr_length)
            y_resample = resample(data[1], compr_length)
            self.compressed_data = [x_resample, y_resample, color_resample]
            time.sleep(0.2)

    def get_spectro_data(self):
        return self.compressed_data

class SignalPlotter(threading.Thread):
    """ Retrieves signal data, downsamples and sets new Y data and limits. """
    def __init__(self, listener, plot, line):
        self.listener = listener
        self.plot = plot
        self.line = line

        threading.Thread.__init__(self, args=(), kwargs=None)
        self.setDaemon(True)
        self.start()

    def run(self):
        min_power = 8000 # Minimum power value of graph axes, avoids graph showing loads of movement when it's just noise.
        while True:
            signal = self.listener.get_item('signal')
            signal_max = max(abs(signal)) * (1 + Y_PADDING) # Pad Y maximum/minimum so line doesn't hit top of graph.
            y_max = signal_max if signal_max > min_power else min_power # If mainly noise in signal use min_power as graph max/min.
            self.plot.set_ylim([-y_max, y_max])
            self.line.set_ydata(resample(signal, len(signal) // DOWNSAMPLE_RATE))
            time.sleep(0.1)

class SpectrumPlotter(threading.Thread):
    """ Retrieves signal data, downsamples and sets new Y data and limits. """
    def __init__(self, listener, plot, line):
        self.listener = listener
        self.plot = plot
        self.line = line

        threading.Thread.__init__(self, args=(), kwargs=None)
        self.setDaemon(True)
        self.start()

    def run(self):
        while True:
            spectrum = self.listener.get_item('spectrum')
            downsampled_spectrum = resample(spectrum, len(spectrum) // DOWNSAMPLE_RATE)
            self.plot.set_ylim([0, max(downsampled_spectrum) * (1 + Y_PADDING)])
            self.line.set_ydata(downsampled_spectrum)
            time.sleep(0.1)

class Debugger(tk.Tk):
    """ Setup debugger UI to display analysis results from rtmaii.

    """
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.config(bg=BACKGROUND_COLOR)
        self.listener = Listener()
        self.setup()
        self.update()

    def changetrack(self):
        self.is_live = False
        self.track = tk.filedialog.askopenfilename(initialdir = "/", title = "Select track", filetypes = (("wave files","*.wav"),("all files","*.*")))
        if self.track :
            self.listener.set_source(self.track)

    def liveinput(self):
        self.is_live = True
        self.listener.set_source(None)

    def update(self):
        """ Update UI every FRAME_DELAY milliseconds """
        self.update_graphs()
        self.update_labels()
        self.update_controls()
        self.after(FRAME_DELAY, self.update)

    def update_labels(self):
        # --- UPDATE LABELS --- #
        self.pitch.set("{0:.2f}".format(self.listener.get_item('pitch')))
        key = self.listener.get_item('key')
        self.key.set(key['key'])
        self.cent.set(key['cents_off'])
        self.genre.set(self.listener.get_item('genre'))
        #bpm stuff
        self.beats.set(self.listener.get_item('beats'))
        self.bpm.set(self.listener.get_item('bpm'))
        bands = self.listener.get_item('bands')
        # Update each band value.
        for key, value in bands.items():
            self.bands[key].set("{0:.2f}".format(value))

    def update_controls(self):
        # --- UPDATE CONTROLS --- #
        if self.listener.is_active():
            self.play.config(state='disabled')
            self.pause.config(state='normal')
            self.stop.config(state='normal')
        else:
            self.play.config(state='normal')
            self.pause.config(state='disabled')
            self.stop.config(state='disabled')

        if self.is_live:
            self.live.config(state='disabled')
        else:
            self.live.config(state='normal')

    def update_graphs(self):
        # --- UPDATE GRAPHS --- #
        curr_time = time.time()
        if self.spectro_time - curr_time <= 0: # Plot spectrogram every now and again.
            self.spectrogram_plot.clear()
            self.spectrogram_plot.set_title('Spectrogram')
            self.spectrogram_plot.set_xlabel('Time')
            self.spectrogram_plot.set_ylabel('Frequency (Hz)')
            data = self.spectro_thread.get_spectro_data()

            self.spectrogram_plot.pcolormesh(data[0], data[1], data[2])
            self.spectrogram_plot.set_xlim(0, 1.5)
            self.spectrogram_plot.set_ylim(0, 20000)
            self.spectrogram_canvas.draw()
            self.spectro_time = time.time() + SPECTRO_DELAY # After SPECTRO_DELAY replot.

        # --- FAST PLOTTING METHODS --- #
        self.signal_canvas.restore_region(self.clear_background) # Clear background.
        self.signal_plot.draw_artist(self.signal_line) # Draw new data.
        self.signal_canvas.blit(self.signal_plot.bbox) # Display new data in plot.
        self.spectrum_canvas.restore_region(self.clear_background)
        self.spectrum_plot.draw_artist(self.spectrum_line)
        self.spectrum_canvas.blit(self.spectrum_plot.bbox)

    def setup(self):
        """Create UI elements and assign configurable elements. """
        chunk_size = self.listener.analyser.config.get_config('frames_per_sample')
        frequency_length = self.listener.analyser.config.get_config('frequency_resolution')
        frequencies = fftfreq(frequency_length, 1 / SAMPLING_RATE)[::DOWNSAMPLE_RATE]
        self.frequencies = frequencies[:len(frequencies)//2]

        # --- INIT SETUP --- #
        self.timeframe = arange(0, chunk_size, DOWNSAMPLE_RATE) # Where DOWNSAMPLE_RATE = steps taken.
        self.title("RTMAAI VISUALIZER")
        self.setup_control_panel()
        self.setup_left_frame()
        self.setup_right_frame()

        self.is_live = False
        self.spectro_time = time.time() # Initial ticker for spectorgram plotting.

    def setup_signal_graph(self, frame):
        # --- SIGNAL GRAPH SETUP --- #
        signal_frame = Figure(figsize=(7, 4), dpi=100)
        self.signal_plot = signal_frame.add_subplot(111)
        self.signal_canvas = FigureCanvasTkAgg(signal_frame, frame)
        self.signal_canvas.show()
        self.clear_background = self.signal_canvas.copy_from_bbox(self.signal_plot.bbox)
        self.signal_line, = self.signal_plot.plot(self.timeframe, self.timeframe)
        self.signal_plot.set_title('Signal')
        self.signal_plot.set_xlabel('Time (Arbitary)')
        self.signal_plot.set_ylabel('Amplitude')
        self.signal_plot.get_xaxis().set_ticks([])
        self.signal_plot.get_yaxis().set_ticks([])
        self.signal_canvas.get_tk_widget().pack(pady=INNERPADDING, padx=INNERPADDING)
        SignalPlotter(self.listener, self.signal_plot, self.signal_line)

    def setup_spectrum_graph(self, frame):
        # --- SPECTRUM GRAPH SETUP --- #
        spectrum_frame = Figure(figsize=(7, 4), dpi=100)
        self.spectrum_plot = spectrum_frame.add_subplot(111)
        self.spectrum_canvas = FigureCanvasTkAgg(spectrum_frame, frame)
        self.spectrum_canvas.show()
        self.spectrum_line, = self.spectrum_plot.plot(self.frequencies, self.frequencies)
        self.spectrum_plot.set_title('Spectrum')
        self.spectrum_plot.set_xlabel('Frequency (Hz)')
        self.spectrum_plot.set_ylabel('Power')
        self.spectrum_plot.get_yaxis().set_ticks([])
        self.spectrum_canvas.get_tk_widget().pack(pady=(0, INNERPADDING), padx=INNERPADDING)
        SpectrumPlotter(self.listener, self.spectrum_plot, self.spectrum_line)

    def setup_spectrogram_graph(self, frame):
        # --- SPECTROGRAM GRAPH --- #
        spectrogram_border = tk.Frame(frame, bg=TRIM_COLOR)
        spectrogram_border.pack(side=tk.BOTTOM, padx=XPADDING, pady=XPADDING)
        spectrogram_frame = Figure(figsize=(7, 4), dpi=100)
        self.spectrogram_plot = spectrogram_frame.add_subplot(111)
        self.spectrogram_canvas = FigureCanvasTkAgg(spectrogram_frame, spectrogram_border)
        self.spectrogram_canvas.show()
        self.spectrogram_canvas.get_tk_widget().pack(padx=INNERPADDING, pady=INNERPADDING, side=tk.BOTTOM)
        self.spectro_thread = SpectrogramCompression(self.listener)

    def setup_media_controls(self, frame):
        # --- MEDIA CONTROLS --- #
        self.fast_rewind = tk.Button(frame, text="Fast Rewind", command=partial(self.listener.change_analysis, 10), bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE))
        self.fast_rewind.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT, ipadx=INNERPADDING, ipady=INNERPADDING)
        self.fast_rewind_icon = tk.PhotoImage(file="./assets/FastRewind.png", master=self)
        self.fast_rewind.config(image=self.fast_rewind_icon)

        self.rewind = tk.Button(frame, text="Rewind", command=partial(self.listener.change_analysis, 1), bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE))
        self.rewind.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT, ipadx=INNERPADDING, ipady=INNERPADDING)
        self.rewind_icon = tk.PhotoImage(file="./assets/Rewind.png", master=self)
        self.rewind.config(image=self.rewind_icon)

        self.play = tk.Button(frame, text="Play", command=self.listener.start_analysis, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE))
        self.play.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT, ipadx=INNERPADDING, ipady=INNERPADDING)
        self.play_icon = tk.PhotoImage(file="./assets/Play.png", master=self)
        self.play.config(image=self.play_icon)

        self.pause = tk.Button(frame, text="Pause", command=self.listener.pause_analysis, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE))
        self.pause.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT, ipadx=INNERPADDING, ipady=INNERPADDING)
        self.pause_icon = tk.PhotoImage(file="./assets/Pause.png", master=self)
        self.pause.config(image=self.pause_icon)

        self.stop = tk.Button(frame, text="Stop", command=self.listener.stop_analysis, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE))
        self.stop.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT, ipadx=INNERPADDING, ipady=INNERPADDING)
        self.stop_icon = tk.PhotoImage(file="./assets/Stop.png", master=self)
        self.stop.config(image=self.stop_icon)

        self.forward = tk.Button(frame, text="Forward", command=partial(self.listener.change_analysis, -1), bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE))
        self.forward.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT, ipadx=INNERPADDING, ipady=INNERPADDING)
        self.forward_icon = tk.PhotoImage(file="./assets/Forward.png", master=self)
        self.forward.config(image=self.forward_icon)

        self.fast_forward = tk.Button(frame, text="Fast Forward", command=partial(self.listener.change_analysis, -10), bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE))
        self.fast_forward.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT, ipadx=INNERPADDING, ipady=INNERPADDING)
        self.fast_forward_icon = tk.PhotoImage(file="./assets/FastForward.png", master=self)
        self.fast_forward.config(image=self.fast_forward_icon)

    def setup_source_controls(self, frame):
        # --- SOURCE CONTROLS --- #
        self.browse = tk.Button(frame, text="Browse", command=self.changetrack, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE))
        self.browse.pack(padx=(100, XPADDING), fill=tk.X, side=tk.LEFT, ipadx=INNERPADDING, ipady=INNERPADDING)
        self.browse_icon = tk.PhotoImage(file="./assets/Browse.png", master=self)
        self.browse.config(image=self.browse_icon)

        self.live = tk.Button(frame, text="Live", command=self.liveinput, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE))
        self.live.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT, ipadx=INNERPADDING, ipady=INNERPADDING)
        self.live_icon = tk.PhotoImage(file="./assets/Live.png", master=self)
        self.live.config(image=self.live_icon)

    def setup_pitch_label(self, frame):
        # --- PITCH LABEL --- #
        self.pitch = tk.StringVar()
        pitch_label = tk.Label(frame, text=str('Pitch:'), bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        pitch_label.place(x=450, y=0, height=30, width=50)
        pitch_value = tk.Label(frame, textvariable=self.pitch, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        pitch_value.place(x=500, y=0, height=30, width=100)

    def setup_key_label(self, frame):
        # --- KEY LABEL --- #
        self.key = tk.StringVar()
        key_label = tk.Label(frame, text=str('Key:'), bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        key_label.place(x=100, y=0, height=30, width=40)
        key_value = tk.Label(frame, textvariable=self.key, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        key_value.place(x=140, y=0, height=30, width=80)

        self.cent = tk.StringVar()
        cent_value = tk.Label(frame, textvariable=self.cent, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        cent_value.place(x=220, y=0, height=30, width=50)

    def setup_genre_label(self, frame):
        # --- GENRE LABEL --- #
        self.genre = tk.StringVar()
        genre_label = tk.Label(frame, text=str('Genre:'), bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        genre_label.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
        genre_value = tk.Label(frame, textvariable=self.genre, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        genre_value.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)

    def setup_bpm_label(self, frame):
        # --- BPM LABEL --- #
        self.bpm = tk.StringVar()
        bpm_label = tk.Label(frame, text=str('BPM:'), bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        bpm_label.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
        bpm_value = tk.Label(frame, textvariable=self.bpm, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        bpm_value.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)

    def setup_beats_label(self, frame):
        # --- Beats LABEL --- #
        self.beats = tk.StringVar()
        beats_label = tk.Label(frame, text=str('Beats:'), bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        beats_label.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
        beats_value = tk.Label(frame, textvariable=self.beats, bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        beats_value.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)

    def setup_bands_label(self, frame):
        # --- BANDS LABEL --- #
        self.bands = {}
        chosen_bands = self.listener.get_item('bands')
        bands_frame = tk.LabelFrame(frame, borderwidth=1, text="Analysed Bands", bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE), highlightbackground=TRIM_COLOR, highlightthickness=4)
        bands_frame.pack(padx=10, pady=10)

        for key, _ in chosen_bands.items():
            self.bands[key] = tk.IntVar()
            band_frame = tk.Frame(bands_frame, borderwidth=1, bg=ACCENT_COLOR)
            band_frame.pack()
            key_label = tk.Label(band_frame, text='{}: '.format(key), foreground=TEXT_COLOR, bg=ACCENT_COLOR, font=(None, FONT_SIZE))
            key_label.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
            value_label = tk.Label(band_frame, textvariable=self.bands[key], foreground=TEXT_COLOR, bg=ACCENT_COLOR, font=(None, FONT_SIZE))
            value_label.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)

    def setup_pitch_frame(self, frame):
        # --- PITCH FRAME --- #
        pitch_frame = tk.Frame(frame, borderwidth=1, bg=ACCENT_COLOR, height=32)
        pitch_frame.pack(padx=10, fill=tk.X)
        pitch_frame.pack_propagate(0)
        self.setup_key_label(pitch_frame)
        self.setup_pitch_label(pitch_frame)

    def setup_genrebeat_frame(self, frame):
        # --- GENRE & BEAT FRAME --- #
        gb_frame = tk.Frame(frame, borderwidth=1, bg=ACCENT_COLOR)
        gb_frame.pack(padx=10)
        self.setup_genre_label(gb_frame)
        self.setup_beats_label(gb_frame)
        self.setup_bpm_label(gb_frame)

    def setup_control_panel(self):
        # --- CONTROL FRAME --- #
        control_background = tk.Frame(self, borderwidth=1, bg='#49516F')
        control_background.pack(side=tk.TOP, pady=(0,10), ipady=INNERPADDING, fill='x')
        control_frame = tk.Frame(control_background, bg='#49516F', pady=5)
        control_frame.pack(side=tk.TOP)

        self.setup_media_controls(control_frame)
        self.setup_source_controls(control_frame)

    def setup_value_frame(self, frame):
        # --- VALUE FRAME --- #
        value_frame = tk.LabelFrame(frame, borderwidth=1, width=500, height=500, text="Analysed Values", bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE), highlightbackground=TRIM_COLOR, highlightthickness=4)
        value_frame.pack(side=tk.TOP, padx=XPADDING, pady=XPADDING, fill='x')

        self.setup_pitch_frame(value_frame)
        self.setup_genrebeat_frame(value_frame)
        self.setup_bands_label(value_frame)

    def setup_left_frame(self):
        # --- LEFT FRAME---- #
        left_frame = tk.Frame(self, borderwidth=1, width=500, height=500, bg=TRIM_COLOR)
        left_frame.pack(side=tk.LEFT, padx=(XPADDING, 0))
        self.setup_signal_graph(left_frame)
        self.setup_spectrum_graph(left_frame)

    def setup_right_frame(self):
        # --- RIGHT FRAME --- #
        right_frame = tk.Frame(self, borderwidth=1, width=500, height=500, bg=BACKGROUND_COLOR)
        right_frame.pack(side=tk.RIGHT)

        self.setup_spectrogram_graph(right_frame)
        self.setup_value_frame(right_frame)

def main():
    debugger = Debugger()
    debugger.mainloop()

if __name__ == '__main__':
    main()
