'''
Library to create audio from onset lists.
'''
import magic
import os
import tempfile
import pkg_resources

import m2.midi as midi
import numpy as np

from pydub import AudioSegment
from subprocess import call


CLICK_FILE = pkg_resources.resource_filename(__name__, 'click.mp3')

CLICK_OFFSET = 0


def beats_lines_to_beats(beats_lines):
    '''
    Reads .beats file lines back to python form

    Returns:
        :: [ms]
    '''
    def _beat_line_to_beat(l):
        return float(l.split(' ', 1)[0])
    return [_beat_line_to_beat(l) for l in beats_lines]


class open_audio:
    '''Open an audio file and returns an pydub.AudioSegment.

    Supports standard audio files and also midis.
    '''

    def __init__(self, audio_file):
        self.audio_file = os.path.realpath(audio_file)

    def __enter__(self):
        if magic.from_file(self.audio_file, mime=True) == 'audio/midi':
            print 'Midi found. Converting to wav.'
            with tempfile.NamedTemporaryFile('rw') as temp:
                print temp.name
                call(['timidity', '-Ow', '-o',
                      temp.name, self.audio_file])
                self.is_midi = True
                return AudioSegment.from_file(temp.name)
        else:
            self.is_midi = False
            return AudioSegment.from_file(self.audio_file)

    def __exit__(self, type, value, traceback):
        return not isinstance(value, Exception)


def adjust_beats_if_midi(audio_file, beats):
    audio_file = os.path.realpath(audio_file)
    if magic.from_file(audio_file, mime=True) == 'audio/midi':
        onsets = midi.midi_to_collapsed_onset_times(audio_file)
        beats = np.array(beats)
        return beats - onsets[0]
    else:
        return beats


def create_audio_with_beats(base_audio, beats,
                            click_gain_delta=0,
                            audio_gain_delta=0,
                            split_beats=False):
    try:
        click = AudioSegment.from_mp3(CLICK_FILE)
    except Exception as e:
        print e, CLICK_FILE
        exit()

    base_audio = base_audio + audio_gain_delta
    click = click + click_gain_delta

    audio_with_click = base_audio
    for beat in beats:
        audio_with_click = audio_with_click.overlay(
            click, position=beat - CLICK_OFFSET)
    return audio_with_click


def create_beats_track(beats, click_gain_delta=0):
        click = AudioSegment.from_mp3(CLICK_FILE)
        duration = beats[-1] + len(click)
        silence = AudioSegment.silent(duration=duration)
        for beat in beats:
            silence = silence.overlay(
                click, position=beat - CLICK_OFFSET)

        return silence
