import numpy as np
from matplotlib import pyplot as plt
import scipy.io.wavfile
from random import shuffle
import pickle
import wave

''' Please look at the example before using this script'''
''' This script creates datasets from audio audio files provided to create the cnn model'''

# Genre lists
rock_set = []
folk_set = []
hiphop_set = []
electronic_set = []

spectrogram_traning = []
spectrogram_evalu = []


def findGenre(fileName : str):
    
    if "rock" in fileName:
        return 0
    elif "folk" in fileName:
        return 1
    elif "hiphop" in fileName:
        return 2
    elif "electric" in fileName:
        return 3

def normalize(v):

    norm = np.linalg.norm(v)
    if norm == 0: 
       return v
    return v / norm


def converterMusicToData(file , listToAppendTo):

    wave_file = wave.open(file)
    wave_length = wave_file.getnframes()
    print("wave legth:", wave_length)

    genre = findGenre(file)

    window_size = 1024
    unique = window_size
    hann = np.hanning(window_size)
    Y = []
    
    for i in range(0, wave_length, window_size):
        if i + window_size > wave_length:
            break
        curr_data = np.frombuffer(wave_file.readframes(window_size), dtype=np.int16)   
        y = np.fft.fft(curr_data * hann)[:1024//2]
        y = normalize(y)
        Y.append(y)

        if(len(Y) > 127 ):
            Y = np.column_stack(Y)
            Y = np.absolute(Y) * 2.0 / np.sum(hann)
            Y = Y / np.power(2.0, (8 * 0))
            Y = (20.0 * np.log10(Y)).clip(-120)
            smallerY = []
            for i in range(0, len(Y), 4):
                if i + 4 > len(Y):
                    break

                meanY = (Y[i] + Y[i+1] + Y[i+2] + Y[i+3])/4
                smallerY.append(meanY)

            listToAppendTo.append([smallerY, genre])
            
            Y = []


''' Insert converterMusicToData functions with music files you would like to use to train a model '''

print("Available Spectrograms ")


''' Insert converterMusicToData functions with music files you would like to use to train a model '''


#typically comment out code below to see how many spectrograms you have when readed all 

print("Creating Training Dataset....")
spectrogram_traning.extend(rock_set[0:0])
spectrogram_traning.extend(folk_set[0:0])
spectrogram_traning.extend(hiphop_set[0:0])
spectrogram_traning.extend(electronic_set[0:0])

print("Creating Evalution Dataset....")
spectrogram_evalu.extend(rock_set[0:0])
spectrogram_evalu.extend(folk_set[0:0])
spectrogram_evalu.extend(hiphop_set[0:0])
spectrogram_evalu.extend(electronic_set[0:0])

print("Shuffling Data")

shuffle(spectrogram_traning)
shuffle(spectrogram_evalu)

print("Spilting spectrogram data from spectrogram label")

spectrogram_traningX, spectrogram_traningY = zip(*spectrogram_traning)

spectrogram_evaluX, spectrogram_evaluY = zip(*spectrogram_evalu)

print("Saving Dataset")

with open('spectrogram_traningX', 'wb') as f:
     pickle.dump(spectrogram_traningX, f)

with open('spectrogram_traningY', 'wb') as f:
    pickle.dump(spectrogram_traningY, f)

with open('spectrogram_evaluX', 'wb') as f:
    pickle.dump(spectrogram_evaluX, f)

with open('spectrogram_evaluY', 'wb') as f:
    pickle.dump(spectrogram_evaluY, f)




