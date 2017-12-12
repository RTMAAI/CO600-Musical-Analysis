from numpy import log

note_strings = ["C", "C#/Db", "D", "D#/Eb", "E", "F", "F#/Gb", "G", "G#/Ab", "A", "A#/Bb", "B"]

def note_from_pitch(frequency):
    """
        12 Possible notes * (Natural log)
    """
    note_num = 12 * (log(frequency / 440)/log(2))
    note_index = int(round(note_num)+69)%12
    return note_strings[note_index]
