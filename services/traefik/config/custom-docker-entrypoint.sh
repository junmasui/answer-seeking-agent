#!/usr/bin/env sh

set -e  # Exit immediately on error.

# Volume initialization logic (must run as root)
echo "Initializing volumes..."
for VOL in /acme
do
  if [ -d "$VOL" ]; then
    if [ ! -f "$VOL/.initialized" ]; then
      echo "Initializing $VOL..."
      touch "$VOL/.initialized"
      touch "$VOL/acme.json"
      chown -R 1000:1000 "$VOL"
      chmod -R 600 "$VOL"
      ls -ld "$VOL"
    else
      echo "$VOL is already initialized."
    fi
  else
    echo "Warning: Volume directory $VOL not found."
  fi
done

# Transition to the non-privileged entrypoint
echo "Dropping privileges to 1000:1000..."
exec gosu 1000:1000 /custom-docker-entrypoint-nonpriv.sh "$@"
