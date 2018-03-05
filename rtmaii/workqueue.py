from collections import deque
from threading import Condition

class WorkQueue(object):
    def __init__(self, queue_length):
        self.condition = Condition()
        self.queue = deque([], queue_length) if queue_length else deque()

    def get(self):
        """ Get last added item from work queue. If empty sleep thread. """
        self.condition.acquire()
        self.condition.wait()
        data = self.queue.popleft()
        self.condition.release()
        return data

    def get_all(self):
        """ Get all items currently present in work queue. If empty sleep thread. """
        self.condition.acquire()
        self.condition.wait()
        data = []
        while len(self.queue) > 0:
            data.extend(self.queue.popleft())
        self.condition.release()
        return data

    def put(self, data):
        self.condition.acquire()
        self.queue.append(data)
        self.condition.notify()
        self.condition.release()