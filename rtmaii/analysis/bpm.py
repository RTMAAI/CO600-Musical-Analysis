"""BPM Analysis and Beat Detection module.

    - Uses descending velocity algorithm or sound energy algorithm to
    determine beats.
    - Uses spaces between beats to determine bpm.
    - Also includes additional helper functions

"""
import audioop
import logging
import numpy
from scipy.signal import butter, lfilter

LOGGER = logging.getLogger(__name__)

# Beat detection algorithms
def beatdetection(data, threshold):
    """
    Takes data as input and returns true for when a beat occurs

    :param data: raw, high-pass or low-pass chunk of music data
    :param threshold: value of the most recent peak
    :return: The amplitude if there was a beat or false if there wasn't
    """
    amp = getrmsamp(data)

    if amp >= threshold:
        return amp
    return False


def energydetect(amp, energyhistory):
    """

    :param amp:
    :param energyhistory:
    :return:
    """
    if(amp > getaverageenergy(energyhistory) *
       getadjusteddeviation(energyhistory)):
        return True
    return False


#
# Helper methods
#


def getrmsamp(data):
    """
    Returns the root-mean-square amplitude of the audio chunk
    RMS amplitude is well-suited for musical applications because
    it can account for asymetrical waves

    audioop takes the sample width as its second parameter
    where 1=8bit 2=16bit and 4=32bit

    :param data: the musical chunk
    :return: the root-mean-square amplitude of the audio chunk
    """
    return audioop.rms(data, 2)


def shiftenergyhistory(amp, energyhistory):
    """
    Moves the list of energy history so that the newest
    42 chunks of music are being used

    :param amp: the newest amplitude
    :param energyhistory: the list of collected amplitudes
    :return: the new list
    """
    while len(energyhistory) >= 43:
        energyhistory.pop(0)
    energyhistory.append(amp)
    return energyhistory


def getaverageenergy(energyhistory):
    """
    Gets the average local energy on the current energyhistory

    :param energyhistory: the list of collected amplitudes
    :return: the average local energy
    """
    avg = 0
    for amp in energyhistory:
        avg += amp
    return avg/len(energyhistory)


def getadjusteddeviation(energyhistory):
    """

    :param energyhistory:
    :return:
    """
    variance = numpy.var(energyhistory)
    if variance >= 200:
        return 1.1
    elif variance >= 150:
        return 1.2
    elif variance >= 100:
        return 1.3
    elif variance >= 50:
        return 1.4
    return 1.5


#
# BPM Methods
#


def bpmsimple(beatlist):
    """
    computes bpm based on low-passed and high-passed beat times
    :param beatarray: array of low-passed beats
    :param hbeatarray: array of high-passed beats
    :return: approximate bpm
    """
    length = len(beatlist)
    if length >= 2:
        total = 0
        for dif in beatlist:
            adddif = dif
            total = total + adddif

        avg = total/length
        return 60/avg
    return 0


#
# beatlist validation methods
#


def cleanbeatarray(beatlist):
    """
    Validates the data from the beat array and discards outliers and wrong
    results including 0, negative entries or timedif entries higher than 2
    seconds (sub-30 bpm) are unrealistic and the threshold needs to be
    somewhere)


    :param beatarray: A list of beat time differences
    :return: beatarray: A list of beat time differences with validated info
    """
    newlist = []
    for dif in beatlist:
        if dif > 0.18 and dif <= 2:
            newlist.append(dif)
    return newlist


def cleanbeatarrayalt(beatlist):
    """
    Validates the data from the beat array and discards outliers and wrong
    results including 0, negative entries or timedif entries higher than 2
    seconds (sub-30 bpm) are unrealistic and the threshold needs to be
    somewhere)


    :param beatarray: A list of beat time differences
    :return: beatarray: A list of beat time differences with validated info
    """
    for dif in beatlist:
        if dif <= 0.18 or dif > 2:
            beatlist.remove(dif)
    return beatlist


def limitsize(beatlist, size):
    """
    This method takes a list as an input and shortens it to a desirable length

    :param beatlist: A list of beat time differences
    :param size: an int describing the target size of the list
    :return: newlist: a list of beat time differences of the length given in
                        the size int
    """
    LOGGER.info('limitsize called')
    oldentries = len(beatlist - size)
    if oldentries > 0:
        newlist = beatlist[oldentries:]
        return newlist
    return beatlist


def lowpass(low_cut, low_pass, sampling_rate):
    """
    This is technically a band pass filter, although it just cuts out noise
    at the bottom

    :param data:
    :return:
    """
    nyq = sampling_rate/2
    low = low_cut/nyq
    high = low_pass/nyq
    num, denom = butter(5, [low, high], btype='bandpass')
    LOGGER.info('Created Lowpassfilter')
    return {'num': num, 'denom': denom}


def applylowpass(data, num, denom):
    """

    :param data:
    :param num:
    :param denom:
    :return:
    """
    lowpassed = lfilter(num, denom, data)
    return lowpassed
