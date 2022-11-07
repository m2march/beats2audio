# Beats2Audio

`beats2audio` is an utility to create audio files with clicks at designated 
onset times as provided in a configuration file. Onset times are specified in
a text file defining one location per line, in milliseconds. This utility was
developed in the context of the publication _"A simple and cheap setup for timing tapping responses synchronized to auditory stimuli."_ (Miguel, M.A., Riera, P. & Slezak, D.F.  Behav Res (2021). https://doi.org/10.3758/s13428-021-01653-y). 


## Installation

### Non-pip Requirements

* conda install pyaudio

### Instructions

* From pypi:

```
    pip install m2-beats2audio
```

* From sources:

```
    git clone https://github.com/m2march/beats2audio.git
    cd beats2audio
    python setup.py install
```


## Usage

Given a input file as the following, specifying onsets at 500 ms intervals
(see `examples/iso_500.txt`):

    0
    500
    1000
    1500
    2000
    2500

`beats2audio` takes as a positional parameter the onset times file and
specifies an output file with the `-o` flag. I.e.:

    `beats2audio -o 500.wav examples/iso_500.txt`

The utility can produce `wav` and `mp3` files, according to the extension of
the output file or via the `-f` flag. More options are explained in the help
text `-h`.
