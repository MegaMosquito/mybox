#
# A class to support R, G, or B flashing RGB LEDs for my network monitor box.
#
# Caller must configure the RPi.GPIO library and each pin before hand. E.g.:
#    GPIO.setmode(GPIO.BCM)
#    GPIO.setup(<<pin>>, GPIO.OUT)
#    x = RGB_LED("foo", 20, 21, 18)
#
# Written by Glen Darling, February 2020.
#


import threading
import time


# Import the GPIO library so python can work with the GPIO pins
import RPi.GPIO as GPIO


# Debug flags
DEBUG_RGB_LEDS = False

# Debug print
def debug(flag, str):
  if flag:
    print(str)


SLEEP_BETWEEN_UPDATES_SEC = 0.1
class RGB_LED(threading.Thread):

  flash_state = False

  # The main program must call this regularly to change the flash state
  @classmethod
  def toggle_flash_state(cls):
    cls.flash_state = not cls.flash_state

  # Constructor for an RGB_LED
  # Pass None to the constuctor as a color pin number to not use that color.
  # E.g., to not use blue:  x = RGB_LED("foo", 20, 21, None)
  def __init__(self, name, gpio_red, gpio_green, gpio_blue):
    threading.Thread.__init__(self)
    self.name = name
    self.gpio_red = gpio_red
    self.gpio_green = gpio_green
    self.gpio_blue = gpio_blue
    self._red = False
    self._green = False
    self._blue = False
    self._flash = False
    self._keep_swimming = True
    self.start()

  # Command this RGB_LED to turn off
  def off(self):
    self._green = False
    self._red = False
    self._blue = False

  # Command this RGB_LED to turn red
  def red(self):
    self._green = False
    self._red = True
    self._blue = False

  # Command this RGB_LED to turn green
  def green(self):
    self._green = True
    self._red = False
    self._blue = False

  # Command this RGB_LED to turn blue
  def blue(self):
    self._green = True
    self._red = False
    self._blue = True

  # Return a string describing the current state of hit RGB_LED (for debugging)
  def state(self):
    if self._flash:
      if self._red: return "red,flashing"
      elif self._green: return "green,flashing"
      elif self._blue: return "blue,flashing"
    else:
      if self._red: return "red,solid"
      elif self._green: return "green,solid"
      elif self._blue: return "blue,solid"
    return "off"

  # Command this RGB_LED to start or stop flashing
  def flash(self, which):
    self._flash = which

  def stop(self):
    self._keep_swimming = False

  def run(self):
    debug(DEBUG_RGB_LEDS, ("Starting RGB_LED \"%s\", pins: R=%s G=%s B=%s" % (self.name, str(self.gpio_red), str(self.gpio_green), str(self.gpio_blue))))
    while self._keep_swimming:
      on = True
      # If this RGB_LED is in flashing state
      if self._flash:
        # Set "on" to the state of the global toggle (else leave it on)
        on = RGB_LED.flash_state 
      # if a gpio pin is defined for red:
      if self.gpio_red:
        # if the global toggle is on, and red is active (true) on this RGB_LED:
        if on and self._red:
          GPIO.output(self.gpio_red, GPIO.HIGH)
        # Otherwise the global toggle is off, or red is nto currently active
        else:
          GPIO.output(self.gpio_red, GPIO.LOW)
      if self.gpio_green:
        if on and self._green:
          GPIO.output(self.gpio_green, GPIO.HIGH)
        else:
          GPIO.output(self.gpio_green, GPIO.LOW)
      if self.gpio_blue:
        if on and self._blue:
          GPIO.output(self.gpio_blue, GPIO.HIGH)
        else:
          GPIO.output(self.gpio_blue, GPIO.LOW)
      if self._red or self._green or self._blue:
        debug(DEBUG_RGB_LEDS, ("--> RGB_LED \"%s\", state: %s" % (self.name, self.state())))
      time.sleep(SLEEP_BETWEEN_UPDATES_SEC)



