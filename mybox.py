#
# Support container for my network monitor hardware box
#
# Written by Glen Darling, February 2020.
#


import json
import os
import subprocess
import threading
import time
import datetime
from collections import deque

from leds import *
from buttons import *


# Import the GPIO library so python can work with the GPIO pins
import RPi.GPIO as GPIO



# Debug flags
DEBUG_FAN = False

# Debug print
def debug(flag, str):
  if flag:
    print(str)




# These values need to be provided in the container environment
MY_LED_MAIN_GREEN    = int(os.environ['MY_LED_MAIN_GREEN'])
MY_LED_MAIN_RED      = int(os.environ['MY_LED_MAIN_RED'])
MY_LED_ROUTER_GREEN  = int(os.environ['MY_LED_ROUTER_GREEN'])
MY_LED_ROUTER_RED    = int(os.environ['MY_LED_ROUTER_RED'])
MY_LED_MODEM_GREEN   = int(os.environ['MY_LED_MODEM_GREEN'])
MY_LED_MODEM_RED     = int(os.environ['MY_LED_MODEM_RED'])
MY_RELAY_WIFI        = int(os.environ['MY_RELAY_WIFI'])
MY_RELAY_ROUTER      = int(os.environ['MY_RELAY_ROUTER'])
MY_RELAY_MODEM       = int(os.environ['MY_RELAY_MODEM'])
MY_BUTTON_MAIN       = int(os.environ['MY_BUTTON_MAIN'])
MY_BUTTON_WIFI       = int(os.environ['MY_BUTTON_WIFI'])
MY_BUTTON_ROUTER     = int(os.environ['MY_BUTTON_ROUTER'])
MY_BUTTON_MODEM      = int(os.environ['MY_BUTTON_MODEM'])
MY_FAN_CONTROL_PWM   = int(os.environ['MY_FAN_CONTROL_PWM'])



# Setup the GPIOs
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(MY_LED_MAIN_GREEN, GPIO.OUT)
GPIO.setup(MY_LED_MAIN_RED, GPIO.OUT)
GPIO.setup(MY_LED_ROUTER_GREEN, GPIO.OUT)
GPIO.setup(MY_LED_ROUTER_RED, GPIO.OUT)
GPIO.setup(MY_LED_MODEM_GREEN, GPIO.OUT)
GPIO.setup(MY_LED_MODEM_RED, GPIO.OUT)
GPIO.setup(MY_RELAY_WIFI, GPIO.OUT)
GPIO.setup(MY_RELAY_ROUTER, GPIO.OUT)
GPIO.setup(MY_RELAY_MODEM, GPIO.OUT)
GPIO.setup(MY_BUTTON_MAIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MY_BUTTON_WIFI, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MY_BUTTON_ROUTER, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MY_BUTTON_MODEM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MY_FAN_CONTROL_PWM, GPIO.OUT)
PWM_FREQUENCY = 110
fan_percent = GPIO.PWM(MY_FAN_CONTROL_PWM, PWM_FREQUENCY)



# Turn the appropriate outlet off then back on
def power_cycle(which):
  print("Power cycle \"%s\"." % (which))



# Loop forever checking CPU temperature and adjusting the fan PWM
FAN_RAMP_START = 40.0 # I.e., fan starts to ramp up speed at this temp (in C)
FAN_RAMP_FULL = 60.0 # I.e., max fan starts at this temp (in C)
FAN_MIN = 25.0 # Baseline fan speed in percent (it will never go below this)
SLEEP_BETWEEN_TEMP_CHECKS_SEC = 20
CPUTEMP_PATH = '/cputemp'
class FanThread(threading.Thread):
  def run(self):
    global fan_percent
    debug(DEBUG_FAN, ("Fan management thread started!"))
    fn = CPUTEMP_PATH
    while True:
      with open(fn, 'r') as file:
        temp = float(file.read().replace('\n', '')) / 1000.0
      fan_ramp = 0
      if temp >= FAN_RAMP_START:
        fan_ramp = temp - FAN_RAMP_START
      if temp >= FAN_RAMP_FULL:
        fan_ramp = (FAN_RAMP_FULL - FAN_RAMP_START)
      fan_pct = int(100.0 * (fan_ramp / (FAN_RAMP_FULL - FAN_RAMP_START)))
      if fan_pct < FAN_MIN:
        fan_pct = FAN_MIN
      if fan_pct > 100:
        fan_pct = 100
      debug(DEBUG_FAN, ("--> FAN: t=%0.1f\N{DEGREE SIGN}C, f=%d%%\n" % (temp, fan_pct)))
      fan_percent.ChangeDutyCycle(fan_pct)
      time.sleep(SLEEP_BETWEEN_TEMP_CHECKS_SEC)



# Loop forever checking status, and setting status LEDs accordingly
SLEEP_BETWEEN_STATUS_CHECKS_SEC = 10
led_main = None
led_router = None
led_modem = None
class StatusThread(threading.Thread):
  def run(self):
    while True:
      time.sleep(SLEEP_BETWEEN_STATUS_CHECKS_SEC)



# Loop forever watching the buttons, and if needed, power cycling things
FLASH_START = 2
FLASH_ENOUGH = 7
CYCLING_MINIMUM = 30
SLEEP_BETWEEN_BUTTON_CHECKS_SEC = 0.25
button_main = None
button_wifi = None
button_router = None
button_modem = None
button_main_start = None
button_main_cycling = None
button_wifi_start = None
button_router_start = None
button_modem_start = None
class ButtonThread(threading.Thread):
  def run(self):
    global button_main_start
    global button_main_cycling
    global button_wifi_start
    global button_router_start
    global button_modem_start
    global led_main
    global led_router
    global led_modem
    while True:

      #  main button
      if not button_main.is_pressed():
        button_main_start = None
        button_main_cycling = None
        led_main.flash(False)
      elif button_main.is_pressed() and not button_main_start:
        button_main_start = time.time()
      else:
        elapsed = (time.time() - button_main_start)
        if elapsed > FLASH_START:
          led_main.flash(True)
        if elapsed > FLASH_ENOUGH and not button_main_cycling:
          led_main.flash(False)
          button_main_cycling = time.time()
          power_cycle("main")
        elif elapsed > FLASH_ENOUGH and button_main_cycling:
          elapsed_cycling = (time.time() - button_main_cycling)
          if elapsed_cycling > CYCLING_MINIMUM:
            button_main_cycling = None

      # wifi button
      if not button_wifi.is_pressed():
        button_wifi_start = None
        button_wifi_cycling = None
      elif button_wifi.is_pressed() and not button_wifi_start:
        button_wifi_start = time.time()
      else:
        elapsed = (time.time() - button_wifi_start)
        if elapsed > FLASH_ENOUGH and not button_wifi_cycling:
          button_wifi_cycling = time.time()
          power_cycle("wifi")
        elif elapsed > FLASH_ENOUGH and button_wifi_cycling:
          elapsed_cycling = (time.time() - button_wifi_cycling)
          if elapsed_cycling > CYCLING_MINIMUM:
            button_wifi_cycling = None

      # router button
      if not button_router.is_pressed():
        button_router_start = None
        button_router_cycling = None
        led_router.flash(False)
      elif button_router.is_pressed() and not button_router_start:
        button_router_start = time.time()
      else:
        elapsed = (time.time() - button_router_start)
        if elapsed > FLASH_START:
          led_router.flash(True)
        if elapsed > FLASH_ENOUGH and not button_router_cycling:
          led_router.flash(False)
          button_router_cycling = time.time()
          power_cycle("router")
        elif elapsed > FLASH_ENOUGH and button_router_cycling:
          elapsed_cycling = (time.time() - button_router_cycling)
          if elapsed_cycling > CYCLING_MINIMUM:
            button_router_cycling = None


      # modem button
      if not button_modem.is_pressed():
        button_modem_start = None
        button_modem_cycling = None
        led_modem.flash(False)
      elif button_modem.is_pressed() and not button_modem_start:
        button_modem_start = time.time()
      else:
        elapsed = (time.time() - button_modem_start)
        if elapsed > FLASH_START:
          led_modem.flash(True)
        if elapsed > FLASH_ENOUGH and not button_modem_cycling:
          led_modem.flash(False)
          button_modem_cycling = time.time()
          power_cycle("modem")
        elif elapsed > FLASH_ENOUGH and button_modem_cycling:
          elapsed_cycling = (time.time() - button_modem_cycling)
          if elapsed_cycling > CYCLING_MINIMUM:
            button_modem_cycling = None

      time.sleep(SLEEP_BETWEEN_BUTTON_CHECKS_SEC)



# Main program (instantiates and starts threads)
if __name__ == '__main__':

  # Initialize the output pins

  # LEDs:
  GPIO.output(MY_LED_MAIN_GREEN, GPIO.LOW)
  GPIO.output(MY_LED_MAIN_RED, GPIO.LOW)
  GPIO.output(MY_LED_ROUTER_GREEN, GPIO.LOW)
  GPIO.output(MY_LED_ROUTER_RED, GPIO.LOW)
  GPIO.output(MY_LED_MODEM_GREEN, GPIO.LOW)
  GPIO.output(MY_LED_MODEM_RED, GPIO.LOW)

  # Relays:
  GPIO.output(MY_RELAY_WIFI, GPIO.HIGH)
  GPIO.output(MY_RELAY_ROUTER, GPIO.HIGH)
  GPIO.output(MY_RELAY_MODEM, GPIO.HIGH)

  # Fan: (set initial value; change with: `fan_percent.ChangeDutyCycle(100)`
  fan_percent.start(100)

  # Enable warnings here, after initialization (to avoid some init noise)
  GPIO.setwarnings(True)

  # Monitor CPU temperature and adjust fan accordingly
  fan = FanThread()
  fan.start()

  # Create the button objects
  button_main = Button("main", MY_BUTTON_MAIN)
  button_wifi = Button("wifi", MY_BUTTON_WIFI)
  button_router = Button("router", MY_BUTTON_ROUTER)
  button_modem = Button("modem", MY_BUTTON_MODEM)

  # Create the LED objects
  led_main = LED("main", MY_LED_MAIN_GREEN, MY_LED_MAIN_RED)
  led_router = LED("router", MY_LED_ROUTER_GREEN, MY_LED_ROUTER_RED)
  led_modem = LED("modem", MY_LED_MODEM_GREEN, MY_LED_MODEM_RED)

  # Monitor status, and operate the status LEDs accordingly
  stable = False
  led_main.red()
  status = StatusThread()
  status.start()

  # Monitor the button objects, and operate the LED objects accordingly
  buttons = ButtonThread()
  buttons.start()

  # Prevent exit and operate the LED flasher
  while True:
    LED.toggle_flasher()
    time.sleep(0.5)

