'''
Library to create audio from onset lists.
'''
import magic
import os
import tempfile
import pkg_resources
import subprocess

import numpy as np

from pydub import AudioSegment
from subprocess import call
from scipy.io import wavfile


CLICK_FILE = pkg_resources.resource_filename(__name__, 'click.wav')
CLICK_MAX_DELAY = 1.72
SEP_FILE = pkg_resources.resource_filename(__name__, 'separator.mp3')

ACCEPTABLE_MP3_SAMPLE_RATES = [22050, 44100, 48000]

CLICK_OFFSET = 0

# Main beats2track functions

def create_beats_track(beats, click_gain_delta=0, min_duration=0):
    """
    Creates an AudioSegment with clicks in beats positions.

    Params:
        beats: moment of click sounds in milliseconds
        click_gain_delta: gain to apply to click sound in dB
        min_duration: minimun duration of the audio. If beats end sounding 
            before min_duration, the audio is filled with silence until the
            duration is reached

    Returns:
        pydub.AudioSegment with identical click sounds in each time defined in 
        `beats` during at least `min_duration`.
    """
    click = AudioSegment.from_mp3(CLICK_FILE)
    click = click + click_gain_delta
    duration = beats[-1] + len(click)
    duration = max(min_duration, duration)
    silence = AudioSegment.silent(duration=duration)
    for beat in beats:
        silence = silence.overlay(
            click, position=beat - CLICK_OFFSET)

    return silence


def create_beats_audio(beats, output_filename, format,
                       click_gain_delta=0, min_duration=0,
                       sample_rate=48000):
    """
    Creates an audio file with click positions at `beats`.

    Params:
        beats: position of clicks in milliseconds
        output_filename: name of the output file
        format: audio format of the output file (e.g.: "mp3", "wav")
        click_gain_delta: gain to apply to click sound in dB
        min_duration: minimun duration of the audio. 
        sample_rate: sample rate used in the output file

    Returns:
        None, file is created as a side effect
    """
    seg = create_beats_track(beats, click_gain_delta, min_duration)
    seg.set_frame_rate(sample_rate).export(output_filename, format=format)


def create_beats_mp3(beats, output_filename, click_gain_delta=0,
                     min_duration=0, sample_rate=48000):
    """
    Creates mp3 file with click position at `beats`.

    See `create_beats_audio` for more detail.
    """
    create_beats_audio(beats, output_filename, 'mp3',
                       click_gain_delta, min_duration,
                       sample_rate)


def create_beats_wav(beats, output_filename, click_gain_delta=0,
                     min_duration=0, sample_rate=48000):
    """
    Creates wav file with click position at `beats`.

    See `create_beats_audio` for more detail.
    """
    create_beats_audio(beats, output_filename, 'wav',
                       click_gain_delta, min_duration,
                       sample_rate)


# Other functionalities

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
    '''
    Open an audio file and returns an pydub.AudioSegment.

    Supports standard audio files and also midis.
    '''

    def __init__(self, audio_file):
        self.audio_file = os.path.realpath(audio_file)

    def __enter__(self):
        if magic.from_file(self.audio_file, mime=True) == 'audio/midi':
            import m2.midi as midi
            print('Midi found. Converting to wav.')
            with tempfile.NamedTemporaryFile('rw') as temp:
                print(temp.name)
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
        import m2.midi as midi
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
        print(e, CLICK_FILE)
        exit()

    base_audio = base_audio + audio_gain_delta
    click = click + click_gain_delta

    audio_with_click = base_audio
    for beat in beats:
        audio_with_click = audio_with_click.overlay(
            click, position=beat - CLICK_OFFSET)
    return audio_with_click




def join_tracks_w_sep(ts,
                      left_padding=0, right_padding=400, dur=2000):
    '''
    Joins tracks with a separator.

    Asumes all segments have same channel count and frame rate.

    Args:
        ta: list of AudioSegment to join
        left_padding: ms of silence between ta and the separator
        right_padding: ms of silence between the separator and tb
        dur: duration in ms of the separator tone

    Returns: joined audio segment
    '''
    # First we create the separator segment
    final_sep = separator_segment(left_padding, right_padding, dur)

    # We temporarily write the separator and all segments
    sep_fn = tempfile.mkstemp(prefix='sep_', suffix='.wav')[1]
    final_sep.export(sep_fn, 'wav')

    def save_segment(i, s):
        fn = tempfile.mkstemp(prefix='seg_', suffix='.wav')[1]
        s.export(fn, 'wav')
        return fn

    segment_fns = [save_segment(i, s) for i, s in enumerate(ts)]

    output_fn = tempfile.mkstemp(prefix='out_', suffix='.wav')[1]

    # Joining with ffmpeg
    list_file = tempfile.mkstemp(suffix='.list')[1]
    with open(list_file, 'w') as f:
        fmt = 'file {}\n'
        f.write(fmt.format(segment_fns[0]))
        for fn in segment_fns[1:]:
            f.write(fmt.format(sep_fn))
            f.write(fmt.format(fn))

    concatenate_cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0']
    concatenate_cmd.extend(['-i', list_file])
    concatenate_cmd.extend(['-c', 'copy', output_fn])

    subprocess.Popen(concatenate_cmd).communicate()

    ret_seg = AudioSegment.from_file(output_fn)

    # Cleanup
    os.remove(sep_fn)
    os.remove(output_fn)
    for fn in segment_fns:
        os.remove(fn)

    return ret_seg


def separator_segment(left_padding=1000, right_padding=1000, dur=1000):
    # First we create the separator segment
    separator_tone = separator_sound_segment(dur)

    left_pad = AudioSegment.silent(left_padding)
    right_pad = AudioSegment.silent(right_padding)
    final_sep = left_pad + separator_tone + right_pad
    return final_sep


def create_separator_sound(dur, f=354.0,
                           noise_sigma=0.1, sr=48000, channels=2,
                           volume=0.1, fn=None):
    '''
    Creates a tone of frequency _f_ with gaussian noise of _dur_ ms.

    Returns a (sr * dur, channels) numpy array
    '''
    fd = (volume * np.sin(2 * np.pi *
                np.arange(int(sr * dur / 1000.0)) * f/sr)).astype(np.float32)

    if noise_sigma and noise_sigma != 0.0:
        noise = np.random.normal(0, volume * noise_sigma, fd.size)
        fd = fd + noise

    fd = (np.zeros((channels, 1)) + fd).astype(np.float32)

    return fd.T


def separator_sound_segment(dur, f=354.0,
                            noise_sigma=0.05, sr=48000,
                            channels=2, volume=0.1):
    a = create_separator_sound(dur, f, noise_sigma, sr, channels, volume=volume)
    with tempfile.NamedTemporaryFile() as f:
        wavfile.write(f.name, sr, a)
        seg = AudioSegment.from_file(f.name)
    return seg


# Low level functions

def segment_to_np_array(s):
    na = np.array(s.get_array_of_samples())
    return na.reshape((s.frame_count(), s.channels))
