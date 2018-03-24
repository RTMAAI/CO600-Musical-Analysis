""" CUSTOM NODE EXAMPLE

    - This example script shows you how to add custom nodes and rework the hierarchy.

    To create your own nodes you will need to create a class object that inherits,
    from either the base Worker class we've created or the Coordinator class.

    Each node type comes with it's own inherited attributes and methods.

    WORKER:

    Process:
        A worker has a processing queue, on which the parent thread will add data to.
        In the run loop of the thread, the worker will grab data from its own queue.
        If there is no data available then the worker will sleep.
        If there is data then the rest of the run loop is run, processing the data.

    Args:
        - queue_length(int): Max length processing queue can reach. (Default 1 for workers)
        - config: Configuration object to fetch analysis settings from. (Provided by kwargs)
        - channel_id: Id of channel this node is analysing. (Provided by kwargs)

    Attributes:
        - queue (WorkQueue): Nodes queue of data to be processed.
        - channel_id (int): id of channel this node is analysing.
        - config (obj): Configuration object to fetch analysis settings from.

    Methods:
        - reset_attributes(): override to reset any attributes on audio source changes.

    COORDINATOR:

    Process:
        - queue (WorkQueue): Coordinators queue of data to be processed.
        - peer_list (list): List of peer threads to communicate processed data with.
        - channel_id (int): Id of channel being analysed.
        - config (Config): Configuration object of library to fetch analysis values from.

    Args:
        - queue_length(int): Max length processing queue can reach.
        - config: Configuration object to fetch analysis settings from. (Provided by kwargs)
        - channel_id: Id of channel this node is analysing. (Provided by kwargs)

    Attributes:
        - queue (WorkQueue): Nodes queue of data to be processed.
        - peer_list (list): List of peer threads to communicate processed data with.
        - channel_id (int): Id of channel this node is analysing.
        - config (obj): Configuration object to fetch analysis settings from.

    Methods:
        - message_peers(data: obj): sends data to all peers in peer_list
        - reset_attributes(): override to reset any attributes on audio source changes.

    WORKQUEUE:
        - The workqueue object attached to nodes is their lifeforce.
        - A node will only awaken whilst there is data in their queue, and sleeps afterwards.

    When initializing nodes, their Workqueue can have a max length set.
    If the queue reaches above this maximum size then when a new item is pushed onto the
    the stack, another item is removed at the opposite end.

    Workers have a default queue_length of 1 because they are by default 'Greedy' and only
    care about the last item that was added to their queue.

    Methods:
        - get(): gets item from front of queue.
        - get_all(): gets all items from the queue as a single list.
        - put(data: obj): adds item to end of a threads queue.
"""
import time
from rtmaii import rtmaii # Replace with just import rtmaii in actual implementation.
from rtmaii.worker import Worker # Import this module to create custom Workers.
from rtmaii.coordinator import Coordinator # Import this module to create custom coordinators.
from pydispatch import dispatcher # To dispatch signals in your node, use this module.
# More information on pydispatch can be found here: http://pydispatcher.sourceforge.net/
class NewWorker(Worker):
    """ Basic Custom Worker Example.

        When creating a custom node, the arg **kwargs must be provided.
        This is because we expose library arguments to this parameter.

        For example kwargs['channel_id'] retrieves the channel this node is analysing.

        kwargs['config'] exposes the config object to your node.

        Using the config object you can retrieve settings such as the sampling_rate.

        Please see our Readme for more information on configuration settings.
    """
    def __init__(self, **kwargs: dict):
        Worker.__init__(self, kwargs['config'], kwargs['channel_id'])
        self.sampling_rate = self.config.get_config('sampling_rate')
        print('Sampling rate: {}'.format(self.sampling_rate))
        # When adding a node, you can specify any number of extra kwargs to pass in.
        print('NewWorker retrieved kwarg["user_kwarg"] with value {}'
              .format(kwargs["user_kwarg"]))

    def reset_attributes(self):
        """ When an audio source is changed this is called to reset dependent attributes.

            Override this method to reset any attributes you need to.

            For example if the sampling_rate were to change from one audio source to another,
            some tasks need to update their calculations to account for this.
        """
        self.sampling_rate = self.config.get_config('sampling_rate')

    def run(self):
        """ Run loop of the node, keep all processing logic within here. """
        # while True: <- would normally be used, to keep thread alive.
        data = self.queue.get()
        dispatcher.send(signal='custom', sender=self.channel_id, data=data)

class NewCoordinator(Coordinator):
    """ Basic Custom Coordinator Example.

        The previous example only needed the kwargs setting.

        However, you may require positional parameters on your node.

        In this case they would be added to the 'init_args' parameter
        when adding the node.
    """
    def __init__(self, arg: str, **_: dict):
        Coordinator.__init__(self)
        # When adding a node, you can specify positional arguments to pass to the node.
        self.var = arg
        print('NewCoordinator set var to {}'.format(self.var))

    def run(self):
        while True: # This is normally used, to keep thread alive during analysis.
            data = self.queue.get()
            dispatcher.send(signal='custom', sender=self.channel_id, data=data)

def main():
    """ Example of methods that can be used to manipulate the hierarchy. """
    def custom_node_callback():
        """ Basic callback, data is passed in the first param.

            The kwargs param holds extra information about the callback.
        """
        print("I'm a new worker running on the library.")

    foobar = 'foobar'

    custom_hierarchy = {
        'Node1': {'class_name': 'NewWorker', 'parent': 'SpectrumCoordinator',
                  'kwargs':{'user_kwarg': 'helloworld'}},
        'NewCoordinator': {'class_name': 'NewCoordinator',
                           'init_args': (foobar,)}
    }

    analyser = rtmaii.Rtmaii([{'function': custom_node_callback, 'signal':'custom'}],
                             track=r'./test_data/spectogramTest.wav',
                             mode='DEBUG',
                             custom_nodes=custom_hierarchy)

    # Nodes can be added after initialization.
    analyser.add_node('NewWorker', **{'generic_arg': 'arg'})
    # And promptly removed using their ID.
    analyser.remove_node('NewWorker')

    # Nodes must have unique IDs, if you reuse a class, please provide an ID.
    analyser.add_node('NewCoordinator', 'Coordinator2', init_args=(foobar,))
    # These then must be removed using the ID you have given them.
    analyser.remove_node('Coordinator2')

    analyser.start()

    end_time = time.time() + 5 # run for 5 seconds
    while time.time() < end_time:
        pass
    analyser.stop()


    """ If analysis is changed to analyse multiple channels asynchronously,
        We have to reconstruct the entire hierarchy. However, any nodes added are preserved.

        The nodes you've added will be added to each invidual channel hierarchy that is created.
        Meaning you can use your nodes to analyse multiple channels at once.
    """
    analyser.set_config(**{'merge_channels': False}) # Analyse multiple channels.
    analyser.set_source(source=r'./test_data/bpmDemo.wav')
    analyser.start()

    end_time = time.time() + 5 # run for 5 seconds
    while time.time() < end_time:
        pass

if __name__ == '__main__':
    main()
