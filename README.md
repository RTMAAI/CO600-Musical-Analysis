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

### Mac/Linux

```bash
    # With Project Folder as current context
    python -m virtualenv VENV # Just to make sure you are using same package versions
    .\init.sh1 # Installs python packages and activates virtualenv
```

### Example implementation

Please see the file example_implementation.py for an example implementation using the libraries API.

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
