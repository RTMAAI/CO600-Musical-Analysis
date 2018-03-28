"""
    BPM analysis module.
    - Uses descending velocity algorithm to determine beats.
    - Uses spaces between beats to determine bpm.

"""
import audioop
import time
import logging

LOGGER = logging.getLogger(__name__)

#these values were used for the deprecated old beat detection algorithm and are now unnecessary
timelast = 0
timedif = 0
maxpeak = 0
threshold = 0
descrate = 100


#Beat detection algorithms
def beatdetection(data, threshold):
    """
    Takes data as input and returns true for when a beat occurs

    :param data: raw, high-pass or low-pass chunk of music data
    :param threshold: value of the most recent peak
    :return: The amplitude if there was a beat or false if there wasn't
    """
    amp = getRMSAmp(data)

    if(amp >= threshold):
        return amp
    else:
        return False

def energydetect(data, energyhistory):
    return False

#Helper methods
def getRMSAmp(data):
    """
    Returns the root-mean-square amplitude of the audio chunk
    RMS amplitude is well-suited for musical applications because it can account for asymetrical waves

    :param data: the musical chunk
    :return: the root-mean-square amplitude of the audio chunk
    """
    #audioop takes the sample width as its second parameter where 1=8bit 2=16bit and 4=32bit
    return audioop.rms(data, 2)


#BPM Methods
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
    else:
        return 0

#beatlist validation methods
def cleanbeatarray(beatlist):
    """
    Validates the data from the beat array and discards outliers and wrong results
    including 0, negative entries or timedif entries higher than 2 seconds (sub-30 bpm
    are unrealistic and the threshold needs to be somewhere)


    :param beatarray: A list of beat time differences
    :return: beatarray: A list of beat time differences with validated info
    """
    #LOGGER.info('cleanhere')
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
    #LOGGER.info('cleanhere')
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


def findequalspacing(beatlist):
    """
    finds a consistent beat spacing in potentially uneven data

    :param beatlist: any list of time differences between beats
    :return: an average even beat division length
    """
    for x in range(0, len(beatlist)-1):
        proposedlength = beatlist[0]

def equalspacing(proposition, comparison, beatlist):
    """
    recursive function that tries to match even lengths

    :param proposition:
    :param beatlist:
    :return:
    """
    i=0
    #0.05 here should be 50ms
    if(approx_equal(proposition, comparison, 0.05)):
        return True;
    elif (proposition > comparison):
        comparison += beatlist[0]
        equalspacing(proposition, comparison, beatlist[1:])
    elif (proposition < comparison):
        pass

def approx_equal(x, y, dev):
    """
    method to see if two time differences are withing a certain range of each other,
    :param x: the first number
    :param y: the second number
    :param dev: the maximum amount of deviation
    :return: True or False depending on whether x is in the range of y or not
    """
    if (x > y-dev and x < y+dev):
        return True
    else:
        return False



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

#
# Deprecated methods under here.
#

def beatdetectiondeprecated(data):
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