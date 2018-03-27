import pickle
import numpy as np
from numpy.linalg import norm

with open(r"./save.p", "rb") as input_file:
    savedSpectrograms = pickle.load(input_file)

print("Number of Labelled spectrograms:", len(debuggerSpectrograms))

debuggerSpectrograms = np.array(debuggerSpectrograms)

print(debuggerSpectrograms[2][0][0])
#print(trainingSpectrograms[2][0][0])


for i in range (0, 1000):
    pass
    #print ("what", i)
    #print(np.subtract(debuggerSpectrograms[i][0][0], trainingSpectrograms[i][0][0]))

