#!/usr/bin/env bash

##set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

GPU_MODE=""

# Parse GNU-style long options
while [[ $# -gt 0 ]]; do
  case "$1" in
    --gpu-mode=* )
      GPU_MODE="${1#*=}"
      ;;
    # Add more long options here as needed
    * )
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
  shift
done

if [ -z "${GPU_MODE:-}" ]; then
    echo "GPU mode missing"
    exit 1
elif [ "$GPU_MODE" == "cuda13" ]; then
    export COMPOSE_FILE=common.compose.yml:cuda.compose.yml
elif [ "$GPU_MODE" == "cpu" ]; then
    export COMPOSE_FILE=common.compose.yml:cpu-only.compose.yml
else
    echo "invalid GPU mode: ${GPU_MODE}"
    exit 1
fi


# Start up the system.
#
MAX_RETRIES=15
BACKOFF=1.5

# Infrastructure
#
echo Launching infrastructure
docker compose --profile infrastructure up -d
if [ $? -ne 0 ]
then
    exit "$?"
fi

SLEEP_TIME=2
for LOOP in $(seq 1 "$MAX_RETRIES")
do
    ./scripts/display_processes.sh --gpu-mode=$GPU_MODE
    if [ $? -eq 0 ]
    then
        break
    fi
    echo Give $SLEEP_TIME seconds for infrastructure
    sleep "$SLEEP_TIME"
    SLEEP_TIME=$( echo "$BACKOFF * $SLEEP_TIME" | bc )
done
if [ $? -ne 0 ]
then
    exit "$?"
fi


# Backup
#
echo Launching backend
docker compose --profile backend up -d
if [ $? -ne 0 ]
then
    exit "$?"
fi

SLEEP_TIME=2
for LOOP in $(seq 1 "$MAX_RETRIES")
do
    ./scripts/display_processes.sh --gpu-mode=$GPU_MODE
    if [ $? -eq 0 ]
    then
        break
    fi
    echo Give $SLEEP_TIME seconds for backend
    sleep "$SLEEP_TIME"
    SLEEP_TIME=$( echo "$BACKOFF * $SLEEP_TIME" | bc )
done
if [ $? -ne 0 ]
then
    exit "$?"
fi

# Backup Autotest
#
echo Launching backend-autotest
docker compose --profile backend-autotest up -d
if [ $? -ne 0 ]
then
    exit "$?"
fi

SLEEP_TIME=2
for LOOP in $(seq 1 "$MAX_RETRIES")
do
    ./scripts/display_processes.sh --gpu-mode=$GPU_MODE
    if [ $? -eq 0 ]
    then
        break
    fi
    echo Give $SLEEP_TIME seconds for backend-autotest
    sleep "$SLEEP_TIME"
    SLEEP_TIME=$( echo "$BACKOFF * $SLEEP_TIME" | bc )
done
if [ $? -ne 0 ]
then
    exit "$?"
fi

# Frontend
#
echo Launching frontend
docker compose --profile frontend up -d
if [ $? -ne 0 ]
then
    exit "$?"
fi

SLEEP_TIME=2
for LOOP in $(seq 1 "$MAX_RETRIES")
do
    ./scripts/display_processes.sh --gpu-mode=$GPU_MODE
    if [ $? -eq 0 ]
    then
        break
    fi
    echo Give $SLEEP_TIME seconds for frontend
    sleep "$SLEEP_TIME"
    SLEEP_TIME=$( echo "$BACKOFF * $SLEEP_TIME" | bc )
done
if [ $? -ne 0 ]
then
    exit "$?"
fi

# Frontend Autotest
#
echo Launching frontend-autotest
docker compose --profile frontend-autotest up -d
if [ $? -ne 0 ]
then
    exit "$?"
fi

SLEEP_TIME=2
for LOOP in $(seq 1 "$MAX_RETRIES")
do
    ./scripts/display_processes.sh --gpu-mode=$GPU_MODE
    if [ $? -eq 0 ]
    then
        break
    fi
    echo Give $SLEEP_TIME seconds for frontend-autotest
    sleep "$SLEEP_TIME"
    SLEEP_TIME=$( echo "$BACKOFF * $SLEEP_TIME" | bc )
done
if [ $? -ne 0 ]
then
    exit "$?"
fi

# Dev Tools
#
echo Launching dev-tools
docker compose --profile dev-tools up -d
if [ $? -ne 0 ]
then
    exit "$?"
fi

SLEEP_TIME=2
for LOOP in $(seq 1 "$MAX_RETRIES")
do
    ./scripts/display_processes.sh --gpu-mode=$GPU_MODE
    if [ $? -eq 0 ]
    then
        break
    fi
    echo Give $SLEEP_TIME seconds for dev-tools
    sleep "$SLEEP_TIME"
    SLEEP_TIME=$( echo "$BACKOFF * $SLEEP_TIME" | bc )
done
if [ $? -ne 0 ]
then
    exit "$?"
fi
