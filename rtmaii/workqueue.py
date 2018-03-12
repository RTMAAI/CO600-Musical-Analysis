""" WORK QUEUE MODULE
"""
from collections import deque
from threading import Condition

class WorkQueue(object):
    """ Used by workers and coordinators to manage their internal work queue.

        **Attributes**:
                - `condition`: Queue Lock, allowing threads to wait until they are notified.
                - `queue`: Queue of data to be processed.
    """
    def __init__(self, queue_length: int = None):
        self.condition = Condition()
        self.queue = deque([], queue_length) if queue_length else deque()

    def get(self) -> object:
        """ Get last added item from work queue. If empty sleep thread. """
        with self.condition:
            self.condition.wait()
            data = self.queue.popleft()
        return data

    def get_all(self) -> list:
        """ Get all items currently present in work queue extending the original object.

            If queue is empty `blocks` until an item is available.
        """
        data = []
        with self.condition:
            self.condition.wait()
            if self.queue:
                data.extend(self.queue.popleft())
        return data

    def put(self, data: object):
        """ Put item onto the work queue and send a notification that new item has been added.

            **Args**
            - `data`: data to be added.
        """
        with self.condition:
            self.queue.append(data)
            self.condition.notify()
