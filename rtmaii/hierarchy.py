from rtmaii.coordinator import Coordinator
from rtmaii.worker import Worker

# TODO: Clean up structure, classify
# TODO: Allow for restructuring of existing hierarchy.
# NOTE: I don't particulary like the way a worker/coordinator has their type added to their class name i.e. BPMCoordinator, these might change to just BPM etc.

def new_hierarchy(config: object):
    """ Create a new hierarchy of communication for the libraries analysis.

        **Args**:
            - Config: a complex object containing configured settings. (Please refer to the configuration module for more information.)
    """
    # Root node is always constructed.
    # Still requires a lot checks.
    tasks = config.get_config('tasks') # The tasks that have been enabled.
    root_peers = []
    channels = config.get_config('channels')
    sampling_rate = config.get_config('sampling_rate')
    # Need to create root node, if merge_channels not enabled do a loop. Creating a hierarchy for each channel.

    # Create multiple first contact peer trees.
    channel_count = 1 if config.get_config('merge_channels') else channels
    for channel_id in range(channel_count):
        channel_peers = [] # The root coordinator will sometimes need to communicate analysis of multiple channels.
        freq_list = []
        spectrum_list = []
        spectrogram_list = []
        prediction_list = []

        #--- LEAF NODES (WORKERS) - Any endpoints must be created first in order be attached to their peer at creation. --#
        if tasks['beat']:
            # TODO: CREATE NECESSARY beat detection workers/coordinators here. (Coordinator creation shouldn't probably be here.)
            #channel_peers.append(new_coordinator('BPM', {'config': config, 'peer_list': [], 'channel_id': channel_id}))
            pass # Had to disable for time being due to infinite while loop.

        if tasks['pitch']:
            algorithm = config.get_config('pitch_algorithm')
            if algorithm == 'hps':
                spectrum_list.append(new_worker('HPS', {'sampling_rate' : sampling_rate, 'channel_id': channel_id}))
            elif algorithm == 'zero-crossings':
                freq_list.append(new_worker('ZeroCrossing', {'sampling_rate' : sampling_rate, 'channel_id': channel_id}))
            elif algorithm == 'fft':
                spectrum_list.append(new_worker('FFT', {'sampling_rate' : sampling_rate, 'channel_id': channel_id}))
            else:
                freq_list.append(new_worker('AutoCorrelation', {'sampling_rate' : sampling_rate, 'channel_id': channel_id}))

        if tasks['genre']:
            prediction_list.append(new_worker('GenrePredictor', {'sampling_rate' : sampling_rate, 'channel_id': channel_id}))

        if tasks['bands']:
            bands_of_interest = config.get_config('bands')
            spectrum_list.append(new_worker('Bands', {'bands_of_interest' : bands_of_interest, 'sampling_rate' : sampling_rate, 'channel_id': channel_id}))


        #--- Root Nodes (Coordinators) - Created last in order so that peers can be injected. ---#
        # This simply avoids creation of u
        if len(prediction_list) > 0:
            channel_peers.append(new_coordinator('FFTS', {'config': config, 'peer_list': spectrogram_list, 'channel_id': channel_id}))
            spectrogram_list.append(new_coordinator('Spectrogram', {'config': config, 'peer_list': prediction_list, 'channel_id': channel_id, 'sampling_rate': sampling_rate}))

        if len(spectrum_list) > 0:
            freq_list.append(new_coordinator('Spectrum', {'config': config, 'peer_list': spectrum_list, 'channel_id': channel_id}))

        if len(freq_list) > 0:
            channel_peers.append(new_coordinator('Frequency', {'config': config, 'peer_list': freq_list, 'channel_id': channel_id}))

        if len(channel_peers) > 0:
            root_peers.append(channel_peers)

    if len(root_peers) > 0:
        return new_coordinator('Root', {'config': config, 'peer_list': root_peers})
    else:
        raise ValueError("No tasks have been configured to run. Please enable at least one analysis task in your configuration.")

COORDINATORS = {subclass.__name__ : subclass for subclass in Coordinator.__subclasses__()}
WORKERS = {subclass.__name__ : subclass for subclass in Worker.__subclasses__()}

def new(subs, type, kwargs):
    if type in subs:
        return subs[type](**kwargs)
    else:
        raise ValueError("Class not found.")

def new_worker(type, kwargs):
    type = '{}Worker'.format(type)
    return new(WORKERS, type, kwargs)

def new_coordinator(type, kwargs):
    type = '{}Coordinator'.format(type)
    return new(COORDINATORS, type, kwargs)