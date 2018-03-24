""" KEY MODULE
    This module contains any methods relating to extracting the key/note of a frequency.

    INPUTS:
        Frequency: Frequency in Hertz to analyse.

    OUTPUTS:
        Note: Dictionary containing Note and cents off
"""
from math import log

ROOT_NOTES = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]

def note_from_pitch(frequency: float) -> dict:
    """ Returns the root note and cents off of a given frequency.

        Args:
            - frequency: Frequency (Hz) to find the root note of.
    """
    midi_num = get_midi_num(frequency)
    offset = get_cents_off(frequency, midi_num)
    note = ROOT_NOTES[midi_num % 12] # Remainder = note index position in NOTE_STRINGS.
    return {"note": note, "cents_off": offset}

def get_midi_num(frequency: float) -> float:
    """ Finds the closest midi note on a piano given a frequency in Hertz.

        Uses mathematical equations listed here: https://newt.phys.unsw.edu.au/jw/notes.html

        Args:
            - frequency: Frequency to compare against.
    """
    semitones_off_a4 = frequency if frequency == 0 else 12 * (log(frequency / 440)/log(2))
    midi_num = round(semitones_off_a4) + 69
    return midi_num

def get_cents_off(frequency: float, midi_num: float) -> float:
    """ Get how far off the estimated note the frequency is.

        Uses mathematical equations listed here: https://en.wikipedia.org/wiki/Cent_(music)

        Args:
            - frequency: Detected frequency.
            - midi_num: Midi num to compare against.
    """
    midi_note_frequency = 440 * (2 ** ((midi_num - 69) / 12))
    cents_off = round(1200 * log(frequency / midi_note_frequency))
    return cents_off
