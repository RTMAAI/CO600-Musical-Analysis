""" KEY MODULE TESTS

    - Any tests against the key analysis module methods will be contained here.
"""
import unittest
from rtmaii.analysis import key

class TestSuite(unittest.TestCase):
    """ Test Suite for the key module. """

    def setUp(self):
        """ Perform setup of initial parameters. """
        self.a4_freq = {'midi_num': 69, 'frequency': 440, 'note': 'A'}
        self.a4sharp_freq = {'midi_num': 70, 'frequency': 466.164, 'note': 'A#/Bb'}
        self.e2_freq = {'midi_num': 40, 'frequency': 82.407, 'note': 'E'}
        self.off_f5_freq = {'midi_num': 77, 'frequency': 690, 'note': 'F',
                            'actual_frequency': 698.46, 'cents_off': -15}

    def test_a4_cents_off(self):
        """ Test that given the equivalent midi number of a frequency that the cents off is 0. """
        self.assertEqual(key.get_cents_off(self.a4_freq['frequency'], self.a4_freq['midi_num']), 0)

    def test_a4_midi(self):
        """ Test that the the midi number calculated for a frequency is correct. """
        self.assertEqual(key.get_midi_num(self.a4_freq['frequency']), self.a4_freq['midi_num'])

    def test_e2_midi(self):
        """ Test that the the midi number calculated for a frequency is correct. """
        self.assertEqual(key.get_midi_num(self.e2_freq['frequency']), self.e2_freq['midi_num'])

    def test_a4sharp_midi(self):
        """ Test that the the midi number calculated for a frequency is correct. """
        self.assertEqual(key.get_midi_num(self.a4sharp_freq['frequency']),
                         self.a4sharp_freq['midi_num'])

    def test_asharp_note(self):
        """ Test that the root note and cents off for a# note is correct. """
        note = key.note_from_pitch(self.a4sharp_freq['frequency'])
        self.assertEqual(note['note'], self.a4sharp_freq['note'])
        self.assertEqual(note['cents_off'], 0)

    def test_e_note(self):
        """ Test that the root note and cents off for an e note is correct."""
        note = key.note_from_pitch(self.e2_freq['frequency'])
        self.assertEqual(note['note'], self.e2_freq['note'])
        self.assertEqual(note['cents_off'], 0)

    def test_cents_off(self):
        """ Test that cents off for a frequency under a note is correct. """
        self.assertEqual(key.get_cents_off(self.off_f5_freq['frequency'],
                                           self.off_f5_freq['midi_num']),
                         self.off_f5_freq['cents_off'])
