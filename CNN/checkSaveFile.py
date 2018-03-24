import pickle
import numpy as np
from numpy.linalg import norm

with open(r"C:\Users\RalphRaulePC\Documents\FinalYearProject\CO600-Musical-Analysis\CNN\save.p", "rb") as input_file:
    debuggerSpectrograms = pickle.load(input_file)

#with open(r"C:\Users\RalphRaulePC\Documents\FinalYearProject\CO600-Musical-Analysis\CNN\TestClassify\OwnRockSpectrogram", "rb") as input_file:
#    trainingSpectrograms = pickle.load(input_file)

differenceArray = []

print("size of debbugger:", len(debuggerSpectrograms))
#print("size of training:", len(trainingSpectrograms))

#differenceArray = []

debuggerSpectrograms = np.array(debuggerSpectrograms)
#trainingSpectrograms = np.array(trainingSpectrograms)
print(debuggerSpectrograms[2][0][0])
#print(trainingSpectrograms[2][0][0])


for i in range (0, 1000):
    pass
    #print ("what", i)
    #print(np.subtract(debuggerSpectrograms[i][0][0], trainingSpectrograms[i][0][0]))




#for i in e:
#    print(i)
