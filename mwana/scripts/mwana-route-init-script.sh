#!/bin/sh

# the following lines will be automatically populated with the correct
# project directory and user when the init script is deployed
PROJECT_DIR=
USER=

stop() {
        echo -n Stopping mwana route process...
        PID=`ps aux|grep "manage.py route"|grep -v grep|awk '{print $2}'`
        if [ -n $PID ]; then
                kill $PID
        fi
        echo done.
}

start() {
        # unfortunately we don't know of a way to tell if the route process
        # started successfully
        echo -n Starting mwana route process...
        sudo -u $USER $PROJECT_DIR/mwana/manage.py route > $PROJECT_DIR/route.log 2>&1 &
        echo done.
}

if [ "x$1" = "xstart" ]; then
        start
elif [ "x$1" = "xstop" ]; then
        stop
elif [ "x$1" = "xrestart" ]; then
        stop
        start
fi
