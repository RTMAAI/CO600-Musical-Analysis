"""
    BPM analysis module.
    - Uses descending velocity algorithm to determine beats.
    - Uses spaces between beats to determine bpm.

"""

import pyaudio
import audioop
import time
import logging

timelast = 0
timedif = 0
maxpeak = 0
threshold = 0
descrate = 100
LOGGER = logging.getLogger(__name__)

def beatdetection(data):
    """
    Takes data as input and returns true for when a beat occurs
    :param data: raw, high-pass or low-pass music info
    :return: true or false depending on if there was a beat
    """
    amp = audioop.rms(data, 2)
    global maxpeak
    global threshold
    global descrate
    global timelast
    global timedif
    threshold -= descrate

    if(amp > maxpeak):
        maxpeak = amp
    if(amp >= threshold):
        threshold = amp
        currenttime = time.clock()
        if(timelast!=0):
            timedif = currenttime - timelast
        timelast = currenttime
        #LOGGER.info('BEAT!')
        return True
    else:
        return False

def gettimedif():
    if(timedif!=0):
        return timedif

def bpmsimple(beatarray, hbeatarray):
    """
    computes bpm based on low-passed and high-passed beat times
    :param beatarray: array of low-passed beats
    :param hbeatarray: array of high-passed beats
    :return: approximate bpm
    """
    if (len(beatarray)>=4):
        total=0
        for dif in beatarray:
            total += dif
        avg = total/len(beatarray)
        return 60/avg
    else:
        return 39

def cleanbeatarray(beatarray):
    """
    placeholder
    validates the data from the beat array and discards outliers and wrong results
    :param beatarray: the array of beats
    :return:
    """
    LOGGER.info('cleanhere')
    return beatarray

def lowpass(data):
    """
    Placeholder to get minimum implementation working
    :param data:
    :return:
    """
    LOGGER.info('Lowpasshere')

def highpass(data):
    """
    Placeholder to get minimum implementation working
    :param data:
    :return:
    """
    LOGGER.info('Highpasshere')