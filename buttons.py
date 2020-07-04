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
    self._keep_swimming = True
    self._start_time = None
    self.start()

  def is_pressed(self):
    return self._is_pressed

  def held_time(self):
    if not self._is_pressed:
      return 0
    else:
      return (time.time() - self._start_time)

  def stop(self):
    self._keep_swimming = False

  def run(self):
    debug(DEBUG_BUTTONS, ("Button monitor for \"%s\" (GPIO#%d) started!" % (self.name, self.gpio)))
    while self._keep_swimming:

      # Note previous state
      was_pressed = self._is_pressed
      # Get current state
      self._is_pressed = '1' != str(GPIO.input(self.gpio))

      # If not pressed, reset the held timer

      # Is the button just being pressed?
      if not was_pressed and self._is_pressed:
        # Note the start time for the "held()" function
        self._start_time = time.time()

      # If the button state has changed, emit this debug message
      if was_pressed != self._is_pressed:
        if self._is_pressed:
          debug(DEBUG_BUTTONS, ("--> Button \"%s\"(GPIO#%d): %s" % (self.name, self.gpio, str(self._is_pressed))))
      # Else if it is on show how long it has been held down
      elif self._is_pressed:
        debug(DEBUG_BUTTONS, ("--> Button \"%s\"(GPIO#%d): %s (%0.1fs)" % (self.name, self.gpio, str(self._is_pressed), self.held_time())))

      time.sleep(SLEEP_BETWEEN_STATE_CHECKS_SEC)



