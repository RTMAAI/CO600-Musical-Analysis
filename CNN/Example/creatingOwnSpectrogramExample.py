import numpy as np
from matplotlib import pyplot as plt
import scipy.io.wavfile
from random import shuffle
import pickle
import wave
import os


# Genre lists - You will have to add a new list if you want to add a new genre
rock_set = []
folk_set = []
hiphop_set = []
electronic_set = []

# These 2 lists will be exported for training 
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

def normalize(ffts):
    ''' '''

    norm_ffts = np.linalg.norm(ffts)
    if norm_ffts == 0:
        return ffts
    return ffts / norm_ffts


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

converterMusicToData(os.path.join(os.path.dirname(__file__),"Example_Music/rock_example.wav"), rock_set)

shuffle(rock_set)

print("Rock set made")

print("Creating Electronic Set ")

converterMusicToData(os.path.join(os.path.dirname(__file__),"Example_Music/electric_example.wav"), electronic_set)

shuffle(electronic_set)

print("Creating Folk Set ")

converterMusicToData(os.path.join(os.path.dirname(__file__),"Example_Music/folk_example.wav"), folk_set)


shuffle(folk_set)
print("Folk set made")
print("Creating Hip Hop Set ")

converterMusicToData(os.path.join(os.path.dirname(__file__),"Example_Music/hiphop_example.wav"), hiphop_set)

shuffle(hiphop_set)
print("Hip Hop set made")

print("Available Spectrograms ")
print("Number of Rock Spectrograms: ", len(rock_set))
print("Number of Folk Spectrograms: ", len(folk_set))
print("Number of Hip Hop Spectrograms: ", len(hiphop_set))
print("Number of Electronic Spectrograms: ", len(electronic_set))


print("Creating Training Dataset....")
spectrogram_traning.extend(rock_set[0:250])
spectrogram_traning.extend(folk_set[0:250])
spectrogram_traning.extend(hiphop_set[0:250])
spectrogram_traning.extend(electronic_set[0:250])

print("Creating Evalution Dataset....")
spectrogram_evalu.extend(rock_set[250:350])
spectrogram_evalu.extend(folk_set[250:350])
spectrogram_evalu.extend(hiphop_set[250:350])
spectrogram_evalu.extend(electronic_set[250:350])

print("Shuffling Data")

shuffle(spectrogram_traning)
shuffle(spectrogram_evalu)

print("Spilting spectrogram data from spectrogram label")

spectrogram_traningX, spectrogram_traningY = zip(*spectrogram_traning)

spectrogram_evaluX, spectrogram_evaluY = zip(*spectrogram_evalu)

print("Saving Dataset")

with open(os.path.join(os.path.dirname(__file__),"Training_Dataset/spectrogram_traningX"), 'wb') as f:
     pickle.dump(spectrogram_traningX, f)

with open(os.path.join(os.path.dirname(__file__),"Training_Dataset/spectrogram_traningY"), 'wb') as f:
    pickle.dump(spectrogram_traningY, f)

with open(os.path.join(os.path.dirname(__file__),"Evaluator_Dataset/spectrogram_evaluX"), 'wb') as f:
    pickle.dump(spectrogram_evaluX, f)

with open(os.path.join(os.path.dirname(__file__),"Evaluator_Dataset/spectrogram_evaluY"), 'wb') as f:
    pickle.dump(spectrogram_evaluY, f)




