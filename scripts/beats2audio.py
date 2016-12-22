#!/usr/bin/python
'''
* beats2audio.py : script that takes a .mid and .beats file and produces an
    audio file with the mid overlayed by a sound on each beat.
'''
import gflags
import magic
import os
import sys
import tempfile
import pkg_resources

import m2.midi as midi
import numpy as np

from pydub import AudioSegment
from subprocess import call


gflags.DEFINE_string('output_file', 'audio_with_beats.mp3',
                     'Name of the output audio file with beats.',
                     short_name='o')

gflags.DEFINE_integer('click_gain_delta', 0,
                      'Gain delta for click track (in dB).',
                      short_name='c')

gflags.DEFINE_integer('audio_gain_delta', 0,
                      'Gain delta for click track (in dB).',
                      short_name='g')

gflags.DEFINE_string('audio_file', None,
                     ('Audio file to add as a background track '
                      '(may be wav, mp3 or mid)'),
                     short_name='a')

FLAGS = gflags.FLAGS


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

    TMP_WAV_FILENAME = '.beats2audio.tmp.wav'

    def __init__(self, audio_file):
        self.audio_file = os.path.realpath(audio_file)

    def __enter__(self):
        if magic.from_file(self.audio_file, mime=True) == 'audio/midi':
            print 'Midi found. Converting to wav.'
            with tempfile.NamedTemporaryFile('rw') as temp:
                call(['timidity', '-Ow', '-o',
                      temp.name, self.audio_file])
                self.is_midi = True
                return AudioSegment.from_file(temp.name)
        else:
            self.is_midi = False
            return AudioSegment.from_file(self.audio_file)

    def __exit__(self, type, value, traceback):
        # if self.is_midi:
            # os.remove(self.TMP_WAV_FILENAME)
        return not isinstance(value, Exception)


def adjust_beats_if_midi(audio_file, beats):
    audio_file = os.path.realpath(audio_file)
    if magic.from_file(audio_file, mime=True) == 'audio/midi':
        onsets = midi.midi_to_collapsed_onset_times(audio_file)
        beats = np.array(beats)
        return beats - onsets[0]
    else:
        return beats


def create_audio_with_beats(audio_file, beats, output_file,
                            click_gain_delta=0,
                            audio_gain_delta=0,
                            split_beats=False):
    with open_audio(audio_file) as base_audio:
        try:
            click = AudioSegment.from_mp3(CLICK_FILE)
        except Exception as e:
            print e, CLICK_FILE
            exit()

        base_audio = base_audio + audio_gain_delta
        click = click + click_gain_delta

        beats = adjust_beats_if_midi(audio_file, beats)

        audio_with_click = base_audio
        for beat in beats:
            audio_with_click = audio_with_click.overlay(
                click, position=beat - CLICK_OFFSET)
        print 'Exporting to', output_file
        audio_with_click.export(output_file, format='mp3')
        return beats


def create_beats_track(beats, click_gain_delta, output_file):
        click = AudioSegment.from_mp3(CLICK_FILE)
        duration = beats[-1] + len(click)
        silence = AudioSegment.silent(duration=duration)
        for beat in beats:
            silence = silence.overlay(
                click, position=beat - CLICK_OFFSET)
        print 'Exporting beats to', output_file
        silence.export(output_file, format='mp3')


def main(beats_file, output_file='audio_with_beats.mp3', audio_file=None,
         click_gain_delta=0, audio_gain_delta=0):

    with open(beats_file, 'r') as f:
        beats = beats_lines_to_beats(f.readlines())

    if audio_file:
        beats = create_audio_with_beats(audio_file, beats, output_file,
                                        click_gain_delta, audio_gain_delta)
    else:
        create_beats_track(beats, click_gain_delta, output_file)


def __main__():
    try:
        argv = FLAGS(sys.argv)  # parse flags
        if len(argv) < 2:
            raise ValueError('No tht.beats file declared')
    except (ValueError, gflags.FlagsError), e:
        print '%s\nUsage: %s ARGS tht_beats\n%s' % (e, sys.argv[0], FLAGS)
        sys.exit(1)

    main(argv[1], FLAGS.output_file,
         audio_file=FLAGS.audio_file,
         click_gain_delta=FLAGS.click_gain_delta,
         audio_gain_delta=FLAGS.audio_gain_delta)


if __name__ == '__main__':
    __main__()
