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

def energydetect(data):
        return False

#brokenbrokenbroken
def gettimedif():
    if(timedif!=0):
        #this needs to be seconds
        return timedif

def bpmsimple(beatlist, hbeatarray):
    """
    computes bpm based on low-passed and high-passed beat times
    :param beatarray: array of low-passed beats
    :param hbeatarray: array of high-passed beats
    :return: approximate bpm
    """
    length = len(beatlist)
    if (length>=2):
        total=0
        for dif in beatlist:
            adddif = dif
            total = total + adddif
            #LOGGER.info(dif)

        avg = total/length
        return 60/avg
        return 38
    else:
        return 39

def cleanbeatarray(beatlist):
    """
    Validates the data from the beat array and discards outliers and wrong results
    including 0, negative entries or timedif entries higher than 2 seconds (sub-30 bpm
    are unrealistic and the threshold needs to be somewhere)


    :param beatarray: A list of beat time differences
    :return: beatarray: A list of beat time differences with validated info
    """
    LOGGER.info('cleanhere')
    newlist = []
    for dif in beatlist:
        if(dif>0.18 and dif<=2):
            newlist.append(dif)
    return newlist

def cleanbeatarrayalt(beatlist):
    """
    Validates the data from the beat array and discards outliers and wrong results
    including 0, negative entries or timedif entries higher than 2 seconds (sub-30 bpm
    are unrealistic and the threshold needs to be somewhere)


    :param beatarray: A list of beat time differences
    :return: beatarray: A list of beat time differences with validated info
    """
    LOGGER.info('cleanhere')
    for dif in beatlist:
        if(dif<=0.18 or dif>2):
            beatlist.remove(dif)
    return beatlist


def limitsize(beatlist, size):
    """
    This method takes a list as an input and shortens it to a desirable length

    :param beatlist: A list of beat time differences
    :param size: an int describing the target size of the list
    :return: newlist: a list of beat time differences of the length given in the size int
    """
    LOGGER.info('limitsize called')
    oldentries = len(beatlist - size)
    if(oldentries>0):
        newlist = beatlist[oldentries:]
        return newlist
    else:
        return beatlist

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