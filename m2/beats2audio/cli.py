import argparse
import sys
import os
import numpy as np
import m2.beats2audio
from m2.beats2audio import create_beats_audio
from m2.beats2audio import defaults, ACCEPTABLE_MP3_SAMPLE_RATES

FORMAT_OPTIONS = ['wav', 'mp3']


def main():
    parser = argparse.ArgumentParser(
        description=('Produce an audio file with click sounds at determined '
                     'positions. This utility is developed to generate '
                     'stimuli in the context of '
                     '"Simple and cheap setup for measuring timed responses '
                     'to auditory stimuli" (Miguel et. al. 2020).')
    )
    parser.add_argument('clicks', type=argparse.FileType('r'),
                        help=('Input file with click locations. Locations '
                              'are expected in milliseconds (unless '
                              '--as-seconds flag is used)'))
    parser.add_argument('-o', dest='output_file', type=str,
                        help=('Path to output audio'),
                        default=None)
    parser.add_argument('-c', '--click_gain', dest='click_gain', type=float,
                        help=('Gain in dB to add to the click sound.'),
                        default=defaults.CLICK_GAIN)
    parser.add_argument('-r', '--sample_rate', type=int, dest='sr',
                        help=('Sample rate to use in output audio.'),
                        default=defaults.SAMPLE_RATE)
    parser.add_argument('-d', '--min-duration', type=int, dest='min_duration',
                        help=('Minimun duration of the output audio. If the '
                              'last click ends before the minimun duration, '
                              'the audio is filled with silence until the '
                              'duration is reached.'),
                        default=0)
    parser.add_argument('-f', '--format', choices=FORMAT_OPTIONS, type=str,
                        dest='format',
                        help=('Format of the output file.'),
                        default=None)
    parser.add_argument('--as-seconds', action='store_true', dest='as_seconds',
                        help=('Click times in input file is given in seconds'),
                        default=False)

    args = parser.parse_args()

    if args.output_file is not None and os.path.exists(args.output_file):
        print('File already exists {}'.format(args.output_file))
        sys.exit()

    click_times = np.array([float(x) for x in args.clicks])

    if (args.as_seconds):
        click_times = click_times * 1000

    if (args.format is not None):
        if (args.output_file is not None):
            out_file_format = os.path.splitext(args.output_file)[1].lstrip('.')
            if (args.format != out_file_format):
                print('Output file name extension does not match provided '
                      'format ({} != {})'.format(out_file_format, args.format))
                sys.exit()
            format = args.format
        else:
            format = args.format
    else:
        if (args.output_file is not None):
            format = os.path.splitext(args.output_file)[1].lstrip('.')
        else:
            format = defaults.FORMAT

    output_file = (args.output_file 
                   if args.output_file is not None 
                   else defaults.OUTPUT_FILENAME_TPL.format(format))

    if (format == 'mp3') and (args.sr not in ACCEPTABLE_MP3_SAMPLE_RATES):
        print('Specified sample rate ({}) for mp3 format is not acceptable. '
              'Accepted sample rates are: {}'.format(
                  args.sr, ACCEPTABLE_MP3_SAMPLE_RATES))
        sys.exit()

    m2.beats2audio.create_beats_audio(
        click_times, output_file, format,
        args.click_gain, args.min_duration, args.sr)
