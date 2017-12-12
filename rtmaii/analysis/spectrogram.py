import threading
from pydispatch import dispatcher

class Spectrogram_thread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.queue = queue
        self.ffts = []

    def run(self):

        while True:
            fft = self.queue.get()
            if fft is None:
                print("Broken")
                break
            self.ffts.append(fft)
            # Also need to remove previous set of FFTs once there is enough data
            dispatcher.send(signal='spectrogram', sender='spectrogram', data=self.ffts)
            # Create spectrogram when enough FFTs generated
