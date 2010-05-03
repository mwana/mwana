#!/bin/sh

stop() {
        echo -n Stopping mwana route process...
        PID=`ps aux|grep "manage.py route"|grep -v grep|awk '{print $2}'`
        if [ -n $PID ]; then
                kill $PID
        fi
        echo done.
}

start() {
        echo -n Starting mwana route process...
        sudo -u deployer /home/deployer/staging/mwana/manage.py route > /home/deployer/staging/route.log 2>&1 &
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
