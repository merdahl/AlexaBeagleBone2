#! /usr/bin/env python

import os
import signal
import random
import time
import alsaaudio
import requests
import json
import re
import sys
import datetime

import webrtcvad

from pocketsphinx import get_model_path
from pocketsphinx.pocketsphinx import *
from sphinxbase.sphinxbase import *

debug = True

# PocketSphinx configuration
ps_config = Decoder.default_config()

# Set recognition model to US
ps_config.set_string('-hmm', os.path.join(get_model_path(), 'en-us'))
ps_config.set_string('-dict', os.path.join(get_model_path(), 'cmudict-en-us.dict'))

#Specify recognition key phrase
ps_config.set_string('-keyphrase', 'pal')
ps_config.set_float('-kws_threshold',1e-5)

# Hide the VERY verbose logging information
ps_config.set_string('-logfn', '/dev/null')

# Process audio chunk by chunk. On keyword detected perform action and restart search
decoder = Decoder(ps_config)

#Variables
p = None
nav_token = ""
streamurl = ""
streamid = ""
position = 0
audioplaying = False
currVolume = 100
vad = webrtcvad.Vad(2)

# constants 
alsa_card = 'plughw:CARD=Device'
VAD_SAMPLERATE = 16000
VAD_FRAME_MS = 30
VAD_PERIOD = (VAD_SAMPLERATE / 1000) * VAD_FRAME_MS
VAD_SILENCE_TIMEOUT = 1000
VAD_THROWAWAY_FRAMES = 10
MAX_RECORDING_LENGTH = 8 
MAX_VOLUME = 100
MIN_VOLUME = 30

def silence_listener(throwaway_frames, filename="./recording.wav"):
    # Reenable reading microphone raw data
    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, alsa_card)
    inp.setchannels(1)
    inp.setrate(VAD_SAMPLERATE)
    inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    inp.setperiodsize(VAD_PERIOD)
    audio = ""


    # Buffer as long as we haven't heard enough silence or the total size is within max size
    thresholdSilenceMet = False
    frames = 0
    numSilenceRuns = 0
    silenceRun = 0
    start = time.time()

    # do not count first 10 frames when doing VAD
    while (frames < throwaway_frames): # VAD_THROWAWAY_FRAMES):
        l, data = inp.read()
        frames = frames + 1
        if l:
            audio += data
            isSpeech = vad.is_speech(data, VAD_SAMPLERATE)

    # now do VAD
    while (thresholdSilenceMet == False) and ((time.time() - start) < MAX_RECORDING_LENGTH):
        l, data = inp.read()
        if l:
            audio += data

            if (l == VAD_PERIOD):
                isSpeech = vad.is_speech(data, VAD_SAMPLERATE)

                if (isSpeech == False):
                    silenceRun = silenceRun + 1
                    #print "0"
                else:
                    silenceRun = 0
                    numSilenceRuns = numSilenceRuns + 1
                    #print "1"

        # only count silence runs after the first one 
        # (allow user to speak for total of max recording length if they haven't said anything yet)
        if (numSilenceRuns != 0) and ((silenceRun * VAD_FRAME_MS) > VAD_SILENCE_TIMEOUT):
            thresholdSilenceMet = True

    if debug: print ("Debug: End recording")

    rf = open(filename, 'w')
    rf.write(audio)
    rf.close()
    inp.close()
    return
        

def voice_trigger_record(filename="./recording.wav"):
    decoder.start_utt()

    if debug: print "Listening for trigger word"

    record_audio = False
    
    # Enable reading microphone raw data
    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, alsa_card)
    inp.setchannels(1)
    inp.setrate(16000)
    inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    inp.setperiodsize(1024)
    audio = ""

    while not record_audio:

        time.sleep(.1)

        triggered = False
        # Process microphone audio via PocketSphinx, listening for trigger word
        while not triggered:
            # Read from microphone
            l,buf = inp.read()
            # Detect if keyword/trigger word was said
            decoder.process_raw(buf, False, False)

            triggered_by_voice = decoder.hyp() is not None

            triggered = triggered_by_voice

        record_audio = True

        if triggered_by_voice:
            if debug: print "Got trigger!"

    # To avoid overflows close the microphone connection
    inp.close()

    if debug: print "Starting to listen..."
    silence_listener(VAD_THROWAWAY_FRAMES, filename)
    
    decoder.end_utt()
    

def loop():
    while True:
        voice_trigger_record()


def setup():
    for sig in (signal.SIGABRT, signal.SIGILL, signal.SIGINT, signal.SIGSEGV, signal.SIGTERM):
        signal.signal(sig, cleanup)

def cleanup(signal, frame):
    sys.exit(0)

if __name__ == "__main__":
    setup()
    loop()

