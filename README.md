Changes and improvements from AlexaBeagleBone
=============================================

Dependency on VLC has been removed.  VLC is great, however on the BeagleBone
Black, it is a bit overkill, and is difficult to build from source if you're on
Yocto filesystem (such as the TI Linux Processor SDK).  Mplayer is another
capable media player available on ARM Linux, low CPU usage, and builds natively
on TI ARM platforms running a recent Yocto filesystem without much fuss
(probably the case with other platforms, but I've only worked with TI
processors).

Mplayer can be put into slave mode and controlled through special files (fifo).
The pymplb wrapper by Stefan Parviainen is a clean and elegant solution for
programatically controlling Mplayer from Python.

Voice triggering is also now supported using PocketSphinx.  Other voice triggering
libraries will be tested as well.  CPU usage seems reasonable, even while
streaming audio and performing a voice triggering session.

Build Instructions
==================

For now things are not terribly user friendly, and are more focused towards my
own development.  Probably the most ornerious task will be creating an AVS
credentials file.

These instructions are written using Debian 8.7, and kernel version 4.4.30
on a Beaglebone Black Wireless (out of box image on eMMC).  Yes, I did rant
above about Yocto, but for now I am starting with Debian, then will switch
over to Yocto filesystem and add instructions for building dependencies.

The following information below is a collection of my own notes, and hopefully
is complete.

Adding Required Linux System Libraries
--------------------------------------

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

Adding Python Packages
----------------------

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

Optional Voice Triggering
-------------------------

I stripped out the basics from the AlexaPi project to get PocketSphinx working
with this project.  To install the Python package for PocketSphinx, first 
install the dependencies (these were what was missing on my system):

	$ sudo apt-get install swig libpulse-dev
	
	# --no-cache-dir helped turn up above dependenices for pocketsphinx
	$ sudo pip --no-cache-dir install --upgrade pocketsphinx

	$ sudo pip install webrtcvad

Freeing space on eMMC
=====================

You might be ruinng low on eMMC space.  I removed several things, including the 
Chromium browser package.

On Debian systems, you can use dpkg to see who are taking the most space:

	$ dpkg-query -Wf '${Installed-Size}\t${Package}\n' | sort -n
    

Features
========

* Supports voice triggering (PocketSphinx)
* Supports using /dev/input device to initiate voice recording from ALSA input device
* Supports streaming audio (e.g. "Play 106.1")
* Supports asking questions while streaming audio playing - stream resumes after response

Instructions and Usage
======================

* Replace cloned version of creds.py with your known-good credentials file
* Optionally add execute permissions to alexa-mplayer2.py

	$ ./alexa-mplayer2.py


Note: voice triggering is currenting the default interface to AVS.  Going back to a key
press event currently only requires uncommenting the alsabuttonrecord call in main().
Right now I do not support multiple triggering mechanisms.  In the future, the triggering 
and utterance recording mechanisms will be separated.

Future work
===========

* Use YAML for configuration and holding credentials
* Add support for GPIO triggering (keyboard adds latency due to key repeats)
* Support overlaying primary and secondary audio streams (simultaneous playback)
