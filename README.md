[![Coverage Status](https://coveralls.io/repos/github/RTMAAI/CO600-Musical-Analysis/badge.svg?branch=master)](https://coveralls.io/github/RTMAAI/CO600-Musical-Analysis?branch=master)
[![Build Status](https://travis-ci.org/RTMAAI/CO600-Musical-Analysis.svg?branch=master)](https://travis-ci.org/RTMAAI/CO600-Musical-Analysis)
[![BCH compliance](https://bettercodehub.com/edge/badge/andrewmumblebee/CO600-Musical-Analysis?branch=master)](https://bettercodehub.com/)

# CO600-Musical-Analysis
Github for the CO600 project on real-time musical analysis.

## Authors:

* Laurent Testing Baeriswyl
* Ralph Jacob Raule
* Andrew Harris

## Getting Started With Development:

### Windows

```powershell
    # With Project Folder as current context
    python -m virtualenv VENV # Just to make sure you are using same package versions
    .\init.ps1 # Installs python packages and activates virtualenv
```

### Mac/Linux

```bash
    # With Project Folder as current context
    python -m virtualenv VENV # Just to make sure you are using same package versions
    .\init.sh1 # Installs python packages and activates virtualenv
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

For more information on the configuration options available, please see the Config section below.

Rtmaii uses an event driven callback system to provide your scripts with updates on the state of analysis.

```python
    def pitch_callback(pitch):
        print(pitch)

    analyser = rtmaii.Rtmaii([{'function': pitch_callback, 'signal':'frequency'},
                              track=r'.\test_data\spectogramTest.wav')
```

For more information on the signals available and the data they return, please see the Callbacks section below.

To run analysis you will need to run the start method on the generated analysis object.

```python
    analyser.start()

    # Runs forever whilst analyser is active, when a track is used will run until it's finished.
    while analyser.is_active():
        pass
```

There are a variety of methods that can be called on the object, please see the Methods section below for more detail.

### Config


### Callbacks


### Debugger

Run ``` python .\debugger.py ``` to use the debugger view of the library.

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