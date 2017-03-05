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

Note: credentials file is missing - add creds.py

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

Features
========

* Supports using /dev/input device to initiate voice recording from ALSA input device
* Supports streaming audio (e.g. "Play 106.1")
* Supports asking questions while streaming audio playing - stream resumes after response

Instructions and Usage
======================

* Replace cloned version of creds.py with your known-good credentials file
* Optionally add execute permissions to alexa-mplayer2.py

$ sudo ./alexa-mplayer2.py   # accessing /dev/input/event* needs root

Future work
===========

* Use YAML for configuration and holding credentials
* Add support for GPIO triggering (keyboard adds latency due to key repeats)
* Add support for hands free voice triggering (already have a prototype working)
* Support overlaying primary and secondary audio streams (simultaneous playback)
