#
# LED objects
#
# Written by Glen Darling, February 2020.
#


import threading
import time


# Import the GPIO library so python can work with the GPIO pins
import RPi.GPIO as GPIO



# Debug flags
DEBUG_LEDS = False

# Debug print
def debug(flag, str):
  if flag:
    print(str)



# Class to operate LEDs
SLEEP_BETWEEN_STATE_CHECKS_SEC = 0.25
class LED(threading.Thread):

  flasher = False

  @classmethod
  def toggle_flasher(cls):
    cls.flasher = not cls.flasher

  def __init__(self, name, gpio_green, gpio_red):
    threading.Thread.__init__(self)
    self.name = name
    self.gpio_green = gpio_green
    self.gpio_red = gpio_red
    self._green = False
    self._red = False
    self._flash = False
    self.start()

  def off(self):
    self._green = False
    self._red = False

  def green(self):
    self._green = True
    self._red = False

  def red(self):
    self._green = False
    self._red = True

  def flash(self, which):
    self._flash = which

  def run(self):
    debug(DEBUG_LEDS, ("LED thread for GPIOs #%d/#%d started!" % (self.gpio_green, self.gpio_red)))
    while True:
      on = True
      if self._flash:
        on = LED.flasher 
      if on and self._green:
        GPIO.output(self.gpio_green, GPIO.HIGH)
      else:
        GPIO.output(self.gpio_green, GPIO.LOW)
      if on and self._red:
        GPIO.output(self.gpio_red, GPIO.HIGH)
      else:
        GPIO.output(self.gpio_red, GPIO.LOW)
      debug(DEBUG_LEDS, ("--> LED \"%s\": f=%s:(%s), g=%s, r=%s" % (self.name, str(self._flash), str(LED.flasher), str(self._green), str(self._red))))
      time.sleep(SLEEP_BETWEEN_STATE_CHECKS_SEC)



