#!/usr/bin/python

import os
import sys
import time
import getopt
import alsaaudio
import struct

# Audio setup constants
alsa_card = 'plughw:CARD=Device'
channels = 1
rate = 16000
period_size = 1000
format = alsaaudio.PCM_FORMAT_S16_LE

def record(recording_file):    
    # Keypress setup  - event1 is AM335x GP EVM matrix keypad
    #                   use 'evtest' to determine mapping on other systems
    infile_path = "/dev/input/event1"  

    FORMAT = "llHHI"
    EVENT_SIZE = struct.calcsize(FORMAT)

    in_file = open(infile_path, "rb")
    keypressed = False
    recording = False
     
    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NORMAL, alsa_card)
    
    # Set attributes: Mono, 16000 Hz, 16 bit little endian samples
    inp.setchannels(channels)                                                      
    inp.setrate(rate)                                                      
    inp.setperiodsize(period_size)                                                  
    inp.setformat(format)
    
	# Blocking call until key is pressed
    print "Waiting to Record..."
    event = in_file.read(EVENT_SIZE)
    keypressed = True

    while keypressed:
        (tv_sec, tv_usec, type, code, value) = struct.unpack(FORMAT, event)
      
        if type == 1 and value == 1 and recording == False:
            print "Recording"
            recording = True        
            f = open(recording_file, 'wb')

        if recording == True and type == 1 and value == 0:
            f.flush()
            f.close()                                                         
            in_file.close()                                                   
            inp.close()
            keypressed = False                                             
            recording = False
            return
        
        if keypressed and recording:
            # Recording
            l, data = inp.read()
            if l:
                f.write(data)
                time.sleep(.001)

        event = in_file.read(EVENT_SIZE)


if __name__ == '__main__':
    record("recording.wav")
    
    print "Finished recording"                                        
    
    print "To test recording, execute:\n\naplay -r {} -c {} -f {} {}\n".format(
        rate, channels, "S16_LE", "recording.wav")
