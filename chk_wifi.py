#
# Code to check the state of the current wifi SSIDs
#
# Written by Glen Darling, July 2020.
#


import json
import requests
import threading
import time


# Debug flags
DEBUG_WIFI = False

# Debug print
def debug(flag, str):
  if flag:
    print(str)


# Class to monitor wifi
REQUEST_TIMEOUT_SEC = 10
SLEEP_BETWEEN_WIFI_CHECKS_SEC = 0.25
class WiFiMonitor(threading.Thread):

  def __init__(self, wifis):
    threading.Thread.__init__(self)
    self._wifis = wifis
    self._lasts = {}
    for ssid in self._wifis.keys():
      addr = self._wifis[ssid]
      self._lasts[addr] = 0
      debug(DEBUG_WIFI, ('--> "%s": "%s"' % (ssid, addr)))
    self._keep_swimming = True
    self.start()

  def last_good_status(self):
    longest = 0
    which = None
    for addr in self._lasts.keys():
      t = time.time() - self._lasts[addr]
      debug(DEBUG_WIFI, ('--> "%s": t=%0.1fs' % (addr, t)))
      if t > longest:
        longest = t
        which = addr
    debug(DEBUG_WIFI, ('<-- last: %0.1f (t=%0.1fs)' % (self._lasts[addr], longest)))
    return self._lasts[addr]

  def details(self):
    j = dict()
    for ssid in self._wifis.keys():
      addr = self._wifis[ssid]
      j[ssid] = dict()
      j[ssid]['addr'] = addr
      j[ssid]['last'] = time.time() - self._lasts[addr]
    debug(DEBUG_WIFI, ('<-- details: %s' % (json.dumps(j))))
    return (json.dumps(j) + '\n').encode('UTF-8')

  def stop(self):
    self._keep_swimming = False

  def run(self):
    debug(DEBUG_WIFI, "WiFi monitor is online.")
    while self._keep_swimming:
      for k in self._wifis.keys():
        addr = self._wifis[k]
        url = 'http://' + addr + '/'
        try:
          r = requests.get(url, timeout=REQUEST_TIMEOUT_SEC)
          if 200 == r.status_code:
            self._lasts[addr] = time.time()
            debug(DEBUG_WIFI, ('--> "%s" [UP]' % (addr)))
          else:
            debug(DEBUG_WIFI, ('--> "%s" [DN]' % (addr)))
        except requests.exceptions.Timeout:
          debug(DEBUG_WIFI, ('--> "%s" [TO]' % (addr)))
        except:
          debug(DEBUG_WIFI, ('--> "%s" [ER]' % (addr)))
      time.sleep(SLEEP_BETWEEN_WIFI_CHECKS_SEC)



