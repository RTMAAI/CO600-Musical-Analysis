[![Coverage Status](https://coveralls.io/repos/github/RTMAAI/CO600-Musical-Analysis/badge.svg?branch=master)](https://coveralls.io/github/RTMAAI/CO600-Musical-Analysis?branch=master)
[![Build Status](https://travis-ci.org/RTMAAI/CO600-Musical-Analysis.svg?branch=master)](https://travis-ci.org/RTMAAI/CO600-Musical-Analysis)
[![BCH compliance](https://bettercodehub.com/edge/badge/andrewmumblebee/CO600-Musical-Analysis?branch=master)](https://bettercodehub.com/)

# CO600-Musical-Analysis
Github for the CO600 project on real-time musical analysis.

## Authors:

* Laurent Baeriswyl
* Ralph Jacob Raule
* Andrew Harris

## Getting Started With Development:

### Windows

```powershell
    # With Project Folder as current context
    python -m virtualenv VENV # Just to make sure you are using same package versions
    .\init.ps1 # Installs python packages and activates virtualenv
```

### Linux

```bash
    # With Project Folder as current context
    python -m virtualenv venv # Just to make sure you are using same package versions
    .\init.sh # Installs python packages and activates virtualenv
```

### Mac

```bash
    # Some issues may arise due to how matplotlib interacts with python on mac
    # With Project Folder as current context
    python3 -m venv venv # Use python3's venv over virtualenv
    .\init.sh # Installs python packages and activates the virtual environment
```

### Example implementation

Please see the file example_implementation.py for an example implementation using the libraries API.

### Usage
To use the library you will first need to import the rtmaii module into the script you want to use it in.

```python
from rtmaii import Rtmaii
```

All the functionality of rtmaii is contained within the Rtmaii class, there are a variety of ways to initiliaze the library.

```python
analyser = rtmaii.Rtmaii([{'function': pitch_callback, 'signal': 'frequency'}],
                            track = r'.\test_data\spectogramTest.wav',
                            config = {
                                'bands': {'myband': [0, 2000]}
                            },
                            mode = 'DEBUG'
                            )
```

For more information on the configuration options available, please see the Config section.

Rtmaii uses an event driven callback system to provide your scripts with updates on the state of analysis.

```python
def pitch_callback(pitch):
    print(pitch)

analyser = rtmaii.Rtmaii([{'function': pitch_callback, 'signal':'frequency'},
                            track=r'.\test_data\spectogramTest.wav')
```

For more information on the signals available and the data they return, please see the Callbacks section.

To run analysis you will need to run the start method on the generated analysis object.

```python
analyser.start()

# Runs forever whilst analyser is active, when a track is used will run until it's finished.
while analyser.is_active():
    pass
```

There are a variety of methods that can be called on the object, please see the Methods section below for more detail.

Can't find a task for a metric you want to analyse? Our library allows you to attach new tasks to the analysis with ease.

```python
analyser.start()

# Runs forever whilst analyser is active, when a track is used will run until it's finished.
while analyser.is_active():
    pass
```

For detailed information on how to develop your own analysis task, please see our Hierarchy section.

### Config

There are a variety of configuration options for the library that can help to tune performance and accuracy if correctly configured.

#### Defaults

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
"frequency_resolution": 20480,
"pitch_algorithm": "auto-correlation",
"frames_per_sample": 1024
```

#### Merge channels

```python
"merge_channels": True #Default
```

The merge channels setting controls whether analysis should be done against each channel in the audio source, or a single combined channel.

#### Pitch method

There are multiple pitch detection methods available in the library, each with their own advantages in different environments.

```python
"pitch_algorithm": "auto-correlation" || "zc" || "hps" || "fft"
```

##### Auto-Correlation

Estimate pitch using the autocorrelation method.

*Advantages*:

* Good for repetitive wave forms, i.e. sine waves/saw tooths.
* Represents a pitch closer to what humans hear.

*Disadvantages*:

* Requires an FFT which can be expensive.
* Not great with inharmonics i.e. Guitars/Pianos.

##### Zero-Crossings (zc):

Estimate pitch by simply counting the amount of zero-crossings.

*Advantages*:

* Good for intermittent stable frequencies, i.e. Guitar Tuners.
* Fast to compute, don't need to apply an FFT.

*Disadvantages*:

* If there is lots of noise or multiple frequencies doesn't work.

##### Harmonic Product Spectrum (hps):

Estimate pitch using the harmonic product spectrum (HPS) Algorithm.

*Advantages*:

* This method is good at finding the true fundamental frequency even if it has a weak power or is missing. The technique amplifies the frequency that the harmonics are a multiple of.

*Disadvantages*:

* Slower than using a naive FFT peak detection and requires a fourier transform, which can be computationally expensive.

##### FFT Peak (fft):

Estimate pitch by finding the peak bin value of the frequency spectrum.

*Advantages*:

* More accurate than Zero-crossings.

*Disadvantages*:

* Not great at detecting pitch with multiple harmonics that have a higher amplitude than the fundamental frequency.


### Callbacks


### Debugger

Run ``` python .\debugger.py ``` to use the debugger view of the library.

### Hierarchy

## Testing the library:

Our tests are contained within the library itself so can be run at anytime to check for issues.

To run the tests open the folder containing the library and run:
```powershell
    python -m unittest discover
```

## Prerequisites

This library requires a few pre-requisites in order to run as expected.
* Python version 3+ must be installed.
* All packages within requirements.txt must be installed. (This can be accomplished using the init script)

## TODOs:
* Add rewind functionality to debugger
* Add source configuration to debugger
* Fix HPS
* Update hierarchy
* Tinker with configurable settings

        **Advantages**:
            - This method is good at finding the true fundamental frequency even if it has a weak power or is missing.
              The technique amplifies the frequency that the harmonics are a multiple of.
        **Disadvantages**:
            - Slower than using a naive FFT peak detection and requires a fourier transform, which can be computationally expensive.
