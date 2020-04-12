all: build run

# Define the GPIO pin numbers used by this hardware configuration

# LED GPIO numbers
MY_LED_MAIN_GREEN        := 25
MY_LED_MAIN_RED          := 21
MY_LED_ROUTER_GREEN      := 20
MY_LED_ROUTER_RED        := 16
MY_LED_MODEM_GREEN       := 8
MY_LED_MODEM_RED         := 7

# Solid State Relay GPIO numbers
MY_RELAY_WIFI            := 17
MY_RELAY_ROUTER          := 27
MY_RELAY_MODEM           := 22

# Push button switches
MY_BUTTON_MAIN           := 26
MY_BUTTON_WIFI           := 19
MY_BUTTON_ROUTER         := 13
MY_BUTTON_MODEM          := 6

# PWM fan control GPIO
MY_FAN_CONTROL_PWM       := 18

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
            --volume /sys/class/thermal/thermal_zone0/temp:/cputemp \
            --volume `pwd`:/outside \
            ibmosquito/mybox:1.0.0 /bin/sh

# Run the container as a daemon (build not forecd here, sp must build it first)
run:
	-docker rm -f mybox 2> /dev/null || :
	docker run -it --name mybox \
            --privileged --restart unless-stopped \
            -e MY_LED_MAIN_GREEN=$(MY_LED_MAIN_GREEN) \
            -e MY_LED_MAIN_RED=$(MY_LED_MAIN_RED) \
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
            --volume /sys/class/thermal/thermal_zone0/temp:/cputemp \
            ibmosquito/mybox:1.0.0

exec:
	docker exec -it mybox /bin/sh

push:
	docker push ibmosquito/mybox:1.0.0

stop:
	-docker rm -f mybox 2>/dev/null || :

clean: stop
	-docker rmi ibmosquito/mybox:1.0.0 2>/dev/null || :

.PHONY: all build dev run push exec stop clean

