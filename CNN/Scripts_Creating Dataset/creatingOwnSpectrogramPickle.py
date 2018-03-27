import numpy as np
from matplotlib import pyplot as plt
import scipy.io.wavfile
from random import shuffle
import pickle
import wave
import json


# Genre lists
rock_set = []
folk_set = []
hiphop_set = []
electronic_set = []

# 
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

print("Creating Rock Set ")

converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\Music\rock_part1.wav", rock_set)
converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\Music\rock_part2.wav", rock_set)
converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\Music\rock_part3.wav", rock_set)
converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\Music\rock_FMA_part1.wav", rock_set)

shuffle(rock_set)

print("Rock set made")

print("Creating Electronic Set ")

converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\Music\electric_part1.wav", electronic_set)
converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\Music\electric_part2.wav", electronic_set)
converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\Music\electric_part3.wav", electronic_set)
converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\Music\electric_FMA_part_1.wav", electronic_set)

shuffle(electronic_set)


print("Creating Folk Set ")

converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\Music\folk_part1.wav", folk_set)
converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\Music\folk_part2.wav", folk_set)
converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\Music\folk_part3.wav", folk_set)
converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\Music\folk_FMA_part1.wav", folk_set)
shuffle(folk_set)
print("Folk set made")
print("Creating Hip Hop Set ")

converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\HipHop\hiphop_Part1.wav", hiphop_set)
converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\HipHop\hiphop_Part2.wav", hiphop_set)
converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\HipHop\hiphop_Part3.wav", hiphop_set)
converterMusicToData(r"C:\Users\RalphRaulePC\Music\OwnDataset\Music\hiphop_FMA_Part1.wav", hiphop_set)
shuffle(hiphop_set)
print("Hip Hop set made")

print("Available Spectrograms ")
print("Number of Rock Spectrograms: ", len(rock_set))
print("Number of Folk Spectrograms: ", len(folk_set))
print("Number of Hip Hop Spectrograms: ", len(hiphop_set))
print("Number of Electronic Spectrograms: ", len(electronic_set))


print("Creating Training Dataset....")
spectrogram_traning.extend(rock_set[0:7500])
spectrogram_traning.extend(folk_set[0:7500])
spectrogram_traning.extend(hiphop_set[0:7500])
spectrogram_traning.extend(electronic_set[0:7500])

print("Creating Evalution Dataset....")
spectrogram_evalu.extend(rock_set[7500:9459])
spectrogram_evalu.extend(folk_set[7500:9500])
spectrogram_evalu.extend(hiphop_set[7500:9500])
spectrogram_evalu.extend(electronic_set[7500:9500])

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




