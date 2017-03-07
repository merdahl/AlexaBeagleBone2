# Changes and improvements from AlexaBeagleBone

Dependency on VLC has been removed.  VLC is great, however on the BeagleBone
Black, it is difficult to build from source if you're on
Yocto filesystem (such as the TI Linux Processor SDK).  Mplayer is another
capable media player available on ARM Linux, consumes low CPU resources 
while streaming audio, and builds natively on TI ARM platforms running a 
recent Yocto filesystem without much fuss (probably the case with other 
platforms, but I've only worked with TI processors).

Mplayer can be put into slave mode and controlled through special files (fifo).
The pymplb wrapper by Stefan Parviainen is a clean and elegant solution for
programatically controlling Mplayer from Python.

Voice triggering is  supported using PocketSphinx and Kitt.AI Snowboy.  
The Pocket Sphinx trigger word is "Pal" - fans of the movie "Uncle Buck" might 
see the humor in using that name.  Kitt.AI is using the trained phrase
"Hey buddy" at the moment.  Other voice triggering libraries will be tested as 
well.  

CPU usage seems reasonable, even while streaming audio and performing a 
voice triggering session.  Right now it looks like about 20-30% CPU utilization
while streaming audio over WiFi, and waiting for trigger phrase, running at
600MHz.  Since the AM335x can go up to 1GHz, there is lots of headroom for
more activities!

Seamless music and AVS responses are now supported.  This scenario arrises
when a user is playing a streaming audio station, and asks AVS a question.
Instead of muting the music track to playback the AVS response, the music
volume is lowered, and we playback the AVS response at normal volume, then
restore the music volume to the previous level.  More about this below in the
ALSA confiuration section.

# Build Instructions

For now things are not terribly user friendly, and are more focused towards my
own development.  Probably the most ornerious task will be creating an AVS
credentials file.

These instructions are written using Debian 8.7, and kernel version 4.4.30
on a Beaglebone Black Wireless (out of box image on eMMC).  Yes, I did rant
above about Yocto, but for now I am starting with Debian, then will switch
over to Yocto filesystem and add instructions for building dependencies.

The following information below is a collection of my own notes, and hopefully
is complete.

## Adding Required Linux System Libraries

Begin with updating apt

    $ sudo apt-get update

Install missing headers (alsa/asoundlib.h) for pyalsaaudio.  apt-file is
a nice helper to determine which package provides a library or header file.

    $ apt-file search alsa/asoundlib.h

    (sudo apt-get install apt-file if you don't have it)

    $ sudo apt-get install libasound2-dev

Install memcached (pronunciation: mem-cash-dee) is a general-purpose distributed
memory caching system. It is often used to speed up dynamic database-driven
websites by caching data and objects in RAM to reduce the number of times an
external data source (such as a database or API) must be read.

    $ sudo apt-get install memcached

Mplayer used for basic mp3 playback

    $ sudo apt-get install mplayer

Evtest helps finding input devices associated file descriptor so we can use a
keyboard for initiating a voice recording

    $ sudo apt-get install evtest

## Adding Python Packages

Install PIP to install python package dependencies.  Using 'get-pip' script
because this will be used on Yocto builds too.

Note: must be done with root permissions, or will fail


    $ sudo python ./get-pip.py

    Collecting pip
      Downloading pip-9.0.1-py2.py3-none-any.whl (1.3MB)
        100% |████████████████████████████████| 1.3MB 107kB/s 
    Installing collected packages: pip
      Found existing installation: pip 9.0.0
        Uninstalling pip-9.0.0:
          Successfully uninstalled pip-9.0.0
    Successfully installed pip-9.0.1
    
Update PIP

    $ sudo pip install update
    Collecting update
      Downloading update-0.4.4.tar.gz
    Building wheels for collected packages: update
      Running setup.py bdist_wheel for update ... done
      Stored in directory: /root/.cache/pip/wheels/f0/35/57/6d8a5c1...
    Successfully built update
    Installing collected packages: update
    Successfully installed update-0.4.4



Install Python package wrapper dependencies
    alsaaudio
    memcached

    $ sudo pip install pyalsaaudio memcached

## Optional Voice Triggering

### KITT.AI snowboy

Snowboy is promising because we are going for a more targeted approach for
the wake word, which is fine.  We don't necessarily need an entire natural
language processing library - that's what AVS is for!

We can even define several "trigger words" to embed into the program to trigger
different actions, whether AVS, or something else on the web or even locally.

Information in the section is lacking - still learning and will fill in more as
it comes to me.

#### Install python bindings

Go over to the snowboy page on github for the latest information on installation
on your system [https://github.com/Kitt-AI/snowboy]

This project also uses the Python package webrtcvad like Pocket Sphinx to while
recording audio for AVS to detect when speech ends.  Unfortunately it appears
to not be working at the moment, and seems to be recording to the maximum
quiet time before giving up, which is currently set at 4 seconds.  I will be 
working on that to speed up latency for short requests, and not cut off long 
requests.

#### Train wake word

Create an account and train your keyword here: [https://snowboy.kitt.ai/dashboard]

Download the model and apply in the AlexaBeagleBone2 resources folder

Included are three models:
    "Hey Buddy"
    "Alexa"
    "Snowboy"


### Pocket Sphinx

I stripped out the basics from the AlexaPi project to get PocketSphinx working
with this project.  To install the Python package for PocketSphinx, first 
install the dependencies (these were what was missing on my system):

	$ sudo apt-get install swig libpulse-dev
	
	# --no-cache-dir helped turn up above dependenices for pocketsphinx
	$ sudo pip --no-cache-dir install --upgrade pocketsphinx

	$ sudo pip install webrtcvad

# Freeing space on eMMC

You might be ruinng low on eMMC space.  I removed several things, including the 
Chromium browser package (please use care when deleting things!).

On Debian systems, you can use dpkg to see who are taking the most space:

	$ dpkg-query -Wf '${Installed-Size}\t${Package}\n' | sort -n
    

# Features

* Supports voice triggering (PocketSphinx)
* Supports using /dev/input device to initiate voice recording from ALSA input device
* Supports streaming audio (e.g. "Play 106.1")
* Supports asking questions while streaming audio playing - stream resumes after response

# Configuring ALSA

ALSA is a beast.  I prefer not to deal with it, but there are times when it's required, such
as allowing streams to be mixed.  Just a forewarning, these changes were for my system, using
a USB audio card for both input and output.  If you're mixing onboard audio and USB audio
inputs and outputs, things will be different.

## Does your system support multiple streams?

You might be surprised what you find :)

Try playing two audio files simultaneously on the command line.  If your second player instance
gives errors, or is never heard, keep reading the next section.

## Supporting multiple streams

After a bunch of Googling, the answer was found here:
https://discuss.mopidy.com/t/setting-up-c-media-usb-headphone-set-in-mixer-mode/1409/4

In my settings below, notice I'm using hw:1,0 for both dmixed and dsnooped pcm blocks-
this is because I'm using my external USB audio card for input and output.

my /etc/asound.conf settings:
```
	pcm.dmixed {
	    type dmix
	    ipc_key 1024
	    ipc_key_add_uid 0
	    ipc_perm 0666
	    slave.pcm "hw:1,0"
	}
	pcm.dsnooped {
	    type dsnoop
	    ipc_key 1025
	    slave.pcm "hw:1,0"
	}

	pcm.duplex {
	    type asym
	    playback.pcm "dmixed"
	    capture.pcm "dsnooped"
	}

	pcm.!default {
	    type plug
	    slave.pcm "duplex"
	}

	ctl.!default {
	    type hw
	    card 1
	}
```

Old settings for external USB audio card (or your card can handle mixing):

```
	pcm.!default {
	    type hw
	    card 1
	}

	ctl.!default {
	    type hw
	    card 1
	}
```

# Instructions and Usage

* Replace cloned version of creds.py with your known-good credentials file
* Optionally add execute permissions to alexa-mplayer2.py

	$ ./alexa-mplayer2.py


Note: voice triggering is currenting the default interface to AVS.  Going back to a key
press event currently only requires uncommenting the alsabuttonrecord call in main().
Right now I do not support multiple triggering mechanisms.  In the future, the triggering 
and utterance recording mechanisms will be separated.

# Future work

* Use YAML for configuration and holding credentials, trigger source, trigger word, ALSA settings, etc
* Add support for GPIO triggering (keyboard adds latency due to key repeats)
* Overlaying primary and secondary audio streams (simultaneous playback) requires more work
* Separate out triggering and audio logic
* Move global volume control to ALSA layer

"Ever heard of the band 999 MegaBytes?  Probably not, they never made it to a gig" -- Alexa Joke
