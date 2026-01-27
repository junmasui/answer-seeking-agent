#!/bin/bash

# This script is a Supervisor event listener.
# It listens for PROCESS_STATE_EXITED events.
# If the process name matches "app", it sends SIGTERM to supervisord.

while true; do
    # Signal readiness
    printf "READY\n"

    # Read the header line
    if ! read -r line; then
        break
    fi

    # Parse length from header
    # Header format: ver:3.0 server:supervisor ... len:84
    len=$(echo "$line" | sed -n 's/.*len:\([0-9]*\).*/\1/p')

    # Read the payload
    if [ -n "$len" ]; then
        if ! read -r -N "$len" payload; then
            break
        fi
    fi

    # Check for PROCESS_STATE_EXITED and processname:app
    if [[ "$line" == *"eventname:PROCESS_STATE_EXITED"* ]]; then
        # We check if the processname in the payload is "app"
        if [[ "$payload" == *"processname:app"* ]]; then
             # Kill supervisor using the pid file.
             # This assumes supervisord runs as root or the same user.
             if [ -f /var/run/supervisord.pid ]; then
                 kill -SIGTERM $(cat /var/run/supervisord.pid)
             else
                 # Fallback if pidfile missing (unlikely if configured)
                 pkill -SIGTERM supervisord
             fi
        fi
    fi

    # Acknowledge the event
    printf "RESULT 2\nOK"
done
