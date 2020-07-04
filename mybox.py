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

from rgb_leds import *
from buttons import *
from chk_wifi import *


# Import the GPIO library so python can work with the GPIO pins
import RPi.GPIO as GPIO



# Debug flags
DEBUG_GPIO = False
DEBUG_SIGNALS = False
DEBUG_FAN = False
DEBUG_PING = False
DEBUG_POWER = False
DEBUG_WIFI_MONITORS = False

# Debug print
def debug(flag, str):
  if flag:
    print(str)



# These values need to be provided in the container environment

MY_LED_MAIN_GREEN    = int(os.environ['MY_LED_MAIN_GREEN'])
MY_LED_MAIN_RED      = int(os.environ['MY_LED_MAIN_RED'])
MY_LED_WIFI_GREEN    = int(os.environ['MY_LED_WIFI_GREEN'])
MY_LED_WIFI_RED      = int(os.environ['MY_LED_WIFI_RED'])
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
MY_ROUTER_IP         = os.environ['MY_ROUTER_IP']
MY_WIFI_AP_IP        = os.environ['MY_WIFI_AP_IP']
MY_OUTSIDE_IP        = os.environ['MY_OUTSIDE_IP']
MY_WIFI_MONITORS     = os.environ['MY_WIFI_MONITORS']



# Setup the GPIOs
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(MY_LED_MAIN_GREEN, GPIO.OUT)
GPIO.setup(MY_LED_MAIN_RED, GPIO.OUT)
GPIO.setup(MY_LED_WIFI_GREEN, GPIO.OUT)
GPIO.setup(MY_LED_WIFI_RED, GPIO.OUT)
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
debug(DEBUG_GPIO, 'GPIO pin modes set.')


# A global to control all of the thread loops
keep_on_swimming = True



# A thread to loop forever checking CPU temperature and adjusting the fan PWM
FAN_RAMP_START = 40.0 # I.e., fan starts to ramp up speed at this temp (in C)
FAN_RAMP_FULL = 60.0 # I.e., max fan starts at this temp (in C)
FAN_MIN = 25.0 # Baseline fan speed in percent (it will never go below this)
SLEEP_BETWEEN_TEMP_CHECKS_SEC = 120
CPUTEMP_PATH = '/cputemp'
class FanThread(threading.Thread):
  def run(self):
    global fan_percent
    debug(DEBUG_FAN, ("Fan management thread started!"))
    fn = CPUTEMP_PATH
    global keep_on_swimming
    while keep_on_swimming:
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



# A thread to set a specified relay low, pause, then set it high again
power_cycling_target = None
POWER_OFF_CONFIRMATION_SEC = 3
POWER_OFF_DURATION_SEC = 10
def power_cycle(relay):
  global power_cycling_target
  debug(DEBUG_POWER, ("Power cycling \"%s\"... [OFF]" % (power_cycling_target)))
  GPIO.output(relay, GPIO.LOW)
  time.sleep(POWER_OFF_DURATION_SEC)
  GPIO.output(relay, GPIO.HIGH)
  debug(DEBUG_POWER, ("Power cycling \"%s\"... [ON!]" % (power_cycling_target)))
  power_cycling_target = None

# Turn the appropriate outlet off then back on, then reset state
def start_power_cycle(which):
  if "main" == which:
    global power_cycling_target
    debug(DEBUG_POWER, "Power cycling all devices ... [OFF]")
    rgb_led_main.red()
    rgb_led_main.flash(False)
    time.sleep(POWER_OFF_CONFIRMATION_SEC)
    GPIO.output(MY_RELAY_WIFI, GPIO.LOW)
    GPIO.output(MY_RELAY_ROUTER, GPIO.LOW)
    GPIO.output(MY_RELAY_MODEM, GPIO.LOW)
    rgb_led_main.green()
    rgb_led_main.flash(True)
    time.sleep(POWER_OFF_DURATION_SEC)
    debug(DEBUG_POWER, "Power cycling all devices ... [ROUTER->ON!]")
    rgb_led_router.green()
    rgb_led_router.flash(True)
    GPIO.output(MY_RELAY_ROUTER, GPIO.HIGH)
    time.sleep(5)
    debug(DEBUG_POWER, "Power cycling all devices ... [WIFI->ON!]")
    rgb_led_wifi.green()
    rgb_led_wifi.flash(True)
    GPIO.output(MY_RELAY_WIFI, GPIO.HIGH)
    time.sleep(1)
    debug(DEBUG_POWER, "Power cycling all devices ... [MODEM->ON!]")
    rgb_led_modem.green()
    rgb_led_modem.flash(True)
    GPIO.output(MY_RELAY_MODEM, GPIO.HIGH)
    power_cycling_target = None
  elif "wifi" == which:
    t = threading.Thread(target=power_cycle, args=[MY_RELAY_WIFI])
    rgb_led_wifi.red()
    rgb_led_wifi.flash(False)
    time.sleep(POWER_OFF_CONFIRMATION_SEC)
    rgb_led_wifi.green()
    rgb_led_wifi.flash(True)
    t.start()
  elif "router" == which:
    t = threading.Thread(target=power_cycle, args=[MY_RELAY_ROUTER])
    rgb_led_router.red()
    rgb_led_router.flash(False)
    time.sleep(POWER_OFF_CONFIRMATION_SEC)
    rgb_led_router.green()
    rgb_led_router.flash(True)
    t.start()
  elif "modem" == which:
    t = threading.Thread(target=power_cycle, args=[MY_RELAY_MODEM])
    rgb_led_modem.red()
    rgb_led_modem.flash(False)
    time.sleep(POWER_OFF_CONFIRMATION_SEC)
    rgb_led_modem.green()
    rgb_led_modem.flash(True)
    t.start()


SLEEP_BETWEEN_PINGS_SEC = 10
PING_TIMEOUT_SEC = 10
ping_times = {}
class PingThread(threading.Thread):
  def __init__(self, name, addr):
    threading.Thread.__init__(self)
    global ping_times
    self._name = name
    self._addr = addr
    ping_times[self._name] = 0
  def run(self):
    global ping_times
    debug(DEBUG_PING, ('--> ping %s (%s)' % (self._name, self._addr)))
    global keep_on_swimming
    while keep_on_swimming:
      try:
        p = subprocess.run('ping -c 1 ' + self._addr + ' >/dev/null 2>&1', capture_output=False, shell=True, check=True, timeout=PING_TIMEOUT_SEC)
        # The ping command returned in time with 0 exit status
        ping_times[self._name] = time.time()
        debug(DEBUG_PING, ('<-- ping %s (%s) [UP]' % (self._name, self._addr)))
      except subprocess.CalledProcessError:
        # The ping command gave a non-zero exit status (host did not respond)
        debug(DEBUG_PING, ('<-- ping %s (%s) [DN]' % (self._name, self._addr)))
      except subprocess.TimeoutExpired:
        # The ping command did not complete before the timeout
        p.kill()
        debug(DEBUG_PING, ('<-- ping %s (%s) [TO]' % (self._name, self._addr)))
      time.sleep(SLEEP_BETWEEN_PINGS_SEC)

# Loop forever checking status, and setting status LEDs accordingly
SLEEP_BETWEEN_LED_CHECKS_SEC = 2
MIN_TOLERANCE = 1 + (SLEEP_BETWEEN_PINGS_SEC + PING_TIMEOUT_SEC)
ROUTER_ALIVE_TOLERANCE_SEC = MIN_TOLERANCE
ROUTER_DEAD_TOLERANCE_SEC = MIN_TOLERANCE + 60
WIFI_AP_ALIVE_TOLERANCE_SEC = MIN_TOLERANCE
WIFI_AP_DEAD_TOLERANCE_SEC = MIN_TOLERANCE + 60
MONITORS_ALIVE_TOLERANCE_SEC = MIN_TOLERANCE + 30
MONITORS_DEAD_TOLERANCE_SEC = MIN_TOLERANCE + 90
OUTSIDE_ALIVE_TOLERANCE_SEC = 120
OUTSIDE_DEAD_TOLERANCE_SEC = 240
rgb_led_main = None
rgb_led_wifi = None
rgb_led_router = None
rgb_led_modem = None
no_buttons_active = True
class StatusThread(threading.Thread):
  def run(self):
    rgb_led_main.green()
    rgb_led_wifi.green()
    rgb_led_router.green()
    rgb_led_modem.green()
    rgb_led_main.flash(True)
    rgb_led_wifi.flash(True)
    rgb_led_router.flash(True)
    rgb_led_modem.flash(True)
    import ast
    wifis = ast.literal_eval(MY_WIFI_MONITORS)
    wifi = WiFiMonitor(wifis)
    router_ping_thread = PingThread("router", MY_ROUTER_IP)
    router_ping_thread.start()
    wifi_ap_ping_thread = PingThread("ap", MY_WIFI_AP_IP)
    wifi_ap_ping_thread.start()
    outside_ping_thread = PingThread("outside", MY_OUTSIDE_IP)
    outside_ping_thread.start()
    last_good_wifi = 0
    last_good_router = 0
    last_good_outside = 0
    last_good_monitors = 0
    global no_buttons_active
    global keep_on_swimming
    while keep_on_swimming:

      # Pause status updates when power cycling in progress
      if None == power_cycling_target and no_buttons_active:

        # Local router status
        last_good_router = ping_times["router"]
        if ROUTER_ALIVE_TOLERANCE_SEC >= (time.time() - last_good_router):
          rgb_led_router.green()
          rgb_led_router.flash(False)
        elif ROUTER_DEAD_TOLERANCE_SEC < (time.time() - last_good_router):
          rgb_led_router.red()
          rgb_led_router.flash(True)
        else:
          rgb_led_router.green()
          rgb_led_router.flash(True)

        # Local WiFi access point status
        last_good_wifi = ping_times["ap"]
        if WIFI_AP_ALIVE_TOLERANCE_SEC >= (time.time() - last_good_wifi):
          rgb_led_wifi.green()
          rgb_led_wifi.flash(False)
        elif WIFI_AP_DEAD_TOLERANCE_SEC < (time.time() - last_good_wifi):
          rgb_led_wifi.red()
          rgb_led_wifi.flash(True)
        else:
          rgb_led_wifi.green()
          rgb_led_wifi.flash(True)

        # Local outside internet connection status
        last_good_outside = ping_times["outside"]
        if OUTSIDE_ALIVE_TOLERANCE_SEC >= (time.time() - last_good_outside):
          rgb_led_modem.green()
          rgb_led_modem.flash(False)
        elif OUTSIDE_DEAD_TOLERANCE_SEC < (time.time() - last_good_outside):
          rgb_led_modem.red()
          rgb_led_modem.flash(True)
        else:
          rgb_led_modem.green()
          rgb_led_modem.flash(True)

        # WiFi monitors' connection status
        last_good_monitors = wifi.last_good_status()
        debug(DEBUG_WIFI_MONITORS, '--> LastGoodMonitors: %0.1fs' % (last_good_monitors))
        if MONITORS_ALIVE_TOLERANCE_SEC >= (time.time() - last_good_monitors):
          debug(DEBUG_WIFI_MONITORS, '** GOOD!')
          rgb_led_main.green()
          rgb_led_main.flash(False)
        elif MONITORS_DEAD_TOLERANCE_SEC < (time.time() - last_good_monitors):
          debug(DEBUG_WIFI_MONITORS, '** BAD!')
          rgb_led_main.red()
          rgb_led_main.flash(True)
        else:
          debug(DEBUG_WIFI_MONITORS, '** ????')
          rgb_led_main.green()
          rgb_led_main.flash(True)

      time.sleep(SLEEP_BETWEEN_LED_CHECKS_SEC)

    wifi.stop()



# Loop forever watching the buttons, and if needed, power cycling things
FLASH_START_SEC = 0.5
FLASH_ENOUGH_SEC = 5.0
SLEEP_BETWEEN_BUTTON_CHECKS_SEC = 0.33
button_main = None
button_wifi = None
button_router = None
button_modem = None
class ButtonThread(threading.Thread):
  def run(self):
    global button_main
    global button_wifi
    global button_router
    global button_modem
    global rgb_led_main
    global rgb_led_wifi
    global rgb_led_router
    global rgb_led_modem
    global power_cycling_target
    global no_buttons_active
    global keep_on_swimming
    while keep_on_swimming:

      no_buttons_active = not (button_main.is_pressed() or button_wifi.is_pressed() or button_router.is_pressed() or button_modem.is_pressed())

      # Ignore the buttons if anything is already power cycling
      if None == power_cycling_target:

        # main button
        if button_main.held_time() > 0 and button_main.held_time() < FLASH_START_SEC:
          rgb_led_main.green()
          rgb_led_main.flash(False)
        elif button_main.held_time() > FLASH_START_SEC:
          rgb_led_main.red()
          rgb_led_main.flash(True)
          if button_main.held_time() > FLASH_ENOUGH_SEC:
            power_cycling_target = "main"
            start_power_cycle("main")

        # wifi button
        if button_wifi.held_time() > 0 and button_wifi.held_time() < FLASH_START_SEC:
          rgb_led_wifi.green()
          rgb_led_wifi.flash(False)
        elif button_wifi.held_time() > FLASH_START_SEC:
          rgb_led_wifi.red()
          rgb_led_wifi.flash(True)
          if button_wifi.held_time() > FLASH_ENOUGH_SEC:
            power_cycling_target = "wifi"
            start_power_cycle("wifi")

        # router button
        if button_router.held_time() > 0 and button_router.held_time() < FLASH_START_SEC:
          rgb_led_router.green()
          rgb_led_router.flash(False)
        elif button_router.held_time() >= FLASH_START_SEC:
          rgb_led_router.red()
          rgb_led_router.flash(True)
          if button_router.held_time() > FLASH_ENOUGH_SEC:
            power_cycling_target = "router"
            start_power_cycle("router")

        # modem button
        if button_modem.held_time() > 0 and button_modem.held_time() < FLASH_START_SEC:
          rgb_led_modem.green()
          rgb_led_modem.flash(False)
        elif button_modem.held_time() > FLASH_START_SEC:
          rgb_led_modem.red()
          rgb_led_modem.flash(True)
          if button_modem.held_time() > FLASH_ENOUGH_SEC:
            power_cycling_target = "modem"
            start_power_cycle("modem")

      time.sleep(SLEEP_BETWEEN_BUTTON_CHECKS_SEC)



# Main program (instantiates and starts threads)
if __name__ == '__main__':

  import signal
  import sys
  def signal_handler(signum, frame):
    global keep_on_swimming
    debug(DEBUG_SIGNALS, 'Signal received!')
    keep_on_swimming = False
    button_main.stop()
    button_wifi.stop()
    button_router.stop()
    button_modem.stop()
    rgb_led_main.stop()
    rgb_led_wifi.stop()
    rgb_led_router.stop()
    rgb_led_modem.stop()
    sys.exit(0)
  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGQUIT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)

  # Always initialize the relay output pins to HIGH (on) at powerup
  GPIO.output(MY_RELAY_WIFI, GPIO.HIGH)
  GPIO.output(MY_RELAY_ROUTER, GPIO.HIGH)
  GPIO.output(MY_RELAY_MODEM, GPIO.HIGH)

  # Fan: (set initial value; change with: `fan_percent.ChangeDutyCycle(___)`
  fan_percent.start(50)

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

  # Create the RGB_LED objects
  rgb_led_main = RGB_LED("main", MY_LED_MAIN_RED, MY_LED_MAIN_GREEN, None)
  rgb_led_wifi = RGB_LED("wifi", MY_LED_WIFI_RED, MY_LED_WIFI_GREEN, None)
  rgb_led_router = RGB_LED("router", MY_LED_ROUTER_RED, MY_LED_ROUTER_GREEN, None)
  rgb_led_modem = RGB_LED("modem", MY_LED_MODEM_RED, MY_LED_MODEM_GREEN, None)

  # Monitor system status, and operate the status LEDs accordingly
  status = StatusThread()
  status.start()

  # Monitor the button objects, and act accordingly when they are pressed
  buttons = ButtonThread()
  buttons.start()

  # Prevent exit and operate the LED flasher
  while keep_on_swimming:
    RGB_LED.toggle_flash_state()
    time.sleep(0.5)

