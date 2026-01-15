#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Volume initialization logic (must run as root)
echo "Initializing volumes..."
for VOL in /data
do
  if [ -d "$VOL" ]; then
    if [ ! -f "$VOL/.initialized" ]; then
      echo "Initializing $VOL..."
      touch "$VOL/.initialized"
      chown -R 999:999 "$VOL"
      chmod -R 777 "$VOL"
      ls -ld "$VOL"
    else
      echo "$VOL is already initialized."
    fi
  else
    echo "Warning: Volume directory $VOL not found."
  fi
done

# Transition to the non-privileged entrypoint
echo "Dropping privileges to redis..."
exec gosu redis /custom-docker-entrypoint-nonpriv.sh "$@"
