""" CUSTOM NODE EXAMPLE """
import time
from rtmaii import rtmaii # Replace with just import rtmaii in actual implementation.
from rtmaii.worker import Worker
from pydispatch import dispatcher

class NewWorker(Worker):
    def __init__(self, channel_id: int):
        Worker.__init__(self, channel_id)

    def run(self):
        # while True: <- would normally be used, to keep thread alive.
        data = self.queue.get()
        dispatcher.send(signal='custom', sender=self.channel_id, data=data)


def main():
    def custom_node_callback(data, **kwargs):
        print("I'm a new worker running on the library.")


    analyser = rtmaii.Rtmaii([{'function': custom_node_callback, 'signal':'custom'}],
                              track=r'./test_data/spectogramTest.wav',
                              mode='DEBUG')

    analyser.add_node('NewWorker')

    analyser.start()

    end_time = time.time() + 10 # run for 10 seconds
    while time.time() < end_time:
        pass
    analyser.stop()

    analyser.set_config(**{'merge_channels': False}) # Analyse multiple channels.
    analyser.set_source(source=r'./test_data/bpmDemo.wav')
    analyser.start()

    end_time = time.time() + 10 # run for 10 seconds
    while time.time() < end_time:
        pass

if __name__ == '__main__':
    main()