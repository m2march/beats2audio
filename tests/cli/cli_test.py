import pytest
import pydub
import os
import filetype
import m2.beats2audio
import m2.rec2taps
import numpy as np
from scipy.io import wavfile
from m2.beats2audio.cli import main, FORMAT_OPTIONS
from m2.beats2audio.cli import ACCEPTABLE_MP3_SAMPLE_RATES
from m2.beats2audio import defaults
from m2.beats2audio import CLICK_FILE, CLICK_MAX_DELAY

click_times = np.array([1000, 1500, 1750, 3000])

IN_FILE_NAME = 'click_times.txt'

## Test list:
# * default params
# * -r param (wav)
# * valid -r param (mp3)
# * invalid -r param (mp3)
# * -o param
# * -f param
# * -c param
# * -d param
# * format from -o
# * format conflict -f, -o
# * --as-seconds
# * produced times (at both formats)


@pytest.fixture
def b2a_fs(fs):
    fs.add_real_file(CLICK_FILE)
    fs.create_file(IN_FILE_NAME,
                   contents='\n'.join([str(x) for x in click_times]))
    yield fs


@pytest.fixture
def b2a_tmp_path(tmp_path):
    with open(os.path.join(tmp_path, IN_FILE_NAME), 'w') as f:
        f.write('\n'.join([str(x) for x in click_times]))

    yield tmp_path


@pytest.fixture
def in_path(tmp_path):
    yield os.path.join(tmp_path, IN_FILE_NAME)


def test_default_arguments(mocker, b2a_fs):
    mocker.patch('sys.argv', ['exec', IN_FILE_NAME])
    mocker.patch('m2.beats2audio.create_beats_audio')

    main()

    expected_args = (click_times,
                     defaults.OUTPUT_FILENAME_TPL.format(defaults.FORMAT),
                     defaults.FORMAT, defaults.CLICK_GAIN, 0, defaults.SAMPLE_RATE)

    m2.beats2audio.create_beats_audio.assert_called_once()
    call_args = m2.beats2audio.create_beats_audio.call_args
    assert (call_args[0][0] == expected_args[0]).all()
    assert (call_args[0][1:] == expected_args[1:])


@pytest.mark.parametrize('sr', [2200, 22000, 44100, 48000])
def test_sr_argument_wav(mocker, b2a_fs, sr):
    mocker.patch('sys.argv', ['exec', 'click_times.txt', '-r', str(sr)])
    mocker.spy(m2.beats2audio, 'create_beats_audio')

    main()

    expected_vargs = (click_times, defaults.OUTPUT_FILENAME_TPL.format('wav'),
                      'wav', defaults.CLICK_GAIN, 0, sr)

    m2.beats2audio.create_beats_audio.assert_called_once()
    call_args = m2.beats2audio.create_beats_audio.call_args
    assert (call_args[0][0] == expected_vargs[0]).all()
    assert (call_args[0][1:] == expected_vargs[1:])

    _sr, _ = wavfile.read(expected_vargs[1])
    assert _sr == sr


@pytest.mark.parametrize('sr', ACCEPTABLE_MP3_SAMPLE_RATES)
def test_sr_argument_mp3(mocker, b2a_tmp_path, sr, in_path):
    out_file = os.path.join(b2a_tmp_path, 'out.mp3')
    mocker.patch('sys.argv', ['exec', in_path, '-r', str(sr),
                              '-f', 'mp3', '-o', out_file])
    mocker.spy(m2.beats2audio, 'create_beats_audio')

    main()

    expected_vargs = (click_times, out_file, 'mp3', defaults.CLICK_GAIN, 0, sr)

    m2.beats2audio.create_beats_audio.assert_called_once()
    call_args = m2.beats2audio.create_beats_audio.call_args
    assert (call_args[0][0] == expected_vargs[0]).all()
    assert (call_args[0][1:] == expected_vargs[1:])

    seg = pydub.AudioSegment.from_mp3(expected_vargs[1])
    assert seg.frame_rate == sr


@pytest.mark.parametrize('sr', [22000, 41000])
def test_invalid_sr_argument_mp3(mocker, b2a_fs, sr):
    mocker.patch('sys.argv', ['exec', IN_FILE_NAME, '-r', str(sr),
                              '-f', 'mp3'])
    mocker.patch('m2.beats2audio.create_beats_audio')

    with pytest.raises(SystemExit):
        main()


@pytest.mark.parametrize('_out_path', ['out1.wav', 'out2.wav'])
def test_output_argument(mocker, b2a_tmp_path, _out_path, in_path):
    out_path = os.path.join(b2a_tmp_path, _out_path)
    mocker.patch('sys.argv', ['exec', in_path, '-o', out_path])

    assert ~os.path.isfile(out_path)

    main()

    assert os.path.isfile(out_path)


@pytest.mark.parametrize('format', FORMAT_OPTIONS)
def test_format_argument(mocker, b2a_tmp_path, format, in_path):
    out_path = os.path.join(b2a_tmp_path, 'out.{}'.format(format))
    mocker.patch('sys.argv', ['exec', in_path, '-o', out_path])
    mocker.spy(m2.beats2audio, 'create_beats_audio')

    main()

    expected_args = (click_times, out_path,
                     format, defaults.CLICK_GAIN, 0,
                     defaults.SAMPLE_RATE)

    format_mime = {'mp3': 'audio/mpeg', 'wav': 'audio/x-wav'}

    m2.beats2audio.create_beats_audio.assert_called_once()
    call_args = m2.beats2audio.create_beats_audio.call_args
    assert (call_args[0][0] == expected_args[0]).all()
    assert (call_args[0][1:] == expected_args[1:])

    assert (filetype.audio(out_path).mime == format_mime[format])


def test_gain_argument(mocker, b2a_fs):
    maxes = []
    for gain in range(-2, 3):
        mocker.patch('sys.argv', ['exec', IN_FILE_NAME, '-c', str(gain)])
        main()
        sr, data = wavfile.read(defaults.OUTPUT_FILENAME_TPL.format('wav'))
        maxes.append(np.max(data))

    assert len(set(maxes)) == len(maxes)
    assert sorted(maxes) == maxes


def test_duration_argument(mocker, b2a_fs):
    mocker.patch('sys.argv', ['exec', IN_FILE_NAME, '-d', str(5000)])
    main()
    sr, data = wavfile.read(defaults.OUTPUT_FILENAME_TPL.format('wav'))
    assert data.shape[0] / sr * 1000 == 5000

    mocker.patch('sys.argv', ['exec', IN_FILE_NAME, '-d', str(2000)])
    main()
    sr, data = wavfile.read(defaults.OUTPUT_FILENAME_TPL.format('wav'))
    assert data.shape[0] / sr * 1000 != 2000


@pytest.mark.parametrize('format', FORMAT_OPTIONS)
def test_format_from_output(mocker, b2a_tmp_path, in_path, format):
    out_file = os.path.join(b2a_tmp_path, 'out.' + format)
    mocker.patch('sys.argv', ['exec', in_path, '-o', out_file])
    main()

    format_mime = {'mp3': 'audio/mpeg', 'wav': 'audio/x-wav'}
    assert (filetype.audio(out_file).mime == format_mime[format])


def test_invalid_format_output(mocker, b2a_fs):
    mocker.patch('sys.argv', ['exec', IN_FILE_NAME, '-f', 'mp3',
                              '-o', 'a.wav'])

    with pytest.raises(SystemExit):
        main()

    mocker.patch('sys.argv', ['exec', IN_FILE_NAME, '-f', 'wav',
                              '-o', 'a.mp3'])

    with pytest.raises(SystemExit):
        main()


def test_as_seconds(mocker, fs):
    fs.create_file('click_times.txt',
                   contents='\n'.join(str(x) for x in [1.5, 2, 3.025]))
    mocker.patch('sys.argv', ['exec', IN_FILE_NAME, '--as-seconds'])
    mocker.patch('m2.beats2audio.create_beats_audio')

    main()

    m2.beats2audio.create_beats_audio.assert_called_once()
    call_args = m2.beats2audio.create_beats_audio.call_args
    assert ([1500, 2000, 3025] == call_args[0][0]).all()


def test_click_times_in_audio(mocker, b2a_fs):
    mocker.patch('sys.argv', ['exec', IN_FILE_NAME])

    main()

    sr, data = wavfile.read(defaults.OUTPUT_FILENAME_TPL.format('wav'))
    onsets = m2.rec2taps.numpy_peaks(data[:, 0], sr) / sr * 1000
    assert ((onsets - (click_times + CLICK_MAX_DELAY)) < 0.1).all()
