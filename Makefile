all: build run

# Define the GPIO pin numbers used by this hardware configuration

# LED GPIO numbers
MY_LED_MAIN_GREEN        := 25
MY_LED_MAIN_RED          := 21
MY_LED_WIFI_GREEN        := 14
MY_LED_WIFI_RED          := 15
MY_LED_ROUTER_GREEN      := 20
MY_LED_ROUTER_RED        := 16
MY_LED_MODEM_GREEN       := 8
MY_LED_MODEM_RED         := 7

# Solid State Relay GPIO numbers
MY_RELAY_WIFI            := 22
MY_RELAY_ROUTER          := 27
MY_RELAY_MODEM           := 17

# Push button switches
MY_BUTTON_MAIN           := 26
MY_BUTTON_WIFI           := 19
MY_BUTTON_ROUTER         := 13
MY_BUTTON_MODEM          := 6

# PWM fan control GPIO
MY_FAN_CONTROL_PWM       := 18

# IP addresses for My router, access point, and google's DNS
MY_ROUTER_IP             := 192.168.123.1
MY_WIFI_AP_IP            := 192.168.123.2
MY_OUTSIDE_IP            := darlingevil.com

# My WiFi SSIDs and the IP addresses of their monitors
MY_WIFI_MONITORS := '{ \
  "Bag End":     "192.168.123.201", \
  "Bagshot Row": "192.168.123.202", \
  "Hobbiton":    "192.168.123.203", \
  "The Shire":   "192.168.123.204" }'

build:
	docker build -t ibmosquito/mybox:1.0.0 .

# Running `make dev` will setup a working environment, just the way I like it.
# On entry to the container's bash shell, run `cd /outside/src` to work here.
dev: build
	-docker rm -f mybox 2> /dev/null || :
	docker run -it --name mybox \
            --privileged --restart unless-stopped \
            -e MY_LED_MAIN_GREEN=$(MY_LED_MAIN_GREEN) \
            -e MY_LED_MAIN_RED=$(MY_LED_MAIN_RED) \
            -e MY_LED_WIFI_GREEN=$(MY_LED_WIFI_GREEN) \
            -e MY_LED_WIFI_RED=$(MY_LED_WIFI_RED) \
            -e MY_LED_ROUTER_GREEN=$(MY_LED_ROUTER_GREEN) \
            -e MY_LED_ROUTER_RED=$(MY_LED_ROUTER_RED) \
            -e MY_LED_MODEM_GREEN=$(MY_LED_MODEM_GREEN) \
            -e MY_LED_MODEM_RED=$(MY_LED_MODEM_RED) \
            -e MY_RELAY_WIFI=$(MY_RELAY_WIFI) \
            -e MY_RELAY_ROUTER=$(MY_RELAY_ROUTER) \
            -e MY_RELAY_MODEM=$(MY_RELAY_MODEM) \
            -e MY_BUTTON_MAIN=$(MY_BUTTON_MAIN) \
            -e MY_BUTTON_WIFI=$(MY_BUTTON_WIFI) \
            -e MY_BUTTON_ROUTER=$(MY_BUTTON_ROUTER) \
            -e MY_BUTTON_MODEM=$(MY_BUTTON_MODEM) \
            -e MY_FAN_CONTROL_PWM=$(MY_FAN_CONTROL_PWM) \
            -e MY_ROUTER_IP=$(MY_ROUTER_IP) \
            -e MY_WIFI_AP_IP=$(MY_WIFI_AP_IP) \
            -e MY_OUTSIDE_IP=$(MY_OUTSIDE_IP) \
            -e MY_WIFI_MONITORS=$(MY_WIFI_MONITORS) \
            -p 8666:8666 \
            --volume /sys/class/thermal/thermal_zone0/temp:/cputemp \
            --volume `pwd`:/outside \
            ibmosquito/mybox:1.0.0 /bin/sh

# Run the container as a daemon (build not forecd here, sp must build it first)
run:
	-docker rm -f mybox 2> /dev/null || :
	docker run -d --name mybox \
            --privileged --restart unless-stopped \
            -e MY_LED_MAIN_GREEN=$(MY_LED_MAIN_GREEN) \
            -e MY_LED_MAIN_RED=$(MY_LED_MAIN_RED) \
            -e MY_LED_WIFI_GREEN=$(MY_LED_WIFI_GREEN) \
            -e MY_LED_WIFI_RED=$(MY_LED_WIFI_RED) \
            -e MY_LED_ROUTER_GREEN=$(MY_LED_ROUTER_GREEN) \
            -e MY_LED_ROUTER_RED=$(MY_LED_ROUTER_RED) \
            -e MY_LED_MODEM_GREEN=$(MY_LED_MODEM_GREEN) \
            -e MY_LED_MODEM_RED=$(MY_LED_MODEM_RED) \
            -e MY_RELAY_WIFI=$(MY_RELAY_WIFI) \
            -e MY_RELAY_ROUTER=$(MY_RELAY_ROUTER) \
            -e MY_RELAY_MODEM=$(MY_RELAY_MODEM) \
            -e MY_BUTTON_MAIN=$(MY_BUTTON_MAIN) \
            -e MY_BUTTON_WIFI=$(MY_BUTTON_WIFI) \
            -e MY_BUTTON_ROUTER=$(MY_BUTTON_ROUTER) \
            -e MY_BUTTON_MODEM=$(MY_BUTTON_MODEM) \
            -e MY_FAN_CONTROL_PWM=$(MY_FAN_CONTROL_PWM) \
            -e MY_ROUTER_IP=$(MY_ROUTER_IP) \
            -e MY_WIFI_AP_IP=$(MY_WIFI_AP_IP) \
            -e MY_OUTSIDE_IP=$(MY_OUTSIDE_IP) \
            -e MY_WIFI_MONITORS=$(MY_WIFI_MONITORS) \
            -p 8666:8666 \
            --volume /sys/class/thermal/thermal_zone0/temp:/cputemp \
            ibmosquito/mybox:1.0.0

status:
	curl -sS localhost:8666 | jq .

exec:
	docker exec -it mybox /bin/sh

push:
	docker push ibmosquito/mybox:1.0.0

stop:
	-docker rm -f mybox 2>/dev/null || :

clean: stop
	-docker rmi ibmosquito/mybox:1.0.0 2>/dev/null || :

.PHONY: all build dev run push exec stop clean

