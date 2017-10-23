import os, time, threading

led0_on = 'echo 1 > /sys/class/leds/beaglebone:green:usr0/brightness'
led0_off = 'echo 0 > /sys/class/leds/beaglebone:green:usr0/brightness'
led1_on = 'echo 1 > /sys/class/leds/beaglebone:green:usr1/brightness'
led1_off = 'echo 0 > /sys/class/leds/beaglebone:green:usr1/brightness'
led2_on = 'echo 1 > /sys/class/leds/beaglebone:green:usr2/brightness'
led2_off = 'echo 0 > /sys/class/leds/beaglebone:green:usr2/brightness'
led3_on = 'echo 1 > /sys/class/leds/beaglebone:green:usr3/brightness'
led3_off = 'echo 0 > /sys/class/leds/beaglebone:green:usr3/brightness'

class userLedScanThread (threading.Thread):
	def __init__(self, name='scanThread'):
		self._stopevent = threading.Event()
		threading.Thread.__init__(self, name=name)
	def run(self):
		userled_clear()
		while not self._stopevent.isSet():
			userled_scan()
			self._stopevent.wait(0.1)

	def join(self, timeout=None):
		self._stopevent.set()
		threading.Thread.join(self, timeout)
		
def userled_clear():
	os.system(led0_off)
        os.system(led1_off)
        os.system(led2_off)
        os.system(led3_off)

def userled_sweep():
	userled_clear()
	os.system(led0_on)
	time.sleep(0.05)
	os.system(led1_on)
	time.sleep(0.05)
	os.system(led2_on)
	time.sleep(0.05)
	os.system(led3_on)

def userled_scan():
	os.system(led0_on)
	time.sleep(0.05)
	os.system(led1_on)
	os.system(led0_off)
	time.sleep(0.05)
	os.system(led2_on)
	os.system(led1_off)
	time.sleep(0.05)
	os.system(led3_on)
	os.system(led2_off)
	time.sleep(0.05)
	os.system(led2_on)
	os.system(led3_off)
	time.sleep(0.05)
	os.system(led1_on)
	os.system(led2_off)
	time.sleep(0.05)
	os.system(led0_on)
	os.system(led1_off)
	time.sleep(0.05)
	os.system(led0_off)

scanThread = userLedScanThread()

def userled_startScan():
	global scanThread
	scanThread = userLedScanThread()
	scanThread.start()

def userled_stopScan():
	global scanThread
	scanThread.join()

if __name__ == "__main__":
	scanThread = userLedScanThread()

	userled_sweep()
	time.sleep(1.0)
	
	scanThread.start()
	time.sleep(1)
	scanThread.join()

