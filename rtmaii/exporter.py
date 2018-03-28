import threading
import os
from rtmaii.workqueue import WorkQueue
import _pickle as cPickle
from pydispatch import dispatcher
import pickle



class Exporter(threading.Thread):

    def __init__(self, queue_length: int = 1):
        threading.Thread.__init__(self, args=(), kwargs=None)
        print("Exporter Created")
        self.queue = WorkQueue(queue_length)
        self.setDaemon(True)
        self.start()
        self.spectrumCollection = []

    def run(self):
        while True:
            spectrumData = self.queue.get()
            self.spectrumCollection.append(spectrumData)
            with open(os.path.join(os.path.dirname(__file__),'../CNN/save.p'), "wb")  as output_file:  
                pickle.dump(self.spectrumCollection, output_file)
            
    
        


