#! /usr/bin/env python

print "Loading modules"
#import alsabuttonrecord
#import voicetrigger
import kittaisb
import json
import os
import pymplb
import random
import re
import requests
import signal
import subprocess
import sys
import time

from amzn import *
from creds import *
from memcache import Client
from threading import Thread

print "Loading modules completed"

"""
Copyright (c) <2016> <Michael Erdahl>

credits:

Sam Machin (AlexaPi)

Permission is hereby granted, free of charge, to any person obtaining a copy of 
this software and associated documentation files (the "Software"), to deal in 
the Software without restriction, including without limitation the rights to 
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
of the Software, and to permit persons to whom the Software is furnished to do 
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE.

"""
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

debug = True
streamUrl = ""
streamPlaying = False

# ctrl-c handler
def signal_handler(signal, frame):
    print "User pressed ctrl-c, exiting\n"
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Setup
servers = ["127.0.0.1:11211"]  # memcached local server
mc = Client(servers, debug=1)
path = os.path.realpath(__file__).rstrip(os.path.basename(__file__))

'''
global mplayer instance
'''
mplayer = pymplb.MPlayer()
mplayer_avs = pymplb.MPlayer() # player just for AVS responses

def internet_on():
    print("Checking Internet Connection...")
    try:
        r = requests.get('https://api.amazon.com/auth/o2/token')
        print("Connection OK")
        return True
    except:
        print("Connection Failed")
        return False
        
def gettoken():
    token = mc.get("access_token")
    if token:
        return token
    else:
        try:
            payload = {"client_id" : Client_ID,
                       "client_secret" : Client_Secret,
                       "refresh_token" : refresh_token,
                       "grant_type" : "refresh_token", }
        except Exception, e:
            raise e # issues here arise from missing or incorrect creds

        url = "https://api.amazon.com/auth/o2/token"
        r = requests.post(url, data = payload)
        resp = json.loads(r.text)
        mc.set("access_token", resp['access_token'], 3570)
        return resp['access_token']

def alexa(recording):
    url = 'https://access-alexa-na.amazon.com/v1/avs/speechrecognizer/recognize'
    headers = {'Authorization' : 'Bearer %s' % gettoken()}

    with open(recording) as inf:
        files = [
                ('file', ('request', json.dumps(avsRequestHeader), 'application/json; charset=UTF-8')),
                ('file', ('audio', inf, 'audio/L16; rate=16000; channels=1'))
                ]   
        r = requests.post(url, headers=headers, files=files)
    
    if r:
        process_response(r)
    else:
        raise RuntimeException("Fatal - did not receive response from AVS")
     
def process_response(r):   
    if r.status_code == 200:

        '''
        Flow needs to be completely reworked.

        Must parse each directive, then work through each task.

        AVS responses should be played back before streaming URLs
        '''

        for v in r.headers['content-type'].split(";"):
            if re.match('.*boundary.*', v):
                boundary =  v.split("=")[1]
        data = r.content.split(boundary)
        
        ''' think this will tell us if there is a streaming audio payload '''
        n = re.search('(?=audio\/mpeg)(.*?)(?=\r\n)', r.content)
        
        r.connection.close()
        
        for d in data:
            ''' determine the payload type of each data chunk and process '''
            m = re.search('(?<=Content\-Type: )(.*?)(?=\r\n)', d)
            if m:
                c_type = m.group(0)
                if c_type == 'application/json':
                    process_json_resp(d.split('\r\n\r\n')[1].rstrip('\r\n--'))
                elif c_type == 'audio/mpeg':
                    ''' voice response from AVS in mp3 format '''
                    raw_mp3 = d.split('\r\n\r\n')[1].rstrip('--')
                    play_response(raw_mp3)
                    if len(streamUrl) and streamPlaying is False:
                        '''
                        Telling an existing stream to play again will cause an
                        audible glitch
                        '''
                        play_stream_url(streamUrl)
                else:
                    print "Unsupported content type: %s" % c_type
    
    else:
        print "Server sent unexpected status code -", r.status_code

'''
these JSON functions should be replaced with Python's native JSON abilities, if
possible
'''
def process_json_resp(json_r):
    resp = json.loads(json_r)

    # empty directives received when you say "stop"
    if not resp['messageBody']['directives']:
        stop_active_stream(clear_url=True)
        return

    '''
    This is very messy - there has to be a better way without jumping
    straight to looking for presence of payload tokens
    '''
    for d in resp['messageBody']['directives']:
        if 'Speaker' in d['namespace']:
            if 'SetVolume' in d['name']:
                if 'volume' in d['payload']:
                    v = d['payload']['volume']
                    mode = d['payload']['adjustmentType']
                    mp_adjust_volume(mode, float(v))

    if debug:
        print "***************** Begin Debug ***************"
        print("{}JSON String Returned:{} {}".format(bcolors.OKBLUE,
            bcolors.ENDC, json.dumps(json.loads(json_r), indent=2)))
        print "***************** End Debug ***************"
    
    ''' do we have a streaming media url in the response '''
    if "streamUrl" in json_r:
        global streamUrl
        streamUrl = json_string_value(json_r, "streamUrl")

def json_string_value(json_r, item):
    m = re.search('(?<={}":")(.*?)(?=")'.format(item), json_r)
    if m:
        if debug: print("{}{}:{} {}".format(bcolors.OKBLUE, item, bcolors.ENDC, m.group(0)))
        return m.group(0)
    else:
        return ""
        
def json_integer_value(json_r, item):
    m = re.search('(?<={}":)(-?[0-9]+)'.format(item), json_r)
    if m:
        if debug: print("{}{}:{} {}".format(bcolors.OKBLUE, item, bcolors.ENDC, m.group(0)))
        return int(m.group(0))
    else:
        return ""

def mp_adjust_volume(mode="relative", nv=-10.0):
    '''
    supported volume adjustment modes:
    relative : adjust in positive or negative increments
    absolute : set volume absolute value (0 - 100)
               (tell Alexa volume 0-10 however)

    Unfortunately with adding another mplayer dedicated to AVS responses,
    things just got a bit more complicated, and now will be forced to make
    volume changes at the ALSA layer, where they should have been done in
    the first place.  This is TODO
    '''

    cv = mplayer.p_volume
    if cv is not None:
        if 'relative' in mode:
            mplayer.p_volume += nv
        elif 'absolute' in mode:
            mplayer.p_volume = nv
        else:
            print "Unsupported volume adjustment mode: ", mode

    if debug: print "New volume: ", mplayer.p_volume

def play_response(raw_mp3):
    '''
    play the speech response from AVS - will block in this function until the
    response has completed playing
    '''
    with open(path + "response.mp3", 'wb') as f:
        f.write(raw_mp3)

    '''
    With some dmix magic in /etc/asound.conf, we are able to play
    the AVS response over the top of a currently playin stream
    https://discuss.mopidy.com/t/setting-up-c-media-usb-headphone-set-in-mixer-mode/1409/3
    '''
    wasStreaming = False
    if streamPlaying is True:
        # stop_active_stream()
        previous_volume = mplayer.p_volume
        mp_adjust_volume("absolute", 5.0)
        wasStreaming = True

    mplayer_avs.loadfile("response.mp3")

    '''
    Wait for response to be completed before returning
    
    playback percent_pos seems to go from 99 to None
    Checking for None right away does not seem to work well - stream may
    not have started yet or may need to prime percent_pos with an initial read
    '''
    while (mplayer_avs.p_percent_pos < 100.0 and
            mplayer_avs.p_percent_pos != None):
        time.sleep(.1)

    '''
    making the assumption we want to resume the stream after asking a question
    but this can be a tricky assumption - need to see what types of meta data
    AVS gives back for different types of requets, and also how a real Echo
    responds

    Today Echo will continue playing a streaming audio while a simple query
    reponse plays back.  If however you ask for a skill, not sure how it 
    responds in that case - it also probably depends (i.e., you might
        want to keep the music playing if you dim the lights, but maybe not
        if you read a wikipedia entry, etc)
    '''
    if wasStreaming is True:
        # resume_stream_url()
        mp_adjust_volume("absolute", previous_volume)

def stop_active_stream(clear_url=False):
    global streamPlaying 
    streamPlaying = False
    mplayer.stop()

    if clear_url is True:
        global streamUrl
        streamUrl = ""
    time.sleep(.1)

def play_stream_url(url, streaming=True, player=mplayer):
    '''
    play_stream_url supports URL and local filesystem paths as input
    url - local or remote audio stream to play (supports mp3, http audio)
    streaming - True for streaming audio links, False for local mp3 files
    player - handle to player for request
    '''
    global streamPlaying
    if streamPlaying:
        stop_active_stream()

    player.loadfile(url)

    if streaming is True:    
        streamPlaying = True

    print "**** Stream playing set to True***"

def resume_stream_url():
    play_stream_url(streamUrl)


	

if __name__ == '__main__':
    if internet_on() == False:
        print("Could not connect to Amazon servers - aborting")
        exit(1)

    token = gettoken()

    ''' say hello! '''
    play_stream_url('./hello.mp3', streaming=False, player=mplayer_avs)

    recording = None
    if len(sys.argv) == 2:
        recording = sys.argv[1]
        print "Using recording", recording
        alexa(recording)

    else:
        while(1):
            recording = path+'recording.wav'
            kittaisb.snowboy_start()
            kittaisb.record(recording)
            #voicetrigger.voice_trigger_record(recording)
            #alsabuttonrecord.record(recording)

            alexa(recording)
