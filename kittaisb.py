#!/usr/bin/python

import alsaaudio
import snowboydecoder
import time
import webrtcvad
import signal

debug = True

# Set silence detection agressiveness to maximum
vad = webrtcvad.Vad(3)

# constants 
alsa_card = 'plughw:CARD=Device'
VAD_SAMPLERATE = 16000
VAD_CHANNELS = 1
VAD_FRAME_MS = 30
VAD_PERIOD = (VAD_SAMPLERATE / 1000) * VAD_FRAME_MS
VAD_SILENCE_TIMEOUT = 1000
VAD_THROWAWAY_FRAMES = 10
MAX_RECORDING_LENGTH = 4
MAX_VOLUME = 100
MIN_VOLUME = 20

speech_filename="recording.wav"

triggered = False

def snowboy_trigger_callback():
    global triggered
    snowboydecoder.play_audio_file()
    triggered = True

def snowboy_interrupt_check():
    global triggered
    return triggered

def snowboy_start():
    detector = snowboydecoder.HotwordDetector("./resources/HeyBuddy.pmdl",
            sensitivity=0.5, audio_gain=1)
    
    '''
    snowboy_trigger_callback will be called when the trigger phrase is detected
    snowboy_interrupt_check will be called every (sleep_time) seconds to
    determine if start() should exit (will loop forever without this fcn)
    sleep_time interval to call interrupt check, while not in triggering loop
    '''
    if debug: print "Snowboy detector starting"
    detector.start(snowboy_trigger_callback, snowboy_interrupt_check, sleep_time=0.03)

    global triggered
    triggered = False

    detector.terminate()

    if debug: print "Snowboy detector finished"

def record(filename, throwaway_frames=VAD_THROWAWAY_FRAMES, timeout=MAX_RECORDING_LENGTH):
    '''
    Begin recording once speech is detected, then stop recording when silence
    is detected.
    '''
    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, alsa_card)
    inp.setchannels(VAD_CHANNELS)
    inp.setrate(VAD_SAMPLERATE)
    inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)
    inp.setperiodsize(VAD_PERIOD)
    audio = ""

    # Buffer as long as we haven't heard enough silence or the total size is within max size
    thresholdSilenceMet = False
    detectedSpeech = False
    frames = 0
    numSilenceRuns = 0
    silenceRun = 0
    start = time.time()
    lastSilenceThresholdMet = 0.0

    # do not count first 10 frames when doing VAD
    while (frames < throwaway_frames): # VAD_THROWAWAY_FRAMES):
        l, data = inp.read()
        frames = frames + 1
        if l:
            isSpeech = vad.is_speech(data, VAD_SAMPLERATE)
            if isSpeech is True:
                audio += data
    
    if debug: print "Recording speech"

    # now do VAD
    while (thresholdSilenceMet == False) and ((time.time() - start) < timeout):
        l, data = inp.read()
        if l:
            if (l == VAD_PERIOD):
                isSpeech = vad.is_speech(data, VAD_SAMPLERATE)

                if (isSpeech == False):
                    silenceRun = silenceRun + 1
                else:
                    audio += data
                    detectedSpeech = True
                    silenceRun = 0
                    numSilenceRuns = numSilenceRuns + 1

        # only count silence runs after the first one 
        # (allow user to speak for total of max recording length if they haven't said anything yet)
        if (numSilenceRuns != 0) and ((silenceRun * VAD_FRAME_MS) > VAD_SILENCE_TIMEOUT):
            thresholdSilenceMet = True
            lastSilenceThresholdMet = time.time() - start
    
    if debug:
        elapsed = time.time() - start
        print "Recording length:", elapsed
        print "Last silence threshold met:", lastSilenceThresholdMet
        print "numSilenceRuns:", numSilenceRuns
        print "Detected speech:", detectedSpeech

    rf = open(filename, 'w')
    rf.write(audio)
    rf.close()
    inp.close()

    if debug: print "Finished recording"
        
if __name__ == "__main__":
    snowboy_start()
    record("recording.wav")

    print "To test recording, execute:\n\naplay -r {} -c {} -f {} {}\n".format(
            VAD_SAMPLERATE, VAD_CHANNELS, "S16_LE", speech_filename)

