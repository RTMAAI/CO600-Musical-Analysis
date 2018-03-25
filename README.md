# ![Logo](./assets/RTMALOGO.png "RTMA")

[![Coverage Status](https://coveralls.io/repos/github/RTMAAI/CO600-Musical-Analysis/badge.svg?branch=master)](https://coveralls.io/github/RTMAAI/CO600-Musical-Analysis?branch=master)
[![Build Status](https://travis-ci.org/RTMAAI/CO600-Musical-Analysis.svg?branch=master)](https://travis-ci.org/RTMAAI/CO600-Musical-Analysis)
[![BCH compliance](https://bettercodehub.com/edge/badge/andrewmumblebee/CO600-Musical-Analysis?branch=master)](https://bettercodehub.com/)

## Authors

* Laurent Baeriswyl
* Ralph Jacob Raule
* Andrew Harris

## Description

RTMA is a Python library that allows you to monitor live music and create audio-responsive software!

## Features

* Detects and responds to beats in a signal.
* Performs BPM analysis
* Fundamental Pitch and Note analysis
* Frequency band analysis
* Genre classification

...All in real time!

Our library's tasks are built as a hierarchy of threaded workers, we sample audio data using a Python wrapper called Pyaudio which sits on top of Portaudio an audio IO library.

This sampled audio data is sent down through our hierarchy to each our nodes in the hierarchy.

Each node has it's own processing queue (WorkQueue). When an item is added, the thread will process the data, and either raise an event signal and/or send the processed data to other nodes in the Hierarchy.

![Hierarchy](./assets/hierarchy.png "Hierarchy")

Some of the nodes in our hierarchy will raise event signals (Shown by the **!** in the image above.)

Any function can be set up to receive these signals, meaning any time a signal is raised the function will be called.

This is achieved through Pydispatcher, which is an implementation of the Observer pattern.

By hooking up a function to an event, you can use to function to retrieve any metric we analyse and do any further processing.

The hierarchy has been designed to be flexible, so nodes can be removed and added with ease. You can even develop your own node!

### Why Use This Library

Imagine you were writing a video game which had a beautiful soundtrack, but you felt like the soundtrack doesn't match the gameplay.

You could use our library to analyse the soundtrack, listening to the BPM, speeding up enemy movement based on the current average.

Or you could check for each beat that occurs in a soundtrack, and cause enemies to move only when this happens.

Maybe you want to find out the genre of a song, use our classification, and change environments based on it.

Perhaps you are creating a runner game, you could create platforms on the fly based on the fundamental pitch of the song.

Making steps higher as the pitch rises, and steps lower as it drops.

Have an audio interface connected to your machine, analysing each musicians audio?

You can turn off our 'Merge_Channels' setting to analyse each channel on it's own, finding metrics for each musician.

The possibilities are endless and our library provides you the means to extend these possibilities!

## Getting Started

## Windows

Installing our library (PowerShell):

```powershell
    # With Project Folder as current context
    python -m virtualenv VENV # Just to make sure you are using same package versions
    .\init.ps1 # Installs python packages and activates virtualenv
```

## Linux

Linux users will first need to install and compile [Portaudio](http://www.portaudio.com/), in order for Pyaudio to be installed.

Please refer to [this](https://askubuntu.com/questions/736238/how-do-i-install-and-setup-the-environment-for-using-portaudio) helpful stackoverflow article for set up steps.

Installing our library (Bash):

```bash
    # With Project Folder as current context
    python -m virtualenv venv # Just to make sure you are using same package versions
    .\init.sh # Installs python packages and activates virtualenv
```

## Mac

Mac users will first need to install [Portaudio](http://www.portaudio.com/), in order for Pyaudio to be installed.

This can be achieved using [Homebrew](https://brew.sh/)

```bash
    brew install portaudio
```

Installing our library (Bash):

```bash
    # Some issues may arise due to how matplotlib interacts with python on mac
    # With Project Folder as current context
    python3 -m venv venv # Use python3's venv over virtualenv
    .\init.sh # Installs python packages and activates the virtual environment
```

## Example implementation

Please see the file example_implementation.py for an example implementation using the libraries API.

This gives a basic overview of how you would interact with our API and get started with implementing our analysis.

## Visualizer/Debugger

![Visualizer UI](./assets/visualizer.png "Visualizer UI")

Bundled with our repository, is a script called *debugger.py*

Running ```python .\debugger.py``` will open a Tkinter UI which can be used to run our library and visualize the analysis.

We recommend that you run this first, to get a feel for what the library can analyse.

This script is implemented on top of our library, so you could easily create an application in a similar vain.

If this script fails to run, please open an issue with any errors you encountered and we'll do our best to fix it asap!

![Controls](./assets/controls.png "Controls")

Our rewind controls don't control playback of an audio source (As you can't rewind live audio.).

If you pause the analysis, you can rewind through the last 50 metrics that were analysed, seeing exactly when a beat occured for example.

## Usage

## Prerequisites

This library requires a few pre-requisites in order to run as expected.

* Python version 3+ must be installed.
* All packages within requirements.txt must be installed. (This can be accomplished using the init script)
* Portaudio must be installed on Linux/Mac OSes

## System Requirements

To run our analysis in realtime we have a few requirements, depending on how you configure your library the response of metrics may be slower or faster. We recommend you read through our documentation on Configuration and use our Benchmarking script to find a configuration with a delay you can handle i.e. < 0.5 ms.

* RAM: 2 GB
* CPU: 1.5 GHz+
* To test whether your system can handle realtime analysis please see our **Benchmarking** section.

### Overview

To use the library you will first need to import the rtmaii module into the script you want to use it in.

```python
from rtmaii import Rtmaii
```

----

All the functionality of rtmaii is contained within the Rtmaii class, there are a variety of ways to initiliaze the library.

```python
analyser = rtmaii.Rtmaii([{'function': pitch_callback, 'signal': 'frequency'}],
                            source = r'.\test_data\spectogramTest.wav',
                            config = {
                                'bands': {'myband': [0, 2000]}
                            },
                            mode = 'DEBUG'
                            )
```

For a rundown of the tasks offered within our library see the **Tasks** section below.

For more information on the configuration options available, please see the **Config** section.

----

Rtmaii uses an event driven callback system to provide your scripts with updates on the state of analysis.

```python
def pitch_callback(pitch):
    print(pitch)

analyser = rtmaii.Rtmaii([{'function': pitch_callback, 'signal':'frequency'},
                            source=r'.\test_data\spectogramTest.wav')
```

For more information on the signals available and the data they return, please see the **Callbacks** section.

----

To run analysis you will need to call the start() method on the generated analysis object.

```python
analyser.start()

# Runs forever whilst analyser is active, when a track is used will run until it's finished.
while analyser.is_active():
    pass
```

There are a variety of methods that can be called on the object, please see the **API** section below for more detail.

----

Can't find a task for a metric you want to analyse? Our library allows you to attach new tasks to the analysis with ease.

Don't like the structure of our analysis? Then you can configure it to suit your needs!

```python
analyser.remove_node('SpectrumCoordinator')

analyser.add_node('CustomCoordinator')
```

For detailed information on how to develop your own analysis task/hierarchy, please see our **Custom Hierarchy** section.

## Configuring Audio Source

Our library supports both live audio analysis and audio file analysis.

The audio source can either be configured when initialising the library.

```python
# Using a wav file for audio analysis.
analyser = rtmaii.Rtmaii(source=r'.\\Tracks\\LetItGo.wav')
```

```python
# Using an audio input ID, if the source is not specified, the default input device on your system will be used.
analyser = rtmaii.Rtmaii(source=1)
```

Or changed using our object's set_source() method, allowing you to reuse our analysis object over multiple tracks.

```python
analyser.set_source('.\\Tracks\\LetItGo.wav')
```

**Warning: If you have changed the default audio device settings, i.e. the amount of channels or sampling rate it users. You will need to provide these in the kwargs to avoid any artefacts in the analysis.**

```python
analyser.set_source(1, **{'rate': 96000, 'channels': 3})
```

If you are unsure of the ID of your audio devices, please run.

```python
analyser.get_input_devices()
```

This will print out the input devices on your system along with their IDs.

![input_devices](./assets/input_devices.png "input_devices")

## Tasks

We offer a number of built in tasks, each analysing different aspects of a signal.

These tasks are all enabled by default, so to retrieve their results, make sure to attach a callback to one of their signals.

## Beat detection & BPM analysis

If you need to detect when a beat has occured in a track or in live audio, listen to our 'Beat' signal.

We also calculate an estimate of the BPM based on the time difference between each beat in a track.

**Task**: ['Beat']
**Signals Produced**: ['Beat', 'BPM']

**Signal Returns** 'Beat' -> bool , 'BPM' -> int

## Pitch & Note

We analyse the fundamental frequency (Pitch) of each sample, generating an event containing the result in Hertz.

Further to this, we also perform some small mathmetical equations to find the closest root note on a piano to the fundamental frequency.

The cents off from the root note is also returned in our analysis.

There are a variety of Pitch detection methods that can be used, please see our **Config** section for more details.

**Task**: ['Pitch']
**Signals Produced**: ['Pitch', 'Note']

**Signal Returns** 'pitch' -> int , 'note' -> {'note': str, 'cents_off' int}

## Genre

Our library employs a convolutional neural network (CNN) in our analysis chain.

It classifies the genre of an audio source based on spectrograms that are created from the audio.

Using these images the CNN is able to find patterns that are common in specific genres.

The network currently can classify between, electronic, rock, hip-hop and folk music.

If you would like to retreive the spectrogram data and perform your own analysis, please attach a function to the 'SpectrogramData' signal.

If you would like to export an image of the spectrogram created, and train your own CNN enable the 'Exporter' task.

**Tasks**: ['Genre', 'Exporter']
**Signals Produced**: ['Genre', 'SpectrogramData']

**Signal Returns** 'Genre' -> str , 'SpectrogramData' -> 3d list

## Frequency band presence

During analysis we perform a fourier transform on the input signal to convert the signal to the frequency domain.

From here we can analyse the presence of a given frequency range.

For example, you can analyse how much of the signal is bass frequencies, making a screen rumble based on the proportion.

**Task**: ['Bands']
**Signals Produced**: ['Bands']

**Signal Returns** 'Bands' -> dict

## Config

There are a variety of configuration options for the library that can help to tune performance and accuracy if correctly configured.

## Defaults

```python
"merge_channels": True,
"bands": {
        "sub-bass":[20, 60],
        "bass":[60, 250],
        "low-mid":[250, 500],
        "mid":[500, 2000],
        "upper-mid":[2000, 4000],
        "presence":[4000, 6000],
        "brilliance":[6000, 20000]
},
"tasks": {
    "pitch": True,
    "genre": True,
    "beat": True,
    "bands": True
},
"block_size": 16384,
"pitch_algorithm": "auto-correlation",
"frames_per_sample": 1024
```

## Setting Config Options

To set config values either pass them in when you initialise the library.

```python
conf = {
'block_size': 8192,
'tasks': {'pitch': False}
}
analyser = rtmaii.Rtmaii(config=conf)
```

Or set them using the analysis object's set_config() method.

```python
conf = {
'bands': {
    'band1': [200, 600],
    'band2': [400, 800]
    }
}
analyser.set_config(**conf)
```

## Merge channels

```python
"merge_channels": True
```

The merge channels setting controls whether analysis should be done against each channel in the audio source, or a single combined channel.

![Multi-channel analysis](./assets/hierarchy_channels.png "Multi-channel analysis")

Referring to our hierarchy diagram, this in effect duplicates all the nodes underneath the 'Root' Coordinator.

Each channel analysed will then have its own sub-hierarchy underneath the 'Root' Coordinator, and the root coordinator will extract each channel signal and send it down its respective hierarchy.

**Please note that analysing multiple channels raises the computational cost by a factor of N, where N is the number of channels! Be wary of enabling this feature.**

Disabling tasks that aren't needed can help to reduce this cost, if you do want to analyse different audio interface channels, i.e. a Bassist seperately from a Guitarist.

## Pitch method

There are multiple pitch detection methods available in the library, each with their own advantages in different environments.

```python
"pitch_algorithm": "ac" | "zc" | "hps" | "fft"
```

### AutoCorrelation (AC)

Estimate pitch using the [autocorrelation](https://cnx.org/contents/i5AAkZCP@2/Pitch-Detection-Algorithms) method.

*Advantages*:

* Good for repetitive wave forms, i.e. sine waves/saw tooths.
* Represents a pitch closer to what humans hear.

*Disadvantages*:

* Requires convolution to be applied which can be expensive.
* Not great with inharmonics i.e. Guitars/Pianos.
* Accuracy is reduced with sampling rate.

### Zero-Crossings (ZC)

Estimate pitch by simply counting the amount of [zero-crossings](https://ccrma.stanford.edu/~pdelac/154/m154paper.htm).

*Advantages*:

* Good for intermittent stable frequencies, i.e. Guitar Tuners.
* Fast to compute, don't need to apply an FFT.

*Disadvantages*:

* If there is lots of noise or multiple frequencies doesn't work.

### Harmonic Product Spectrum (HPS)

Estimate pitch using the [harmonic product spectrum](http://musicweb.ucsd.edu/~trsmyth/analysis/Harmonic_Product_Spectrum.html) algorithm.

*Advantages*:

* This method is good at finding the true fundamental frequency even if it has a weak power or is missing. The technique amplifies the frequency that the harmonics are a multiple of.

*Disadvantages*:

* Slower than using a naive FFT peak detection and requires a fourier transform, which can be computationally expensive.

### FFT Peak (FFT)

Estimate pitch by finding the peak bin value of the frequency spectrum.

*Advantages*:

* More accurate than Zero-crossings.

*Disadvantages*:

* Not great at detecting pitch with multiple harmonics that have a higher amplitude than the fundamental frequency.
* Requires a fourier transform, so more computationally expensive than zero-crossings.

## Bands

```python
"bands": { #Default
        "sub-bass":[20, 60], # Specified as [min, max] of range.
        "bass":[60, 250],
        "low-mid":[250, 500],
        "mid":[500, 2000],
        "upper-mid":[2000, 4000],
        "presence":[4000, 6000],
        "brilliance":[6000, 20000]
}
```

The bands setting controls the frequency bands you would like to find the presence of.

![Audio Spectrum](./assets/spectrum.png "Audio Spectrum")

When analysing an audio signal, we perform a fourier transform to extract the frequency bins of a windowed signal.

This results in a list containing the values shown in the graph above.

The spectrum retrieved gives the sine wave coefficients that can be used to recreate the complex signal.

Our bands analysis, will take the configured bands of interest and find how much of the signal was made up by that band.

![Bands](./assets/bands.png "Frequency Bands")

The value retrieved is a normalized value between 0-1 and shows the overall power of that band proportional to the power of the entire spectrum.

Use this setting to analyse frequency ranges you are interested in learning more about.

## Frames per sample

```python
"frames_per_sample": 1024 # Default
```

Each time we retrieve data from the audio signal, we wait for a specific amount of data points.

The default is 1024 frames of audio, so on average if the sampling rate of the source was 44.1Khz, we'd sample the signal ~43 times a second.

This setting should be fine on most systems, however, there is a chance that your system might produce a static noise when playing back an audio file.

This is usually because the frames_per_sample setting is too low, meaning it's taking too long for the audio source to extract the data before the next sample is ready.

Increasing this setting can help to alleviate this issue, on the other hand reducing this setting to a value such as 512 can help improve the beat detection.

As each sample will be fed into our hierarchy at a much faster rate, making sure the delay before a beat in a signal and the event being raised is minimal.

## Block Size

```python
"block_size": 16384 # Default, we recommend keeping this to a power of 2 as we use an FFT.
# FFTs are an implementation of a DFT which is especially fast on signal lengths that are a power of 2.
```

The block_size setting can help to improve the accuracy of our pitch detection and bands analysis.

This setting means that our pitch and bands methods will wait until enough signal data has been retrieved before doing any analysis.

With an extended version of the signal over time, we can perform more accurate measurements.

In turn the [frequency resolution](https://community.plm.automation.siemens.com/t5/Testing-Knowledge-Base/Digital-Signal-Processing-Sampling-Rates-Bandwidth-Spectral/ta-p/402991) is increased for spectral based tasks (interval between frequency data points)

Setting this to too high of a value, might slow down the response time, so there is a clear trade-off between accuracy and performance.

## Task Config

```python
"tasks": { # Default
    "pitch": True,
    "genre": True,
    "beat": True,
    "bands": True,
    "exporter": True
}
```

Any of our tasks can be disabled, so that you can only focus on metrics you require, which in turn will greatly improve response times.

```python
conf = { # Focus only on the beat and BPM.
'tasks': {'pitch': False, 'genre': False, 'exporter': False, 'bands' : False}
}
analyser = rtmaii.Rtmaii(config=conf)
```

Note: **If you are adding your own custom nodes, please note that our Coordinators may be removed if they have no peers**

## API

There are a variety of methods available on our analysis object, any that aren't covered above are covered in the following sections.

```python
callbacks = [{'function': custom_node_callback, 'signal':'custom'}]
analyser = rtmaii.Rtmaii(source=r'./test_data/spectogramTest.wav', mode='DEBUG')

analyser.set_callbacks(callbacks)

analyser.start()

while analyser.is_active():
    pass

analyser.remove_callbacks(callbacks)

analyser.set_callbacks([{'function': new_callback, 'signal':'pitch'}])

analyser.start()

end_time = time.time() + 5 # run for 5 seconds
while time.time() < end_time:
    pass
analyser.stop()

```

## Callbacks

Our system makes use of Pydispatcher, to provide a callback system, where once an event is raised any interested parties will be called.

### Adding receivers

To add a receiver, first define a method that will be called when the signal is retrieved. This can be on a class object if desired.

```python

def pitch_callback(_, **kwargs):
    """ Basic signal callback, retrieving pitch data from analysis.
        Kwargs will be passed information about the signal.
        kwargs['signal'] = name of signal that called this function.
    """
    print(kwargs)
    print("Frequency event happened")


callbacks = [{'function': pitch_callback, 'signal':'pitch'}] # Must be provided as a list with this signature.
analyser = rtmaii.Rtmaii(source=r'./test_data/spectogramTest.wav', callbacks=callbacks)
# or attach the callbacks after the object is initialised.
analyser.set_callbacks(callbacks)
```

### Removing receivers

If you no longer want the method to be called when the signal is raised, just repass the same list to our remove_callbacks() method.

```python
analyser.remove_callbacks(callbacks)
```

## Analysis Controls

### Start

This starts the analysis, grabbing samples from Pyaudio and feeding them into our Hierarchy for analysis.

```python
analyser.start()
```

### Pause

If you are analysing an audio file, this will pause the analysis, and restart the analysis from where you left off, if you start again.

```python
analyser.pause()
analyser.start() # Picks up where you left off.
```

This has the same effect as stop for live audio.

### Stop

If you are analysing an audio file, this will stop the analysis, and return the analysis to the beginning of the audio file.

```python
analyser.stop()
```

### Is_Active

This returns a bool, stating whether the analysis is still running or not.

This can be utilized in a while loop, when analysing an audio file, to stop the analysis as soon as the Pyaudio reaches the end of the audio stream.

```python
while analyser.is_active():
    pass
```

## Logging

By default we hide most logging messages, unless they have been raised by critical errors.

We use the Python [logging](https://docs.python.org/3/library/logging.html) module to implement our verbose logging stream.

![Logging messages](./assets/log.png "Logging messages")

These messages are also stored within a rtma-log.log file, so all messages can be analysed after analysis.

If you experience any issues with our library, we recommend that you send over a copy of this file in your issue.

If you want to see more detailed logging, then please input a [logging level](https://docs.python.org/3/library/logging.html#levels) of your choice into our object initialisation.

```python
analyser = rtmaii.Rtmaii(mode='DEBUG')
```

## Custom Hierarchy

Our hierarchy can be manipulated to your will. If you don't like any of the tasks we offer, then you can create your own Workers and Coordinators.

```python
def custom_node_callback():
    """ Basic callback, data is passed in the first param.

        The kwargs param holds extra information about the callback.
    """
    print("I'm a new worker running on the library.")

foobar = 'foobar'

custom_hierarchy = {
    'Node1': {'class_name': 'NewWorker', 'parent': 'SpectrumCoordinator',
                'kwargs':{'user_kwarg': 'helloworld'}},
    'NewCoordinator': {'class_name': 'NewCoordinator',
                        'init_args': (foobar,)}
}

analyser = rtmaii.Rtmaii([{'function': custom_node_callback, 'signal':'custom'}],
                            source=r'./test_data/spectogramTest.wav',
                            mode='DEBUG',
                            custom_nodes=custom_hierarchy)

# Nodes can be added after initialization.
analyser.add_node('NewWorker', **{'generic_arg': 'arg'})
# And promptly removed using their ID.
analyser.remove_node('NewWorker')
```

For a detailed rundown of what our different node types are and how to make your own, please refer to our custom_node_example.py script in the repository.

If you find that the development is too restrictive, please raise an issue and we'll look at improving this feature!

## Benchmarking

Our library has been developed on a variety of systems, however, we can't assure that the analysis will remain realtime.

For this purpose we have developed a benchmarking script, that is included with the repository.

To test the average response time of our tasks, run the code below in your cloned folder.

```powershell
   python ./rtma_benchmarker.py
```

This will run a number of benchmarks on our nodes against your system.

![Benchmarking Results](./assets/benchmarker_output.png "Benchmarking Results")

The results show the average time in seconds, it takes for an audio signal to reach each node and invoke a callback.

If the response times are not adequate, then you can try to find a set of configuration options that match the performance you need.

![Benchmarker Help](./assets/benchmarker_help.png "Benchmarker Help")

Running ```python .\rtma-benchmarker.py -h``` will return all the parameters that can be fed into the script for benchmarking.

For example, if the pitch response was too slow, you could try use the zero-crossings method, by supplying the script with the -p param.

```powershell
   python ./rtma_benchmarker.py -p 'zc'
```

Careful tuning of the system can allow the library to run at realtime on lower spec systems.

Parameters such as bands and tasks should be provided as a dictionary. Be aware that on some operating systems, you will need to escape quotes.

This is because the cmdline might already escape the quotes for you, so the dictionary will be invalid when parsed through JSON.

```powershell
   python ./rtma_benchmarker.py -t '{\"pitch\": false}' # As we're parsing the dicts as JSON all bools must be lowercase.
```

```powershell
   python ./rtma_benchmarker.py -b '{\"low_band\": [0, 200], \"high_band\": [2000, 3000]}' # Changing the bands analysed.
```

```powershell
   python ./rtma_benchmarker.py -m # This will make the benchmarker, create a seperate hierarchy for each channel.
```

Making sure to disable unused systems will also save a huge amount of CPU cycles.

## Testing the library

Our tests are contained within the library itself so can be run at anytime to check for issues.

To run the tests open the folder containing the library and run:

```powershell
    python -m unittest discover
```

## Future

* Nodes have to be added to each 'Channel Hierarchy', would be nice to add a beat detection to just a drum channel, etc.
* Further documentation on development and making pull requests
* As always try to optimize each node further, and reduce memory leakage.

## Issues and feedback

We welcome any feedback and issues against our repository, we are final year university students, so are always looking to improve!
