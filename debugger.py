""" VISUALIZER/DEBUGGER IMPLEMENTATION

    - This script contains an implementation of our library, to visualize metrics analysed.

"""
import threading
import time
from functools import partial
import tkinter as tk

from scipy.signal import resample
from scipy.fftpack import fftfreq
from rtmaii import rtmaii # Replace with just import rtmaii in actual implementation.
from rtmaii.workqueue import WorkQueue
from numpy import arange, zeros, append, concatenate
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
matplotlib.use("TkAgg") # Fastest plotter backend.

# ---- UI/STYLE CONSTANTS ---- #
FRAME_DELAY = 50 # How long between each frame update (ms)
XPADDING = 10
INNERPADDING = 5
BACKGROUND_COLOR = '#3366cc'
ACCENT_COLOR = '#6633cc'
TEXT_COLOR = '#fff'
TRIM_COLOR = '#33cc99'
HEADER_SIZE = 20
FONT_SIZE = 15
FRAME_DELAY = 50 # How long between each frame update (ms)

# ---- GRAPH/ANALYSIS CONSTANTS ---- #
SAMPLING_RATE = 44100 # Default sampling rate 44.1 khz
DOWNSAMPLE_RATE = 4 # Denominator to downsample graph by (Should be set according to system specs.)
GY_PADDING = 0.3 # Amount to pad the maximum Y value of a graph by. (% i.e. 0.1 = 10% padding.)
STATE_COUNT = 50 # Amount of states to store that can be moved through.
SPECTRO_DELAY = 2 # Seconds to wait between each spectrogram plot.
SIGNAL_COUNT = 10 # Amount of samples of a signal to store (FPS of signal graph animation)

class Listener(threading.Thread):
    """ Starts analysis and holds a state of analysed results.

        As the analysis runs, rtmaii will sends signals to Pydispatcher.
        The listener connects a few callbacks to each signal in rtmaii.

        When a callback is run, it will be added to a UI thread queue to be displayed,
        as well as being stored in the Listener's state.
    """
    def __init__(self):
        # The amount of states that can be backtracked is specified by STATE_COUNT
        self.state = {
            'pitch': [0],
            'note': [{'note':"N/A", 'cents_off': 0}],
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
            'beats': ['False'],
            'bpm': [0]
        }

        # These set which callback to use when updating a state on the UI.
        self.callbacks = {
            'bands': self.label_callback,
            'note': self.label_callback,
            'genre': self.label_callback,
            'pitch': self.label_callback,
            'beats': self.beat_callback,
            'bpm': self.label_callback,
            'signal': self.graph_callback,
            'spectogramData': self.graph_callback,
            'spectrum': self.graph_callback
        }

        self.handlers = {} # Stores list of threads to send retrieved data to.
        self.max_index = STATE_COUNT - 1 # Max index to restrict state changes to.
        self.state_head = 0 # Pointer to current state of analysis being displayed.

        callbacks = []
        for key, _ in self.state.items():
            callbacks.append({'function': self.callback, 'signal': key})

        self.analyser = rtmaii.Rtmaii(callbacks,
                                      mode='INFO',
                                      source=r'./test_data/bpmDemo.wav',
                                     )

        self.state['spectrum'].append(arange(self.analyser.config.get_config('frequency_resolution')
                                             // 2))
        self.state['signal'].append(arange(self.analyser.config.get_config('frames_per_sample')))

        for key, _ in self.state.items(): # Fill previous 50 states with default values.
            self.state[key] = self.state[key] * STATE_COUNT

        threading.Thread.__init__(self, args=(), kwargs=None)
        self.setDaemon(True)
        self.start()

    def start_analysis(self):
        """ Start analysis. And reset state pointer. """
        self.state_head = 0
        self.analyser.start()

    def add_handler(self, name: str, handler: object):
        """ Add a thread handler, to handle processing retrieved data.

            Args:
                - name: id to give thread
                - handler: handler thread.
        """
        self.handlers[name] = handler

    def pause_analysis(self):
        """ Pauses analysis. """
        self.analyser.pause()

    def stop_analysis(self):
        """ Stop analysis and clear existing state. """
        self.analyser.stop()

    def change_analysis(self, amount: int):
        """ Go to a particular state in the analysis.

            Args:
                - amount : amount to change current state by (Neg or Pos)
        """
        new_value = self.state_head + amount
        # Enforce value to range of max and min size of state store.
        self.state_head = (0 if new_value < 0 else
                           self.max_index if new_value > self.max_index else new_value)

        # When changing analysis, this adds old data to each handlers threads.
        for key, fun in self.callbacks.items():
            # Usually the data is added by a callback, this fabricates the callback with old data.
            if key == 'signal':
                signals = self.state[key][self.state_head + SIGNAL_COUNT: self.state_head: -1]
                fun(key, concatenate(signals))
            else:
                fun(key, self.state[key][self.state_head])


    def set_source(self, source: str):
        """ Change the analysed source. Basic wrapper.

            Args
                - source: source of input, either file or None.
        """
        self.analyser.set_source(source)

    def is_active(self):
        """ Check that analyser is still running. Basic wrapper. """
        return self.analyser.is_active()

    def run(self):
        """ Keep thread alive. """
        condition = threading.Condition()
        while True:
            condition.acquire()
            condition.wait() # Non-blocking sleep.
            condition.release()

    def put_handler(self, handler: object, data: object):
        """ Add data to a given handler's queue.

            Args:
                - handler: id of signal raised.
                - data: data retrieved.
        """
        self.handlers[handler].queue.put(data)

    def graph_callback(self, signal: str, data: object):
        """ Put graph data on it's own handler thread.

            Args:
                - signal: id of signal raised.
                - data: data retrieved.
        """
        self.put_handler(signal, data)

    def label_callback(self, signal: str, data: object):
        """ Put general metric data onto the label handler thread.

            Args:
                - signal: id of signal raised.
                - data: data retrieved.
        """
        self.put_handler('label', [signal, data])

    def beat_callback(self, _, data: object):
        """ Put general beat data onto the beat handler thread.

            Args:
                - data: data retrieved.
        """
        self.put_handler('beat', data)

    def callback(self, data: object, **kwargs: dict):
        """ Add data to listeners state store, and send to thread handler.

            Args:
                - data: data retrieved.
        """
        signal = kwargs['signal']
        self.state[signal].insert(0, data)
        self.state[signal] = self.state[signal][:STATE_COUNT]
        self.callbacks[signal](signal, data)

    def get_item(self, item: str):
        """ Get the latest value of an item from the listener store.

            Args:
                - item: key of metric to retrieve.
        """
        return self.state[item][self.state_head]


class SpectrogramCompression(threading.Thread):
    """ Compresses the data in the spectrogram, making plotting faster. """
    def __init__(self):
        self.queue = WorkQueue(1)
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.compressed_data = [zeros(64), zeros(64), zeros([64, 64])]
        self.setDaemon(True)
        self.start()

    def run(self):
        while True:
            data = self.queue.get()
            compr_length = len(data[0]) // 2
            color_resample = resample(resample(data[2], compr_length), compr_length, axis=1)
            x_resample = resample(data[0], compr_length)
            y_resample = resample(data[1], compr_length)
            self.compressed_data = [x_resample, y_resample, color_resample]

    def get_spectro_data(self):
        """ As we can't update the data through a matplotlib method remotely,
            The UI grabs the latest data from this thread, every two seconds.
        """
        return self.compressed_data

class SignalPlotter(threading.Thread):
    """ Retrieves signal data, downsamples and sets new Y data and limits. """
    def __init__(self, plot, line):
        self.plot = plot
        self.line = line
        self.queue = WorkQueue(1)

        threading.Thread.__init__(self, args=(), kwargs=None)
        self.setDaemon(True)
        self.start()

    def run(self):
        signal = zeros(1024 * SIGNAL_COUNT)
        min_power = 8000
        while True:
            new_data = self.queue.get()
            signal = append(signal, new_data)
            signal = signal[len(new_data):]
            # Pad Y maximum/minimum so line doesn't hit top of graph.
            signal_max = max(abs(signal)) * (1 + GY_PADDING)
            # If mainly noise in signal use min_power as graph max/min.
            y_max = signal_max if signal_max > min_power else min_power
            self.plot.set_ylim([-y_max, y_max])
            self.line.set_ydata(resample(signal, 1024 // DOWNSAMPLE_RATE))

class SpectrumPlotter(threading.Thread):
    """ Retrieves signal data, downsamples and sets new Y data and limits. """
    def __init__(self, plot, line):
        self.plot = plot
        self.line = line
        self.queue = WorkQueue(1)

        threading.Thread.__init__(self, args=(), kwargs=None)
        self.setDaemon(True)
        self.start()

    def run(self):
        while True:
            spectrum = self.queue.get()
            downsampled_spectrum = resample(spectrum, len(spectrum) // DOWNSAMPLE_RATE)
            self.plot.set_ylim([0, max(downsampled_spectrum) * (1 + GY_PADDING)])
            self.line.set_ydata(downsampled_spectrum)

class LabelHandler(threading.Thread):
    """ Thread responsible for updating labels.

        Each time new data is added to the LabelHandler's queue,
        the LabelHandler will check which label the data belongs to,
        and update the appropriate UI variable to display the latest value.
    """
    def __init__(self):
        self.labels = {}
        self.queue = WorkQueue(5)

        threading.Thread.__init__(self, args=(), kwargs=None)
        self.setDaemon(True)
        self.start()

    def add_label(self, variable, key):
        """ Add a label for the thread to update. """
        self.labels[key] = variable

    def run(self):
        while True:
            data = self.queue.get()
            if data[0] == 'note':
                self.labels['cents'].set(data[1]['cents_off'])
                self.labels['note'].set(data[1]['note'])
            elif data[0] == 'bands':
                for key, value in data[1].items():
                    self.labels[key].set("{0:.2f}".format(value))
            elif data[0] == 'pitch':
                self.labels[data[0]].set("{0:.2f}".format(data[1]))
            else:
                self.labels[data[0]].set(data[1])

class BeatHandler(threading.Thread):
    """ Thread responsible for updating the beat label.

        Each time new data is added to the BeatHandlers's queue,
        the BeatHandler will check whether a beat has occured.
        If a beat has occured the beat label will be updated to display this,
        then after 0.1 seconds the beat label wil return to it's default value.
    """
    def __init__(self, beat):
        self.queue = WorkQueue(1)
        self.beat = beat
        self.beat_cooldown = time.time()
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.setDaemon(True)
        self.start()

    def run(self):
        while True:
            beat = self.queue.get()
            if beat:
                self.beat_cooldown = time.time() + 0.1
                self.beat.set('[O]')
            if self.beat_cooldown - time.time() <= 0:
                self.beat.set('[X]')

class Debugger(tk.Tk):
    """ Setup debugger UI to display analysis results from rtmaii.

    """
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.config(bg=BACKGROUND_COLOR)
        self.listener = Listener()
        self.label_handler = LabelHandler()
        self.uic = {}
        self.listener.add_handler('label', self.label_handler)
        self.setup()
        self.update()

    def changetrack(self):
        """ Opens file dialog to select a wav file for analysis. """
        self.uic['is_live'] = False
        track = tk.filedialog.askopenfilename(initialdir="/", title="Select track",
                                              filetypes=(("wave files", "*.wav"),
                                                         ("all files", "*.*"))
                                             )
        if track:
            self.listener.set_source(track)

    def liveinput(self):
        """ Disables live input button, and sets analyser to use live input. """
        self.uic['is_live'] = True
        self.listener.set_source(None)

    def update(self):
        """ Update UI every FRAME_DELAY milliseconds

            This loops forever, until the UI is closed.
        """
        self.update_graphs()
        self.update_controls()
        self.after(FRAME_DELAY, self.update)

    def update_controls(self):
        """ Updates any control buttons on each update loop. """
        if self.listener.is_active():
            self.uic['play'].config(state='disabled')
            self.uic['pause'].config(state='normal')
            self.uic['stop'].config(state='normal')
        else:
            self.uic['play'].config(state='normal')
            self.uic['pause'].config(state='disabled')
            self.uic['stop'].config(state='disabled')

        if self.uic['is_live']:
            self.uic['live'].config(state='disabled')
        else:
            self.uic['live'].config(state='normal')

    def update_graphs(self):
        """ Performs methods to update graphs on each update loop. """
        curr_time = time.time()
        if self.uic['spectro_time'] - curr_time <= 0: # Plot spectrogram every now and again.
            self.uic['spectrogram_plot'].clear()
            self.uic['spectrogram_plot'].set_title('Spectrogram')
            self.uic['spectrogram_plot'].set_xlabel('Time')
            self.uic['spectrogram_plot'].set_ylabel('Frequency (Hz)')
            data = self.uic['spectro_thread'].get_spectro_data()

            self.uic['spectrogram_plot'].pcolormesh(data[0], data[1], data[2])
            self.uic['spectrogram_plot'].set_xlim(0, 1.5)
            self.uic['spectrogram_plot'].set_ylim(0, 20000)
            self.uic['spectrogram_canvas'].draw()
            self.uic['spectro_time'] = time.time() + SPECTRO_DELAY # After SPECTRO_DELAY replot.

        # --- FAST PLOTTING METHODS --- #
        self.uic['signal_canvas'].restore_region(self.uic['clear_bg']) # Clear background.
        self.uic['signal_plot'].draw_artist(self.uic['signal_line']) # Draw new data.
        self.uic['signal_canvas'].blit(self.uic['signal_plot'].bbox) # Display new data in plot.
        self.uic['spectrum_canvas'].restore_region(self.uic['clear_bg']) # Clear background.
        self.uic['spectrum_plot'].draw_artist(self.uic['spectrum_line']) # Draw new data.
        self.uic['spectrum_canvas'].blit(self.uic['spectrum_plot'].bbox) # Display new data in plot.

    def setup(self):
        """Create UI elements and assign configurable elements. """
        chunk_size = self.listener.analyser.config.get_config('frames_per_sample')
        frequency_length = self.listener.analyser.config.get_config('frequency_resolution')
        frequencies = fftfreq(frequency_length, 1 / SAMPLING_RATE)[::DOWNSAMPLE_RATE]
        self.uic['frequencies'] = frequencies[:len(frequencies)//2]

        # --- INIT SETUP --- #
        self.uic['timeframe'] = arange(0, chunk_size, DOWNSAMPLE_RATE)
        self.title("RTMAAI VISUALIZER")
        self.__setup_control_panel__()
        self.__setup_left_frame__()
        self.__setup_right_frame__()

        self.uic['is_live'] = False
        self.uic['spectro_time'] = time.time() # Initial ticker for spectorgram plotting.

    def __setup_signal_graph__(self, frame: object):
        """ Adds a graph component to hold the signal graph.

            Args:
                - frame: component to add graph to.
        """
        signal_frame = Figure(figsize=(7, 4), dpi=100)
        self.uic['signal_plot'] = signal_frame.add_subplot(111)
        self.uic['signal_canvas'] = FigureCanvasTkAgg(signal_frame, frame)
        self.uic['signal_canvas'].show()
        self.uic['clear_bg'] = (self.uic['signal_canvas']
                                .copy_from_bbox(self.uic['signal_plot'].bbox))
        self.uic['signal_line'], = self.uic['signal_plot'].plot(self.uic['timeframe'],
                                                                self.uic['timeframe'])
        self.uic['signal_plot'].set_title('Signal')
        self.uic['signal_plot'].set_xlabel('Time (Arbitary)')
        self.uic['signal_plot'].set_ylabel('Amplitude')
        self.uic['signal_plot'].get_xaxis().set_ticks([])
        self.uic['signal_plot'].get_yaxis().set_ticks([])
        self.uic['signal_canvas'].get_tk_widget().pack(pady=INNERPADDING, padx=INNERPADDING)
        self.listener.add_handler('signal',
                                  SignalPlotter(self.uic['signal_plot'], self.uic['signal_line']))

    def __setup_spectrum_graph__(self, frame: object):
        """ Adds a graph component to hold the spectrum graph.

            Args:
                - frame: component to add graph to.
        """
        spectrum_frame = Figure(figsize=(7, 4), dpi=100)
        self.uic['spectrum_plot'] = spectrum_frame.add_subplot(111)
        self.uic['spectrum_canvas'] = FigureCanvasTkAgg(spectrum_frame, frame)
        self.uic['spectrum_canvas'].show()
        self.uic['spectrum_line'], = self.uic['spectrum_plot'].plot(self.uic['frequencies'],
                                                                    self.uic['frequencies'])
        self.uic['spectrum_plot'].set_title('Spectrum')
        self.uic['spectrum_plot'].set_xlabel('Frequency (Hz)')
        self.uic['spectrum_plot'].set_ylabel('Power')
        self.uic['spectrum_plot'].get_yaxis().set_ticks([])
        self.uic['spectrum_canvas'].get_tk_widget().pack(pady=(0, INNERPADDING), padx=INNERPADDING)
        self.listener.add_handler('spectrum',
                                  SpectrumPlotter(self.uic['spectrum_plot'],
                                                  self.uic['spectrum_line'])
                                 )

    def __setup_spectrogram_graph__(self, frame: object):
        """ Adds a graph component to hold the spectrogram graph.

            Args:
                - frame: component to add graph to.
        """
        spectrogram_border = tk.Frame(frame, bg=TRIM_COLOR)
        spectrogram_border.pack(side=tk.BOTTOM, padx=XPADDING, pady=XPADDING)
        spectrogram_frame = Figure(figsize=(7, 4), dpi=100)
        self.uic['spectrogram_plot'] = spectrogram_frame.add_subplot(111)
        self.uic['spectrogram_canvas'] = FigureCanvasTkAgg(spectrogram_frame, spectrogram_border)
        self.uic['spectrogram_canvas'].show()
        self.uic['spectrogram_canvas'].get_tk_widget().pack(padx=INNERPADDING, pady=INNERPADDING,
                                                            side=tk.BOTTOM)
        self.uic['spectro_thread'] = SpectrogramCompression()
        self.listener.add_handler('spectogramData', self.uic['spectro_thread'])

    def __setup_logo__(self, frame: object):
        """ Adds the rtma logo to the UI.

            Args:
                - frame: component to add logo to.
        """
        self.uic['logo'] = tk.PhotoImage(file="./assets/Logo.png", master=self)
        imglabel = tk.Label(frame, image=self.uic['logo'], bg=ACCENT_COLOR,
                            foreground=TEXT_COLOR, font=(None, HEADER_SIZE))
        imglabel.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT,
                      ipadx=INNERPADDING, ipady=INNERPADDING)

    def __setup_media_controls__(self, frame: object):
        """ Adds the playback and analysis controls to the UI.

            Args:
                - frame: component to add buttons to.
        """
        # --- FASTREWIND --- #
        fast_rewind = tk.Button(frame, text="Fast Rewind",
                                command=partial(self.listener.change_analysis, 10),
                                bg=ACCENT_COLOR, foreground=TEXT_COLOR,
                                font=(None, HEADER_SIZE))
        fast_rewind.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT,
                         ipadx=INNERPADDING, ipady=INNERPADDING)
        self.uic['fast_rewind_icon'] = tk.PhotoImage(file="./assets/FastRewind.png", master=self)
        fast_rewind.config(image=self.uic['fast_rewind_icon'])

        # --- REWIND --- #
        rewind = tk.Button(frame, text="Rewind",
                           command=partial(self.listener.change_analysis, 1),
                           bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE))
        rewind.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT,
                    ipadx=INNERPADDING, ipady=INNERPADDING)
        self.uic['rewind_icon'] = tk.PhotoImage(file="./assets/Rewind.png", master=self)
        rewind.config(image=self.uic['rewind_icon'])

        # --- PLAY --- #
        self.uic['play'] = tk.Button(frame, text="Play", command=self.listener.start_analysis,
                                     bg=ACCENT_COLOR, foreground=TEXT_COLOR,
                                     font=(None, HEADER_SIZE))
        self.uic['play'].pack(padx=XPADDING, fill=tk.X, side=tk.LEFT,
                              ipadx=INNERPADDING, ipady=INNERPADDING)
        self.uic['play_icon'] = tk.PhotoImage(file="./assets/Play.png", master=self)
        self.uic['play'].config(image=self.uic['play_icon'])

        # --- PAUSE --- #
        self.uic['pause'] = tk.Button(frame, text="Pause", command=self.listener.pause_analysis,
                                      bg=ACCENT_COLOR, foreground=TEXT_COLOR,
                                      font=(None, HEADER_SIZE))
        self.uic['pause'].pack(padx=XPADDING, fill=tk.X, side=tk.LEFT, ipadx=INNERPADDING,
                               ipady=INNERPADDING)
        self.uic['pause_icon'] = tk.PhotoImage(file="./assets/Pause.png", master=self)
        self.uic['pause'].config(image=self.uic['pause_icon'])

        # --- STOP --- #
        self.uic['stop'] = tk.Button(frame, text="Stop", command=self.listener.stop_analysis,
                                     bg=ACCENT_COLOR, foreground=TEXT_COLOR,
                                     font=(None, HEADER_SIZE))
        self.uic['stop'].pack(padx=XPADDING, fill=tk.X, side=tk.LEFT, ipadx=INNERPADDING,
                              ipady=INNERPADDING)
        self.uic['stop_icon'] = tk.PhotoImage(file="./assets/Stop.png", master=self)
        self.uic['stop'].config(image=self.uic['stop_icon'])

        # --- FORWARD --- #
        forward = tk.Button(frame, text="Forward",
                            command=partial(self.listener.change_analysis, -1),
                            bg=ACCENT_COLOR, foreground=TEXT_COLOR, font=(None, HEADER_SIZE))
        forward.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT,
                     ipadx=INNERPADDING, ipady=INNERPADDING)
        self.uic['forward_icon'] = tk.PhotoImage(file="./assets/Forward.png", master=self)
        forward.config(image=self.uic['forward_icon'])

        # --- FASTFORWARD --- #
        fast_forward = tk.Button(frame, text="Fast Forward",
                                 command=partial(self.listener.change_analysis, -10),
                                 bg=ACCENT_COLOR, foreground=TEXT_COLOR,
                                 font=(None, HEADER_SIZE))
        fast_forward.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT,
                          ipadx=INNERPADDING, ipady=INNERPADDING)
        self.uic['fast_forward_icon'] = tk.PhotoImage(file="./assets/FastForward.png", master=self)
        fast_forward.config(image=self.uic['fast_forward_icon'])

    def __setup_source_controls__(self, frame: object):
        """ Adds the source control buttons to the UI.
            I.e. the browse and live input buttons.

            Args:
                - frame: component to add buttons to.
        """
        browse = tk.Button(frame, text="Browse", command=self.changetrack,
                           bg=ACCENT_COLOR, foreground=TEXT_COLOR,
                           font=(None, HEADER_SIZE))
        browse.pack(padx=(100, XPADDING), fill=tk.X, side=tk.LEFT,
                    ipadx=INNERPADDING, ipady=INNERPADDING)
        self.uic['browse_icon'] = tk.PhotoImage(file="./assets/Browse.png", master=self)
        browse.config(image=self.uic['browse_icon'])

        self.uic['live'] = tk.Button(frame, text="Live", command=self.liveinput,
                                     bg=ACCENT_COLOR, foreground=TEXT_COLOR,
                                     font=(None, HEADER_SIZE))
        self.uic['live'].pack(padx=XPADDING, fill=tk.X, side=tk.LEFT,
                              ipadx=INNERPADDING, ipady=INNERPADDING)
        self.uic['live_icon'] = tk.PhotoImage(file="./assets/Live.png", master=self)
        self.uic['live'].config(image=self.uic['live_icon'])

    def __setup_pitch_label__(self, frame: object):
        """ Adds the pitch label components to the UI.

            Args:
                - frame: component to add labels to.
        """
        self.uic['pitch'] = tk.StringVar()
        pitch_label = tk.Label(frame, text=str('Pitch:'), bg=ACCENT_COLOR, foreground=TEXT_COLOR,
                               font=(None, FONT_SIZE))
        pitch_label.place(x=450, y=0, height=30, width=50)
        pitch_value = tk.Label(frame, textvariable=self.uic['pitch'], bg=ACCENT_COLOR,
                               foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        pitch_value.place(x=500, y=0, height=30, width=100)
        self.label_handler.add_label(self.uic['pitch'], 'pitch')

    def __setup_note_label__(self, frame: object):
        """ Adds the note label components to the UI.

            Args:
                - frame: component to add labels to.
        """
        self.uic['note'] = tk.StringVar()
        note_label = tk.Label(frame, text=str('Root Note:'), bg=ACCENT_COLOR, foreground=TEXT_COLOR,
                              font=(None, FONT_SIZE))
        note_label.place(x=40, y=0, height=30, width=110)
        note_value = tk.Label(frame, textvariable=self.uic['note'], bg=ACCENT_COLOR,
                              foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        note_value.place(x=140, y=0, height=30, width=80)
        self.label_handler.add_label(self.uic['note'], 'note')

        self.uic['cent'] = tk.StringVar()
        cent_value = tk.Label(frame, textvariable=self.uic['cent'], bg=ACCENT_COLOR,
                              foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        cent_value.place(x=220, y=0, height=30, width=50)
        self.label_handler.add_label(self.uic['cent'], 'cents')

    def __setup_genre_label__(self, frame: object):
        """ Adds the genre label components to the UI.

            Args:
                - frame: component to add labels to.
        """
        self.uic['genre'] = tk.StringVar()
        genre_label = tk.Label(frame, text=str('Genre:'), bg=ACCENT_COLOR, foreground=TEXT_COLOR,
                               font=(None, FONT_SIZE))
        genre_label.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
        genre_value = tk.Label(frame, textvariable=self.uic['genre'], bg=ACCENT_COLOR,
                               foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        genre_value.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
        self.label_handler.add_label(self.uic['genre'], 'genre')

    def __setup_bpm_label__(self, frame: object):
        """ Adds the BPM label components to the UI.

            Args:
                - frame: component to add labels to.
        """
        self.uic['bpm'] = tk.StringVar()
        bpm_label = tk.Label(frame, text=str('BPM:'), bg=ACCENT_COLOR,
                             foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        bpm_label.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
        bpm_value = tk.Label(frame, textvariable=self.uic['bpm'], bg=ACCENT_COLOR,
                             foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        bpm_value.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
        self.label_handler.add_label(self.uic['bpm'], 'bpm')

    def __setup_beats_label__(self, frame: object):
        """ Adds the Beats label components to the UI.

            Args:
                - frame: component to add labels to.
        """
        self.uic['beats'] = tk.StringVar()
        beats_label = tk.Label(frame, text=str('Beats:'), bg=ACCENT_COLOR, foreground=TEXT_COLOR,
                               font=(None, FONT_SIZE))
        beats_label.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
        beats_value = tk.Label(frame, textvariable=self.uic['beats'], bg=ACCENT_COLOR,
                               foreground=TEXT_COLOR, font=(None, FONT_SIZE))
        beats_value.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
        self.listener.add_handler('beat', BeatHandler(self.uic['beats']))

    def __setup_bands_label__(self, frame: object):
        """ Adds the Bands label components to the UI.

            Args:
                - frame: component to add labels to.
        """
        self.uic['bands'] = {}
        chosen_bands = self.listener.get_item('bands')
        bands_frame = tk.LabelFrame(frame, borderwidth=1, text="Analysed Bands", bg=ACCENT_COLOR,
                                    foreground=TEXT_COLOR, font=(None, HEADER_SIZE),
                                    highlightbackground=TRIM_COLOR, highlightthickness=4)
        bands_frame.pack(padx=10, pady=10)

        for key, _ in chosen_bands.items():
            self.uic['bands'][key] = tk.IntVar()
            band_frame = tk.Frame(bands_frame, borderwidth=1, bg=ACCENT_COLOR)
            band_frame.pack()
            key_label = tk.Label(band_frame, text='{}: '.format(key), foreground=TEXT_COLOR,
                                 bg=ACCENT_COLOR, font=(None, FONT_SIZE))
            key_label.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
            value_label = tk.Label(band_frame, textvariable=self.uic['bands'][key],
                                   foreground=TEXT_COLOR,
                                   bg=ACCENT_COLOR, font=(None, FONT_SIZE))
            value_label.pack(padx=XPADDING, fill=tk.X, side=tk.LEFT)
            self.label_handler.add_label(self.uic['bands'][key], key)

    def __setup_pitch_frame__(self, frame: object):
        """ Adds a frame to the UI for pitch related labels.

            Args:
                - frame: master UI component to add frame to.
        """
        pitch_frame = tk.Frame(frame, borderwidth=1, bg=ACCENT_COLOR, height=32)
        pitch_frame.pack(padx=10, fill=tk.X)
        pitch_frame.pack_propagate(0)
        self.__setup_note_label__(pitch_frame)
        self.__setup_pitch_label__(pitch_frame)

    def __setup_genrebeat_frame__(self, frame: object):
        """ Adds a frame to the UI for genre and beat related labels.

            Args:
                - frame: master UI component to add frame to.
        """
        gb_frame = tk.Frame(frame, borderwidth=1, bg=ACCENT_COLOR)
        gb_frame.pack(padx=10)
        self.__setup_genre_label__(gb_frame)
        self.__setup_beats_label__(gb_frame)
        self.__setup_bpm_label__(gb_frame)

    def __setup_control_panel__(self):
        """ Adds a frame to the UI to create the control panel section. """
        control_background = tk.Frame(self, borderwidth=1, bg='#49516F')
        control_background.pack(side=tk.TOP, pady=(0, 10), ipady=INNERPADDING, fill='x')

        self.__setup_logo__(control_background)

        control_frame = tk.Frame(control_background, bg='#49516F', pady=5)
        control_frame.pack(side=tk.TOP)

        self.__setup_media_controls__(control_frame)
        self.__setup_source_controls__(control_frame)

    def __setup_value_frame__(self, frame: object):
        """ Adds a frame to the UI to encaspulate all the metric labels.

            Args:
                - frame: master UI component to add frame to.
        """
        value_frame = tk.LabelFrame(frame, borderwidth=1, width=500, height=500,
                                    text="Analysed Values", bg=ACCENT_COLOR,
                                    foreground=TEXT_COLOR, font=(None, HEADER_SIZE),
                                    highlightbackground=TRIM_COLOR, highlightthickness=4)
        value_frame.pack(side=tk.TOP, padx=XPADDING, pady=XPADDING, fill='x')

        self.__setup_pitch_frame__(value_frame)
        self.__setup_genrebeat_frame__(value_frame)
        self.__setup_bands_label__(value_frame)

    def __setup_left_frame__(self):
        """ Creates a UI frame that is left-aligned.
            Holds the signal and spectrum graphs.
        """
        left_frame = tk.Frame(self, borderwidth=1, width=500, height=500, bg=TRIM_COLOR)
        left_frame.pack(side=tk.LEFT, padx=(XPADDING, 0))
        self.__setup_signal_graph__(left_frame)
        self.__setup_spectrum_graph__(left_frame)

    def __setup_right_frame__(self):
        """ Creates a UI frame that is right-aligned.
            Holds the metric lables and spectrogram graph.
        """
        right_frame = tk.Frame(self, borderwidth=1, width=500, height=500, bg=BACKGROUND_COLOR)
        right_frame.pack(side=tk.RIGHT)

        self.__setup_spectrogram_graph__(right_frame)
        self.__setup_value_frame__(right_frame)

def main():
    """ Start debugger and run main loop. """
    debugger = Debugger()
    debugger.mainloop()

if __name__ == '__main__':
    main()
