#
# Button objects
#
# Written by Glen Darling, February 2020.
#


import threading
import time


# Import the GPIO library so python can work with the GPIO pins
import RPi.GPIO as GPIO



# Debug flags
DEBUG_BUTTONS = False

# Debug print
def debug(flag, str):
  if flag:
    print(str)



# Class to monitor buttons
SLEEP_BETWEEN_STATE_CHECKS_SEC = 0.25
class Button(threading.Thread):

  def __init__(self, name, gpio):
    threading.Thread.__init__(self)
    self.name = name
    self.gpio = gpio
    self._is_pressed = False
    self.start()

  def is_pressed(self):
    return self._is_pressed

  def run(self):
    debug(DEBUG_BUTTONS, ("Button monitor for \"%s\" (GPIO#%d) started!" % (self.name, self.gpio)))
    while True:
      was = self._is_pressed
      self._is_pressed = '1' != str(GPIO.input(self.gpio))
      if was != self._is_pressed:
        debug(DEBUG_BUTTONS, ("--> Button \"%s\"(GPIO#%d): %s" % (self.name, self.gpio, str(self._is_pressed))))
      time.sleep(SLEEP_BETWEEN_STATE_CHECKS_SEC)



