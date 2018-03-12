from math import log

note_strings = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]

def note_from_pitch(frequency):
    """
        12 Possible notes * (Natural log)
        Fn = F0 * (a)**n
    """
    estimated_num = note(frequency)
    offset = cents_off(frequency, estimated_num)
    note_index = int(estimated_num % 12)
    return {'key': note_strings[note_index], 'cents_off': offset}

def note(frequency):
    note_num = frequency if frequency == 0 else 12 * (log(frequency / 440)/log(2))
    note_index = round(note_num) + 69
    return note_index

def cents_off(frequency, note_index):
    """
        Get how far off the estimated key the note was.
    """
    frequency_of_note = 440 * (2 ** ((note_index - 69) / 12))
    cents_off = int(1200 * log(frequency / frequency_of_note, 2))
    return cents_off