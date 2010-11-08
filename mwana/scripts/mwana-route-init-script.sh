#!/bin/sh

# the following lines will be automatically populated with the correct
# project directory and user when the init script is deployed


### BEGIN INIT INFO
# Provides:          rapidsms daemon instance
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: starts instances of mwana rapidsms router
# Description:       starts instance of mwana rapidsms router using start-stop-daemon
### END INIT INFO

PROJECT_DIR=
CODE_ROOT=
VIRTUALENV_ROOT=
USER=

stop() {
        echo -n Stopping mwana route process...
        PID=`ps aux| grep "manage.py runrouter"| grep -v grep|awk '{print $2}'`
        if [ -n $PID ]; then
                kill $PID
        fi
        echo done.
}

start() {
        # unfortunately we don't know of a way to tell if the route process
        # started successfully
        echo -n Starting mwana route process...
        sudo -u $USER $VIRTUALENV_ROOT/bin/python $CODE_ROOT/mwana/manage.py runrouter > $PROJECT_DIR/route.log 2>&1 &
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
