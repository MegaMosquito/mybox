FROM arm32v6/python:3-alpine
WORKDIR /usr/src/app

# Install build tools
RUN apk --no-cache --update add gawk bc socat git gcc libc-dev linux-headers scons swig

# Install the python libraries
RUN pip install RPi.GPIO Flask requests

# Copy over the required files
COPY ./*.py /

# Run the daemon
WORKDIR /
CMD python /mybox.py

