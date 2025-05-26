#!/usr/bin/env bash


# Error on unbound variables
set -u

echo "loading functions"

function wait_for_dependency_gate {
    SIGNAL_FILE="$1"

    echo "waiting for dependency gate to open.  ${SIGNAL_FILE}"


    WAIT_LIMIT=300
    WAIT_INTERVAL=5
    ELAPSED=0

    MESSAGE_INTERVAL=60
    NEXT_MESSAGE="$MESSAGE_INTERVAL"

    while [ ! -f "$SIGNAL_FILE" ]
    do
        if (( "$ELAPSED" > "$NEXT_MESSAGE" ))
        then
            echo "waiting for dependency gate to open."
            NEXT_MESSAGE=$(( NEXT_MESSAGE + MESSAGE_INTERVAL ))
        fi

        sleep "$WAIT_INTERVAL"
        # The $((...)) syntax is for shell arithematic operations.
        ELAPSED=$(( ELAPSED + WAIT_INTERVAL ))
        if [ "$ELAPSED" -ge "$WAIT_LIMIT" ]; then
            echo "dependency gate did not open within ${WAIT_LIMIT} seconds."
            exit 1
        fi
    done

    echo "detected opening of dependency gate."
}

#
function close_dependency_gate {
    echo "closing gate"

    # Parameter expansion explanation:
    #   ${variable%pattern}  removes the shortest match of pattern from the end
    #   /* is the pattern for "slash and anything after"
    #   
    SIGNAL_FILE="${1}"
    SIGNAL_DIR="${SIGNAL_FILE%/*}"

    if [ -f "$SIGNAL_FILE" ]
    then
        rm "$SIGNAL_FILE"
    else
        if [ ! -d "${SIGNAL_DIR}" ]
        then
            echo "WARNING!!  Shared directory ${SIGNAL_DIR} is missing!"
        fi
    fi
    echo "closed gate"
}

function open_dependency_gate {
    echo "opening gate"

    SIGNAL_FILE="${1}"

    date --iso-8601=seconds > "$SIGNAL_FILE"

    echo "opened gate"
}


