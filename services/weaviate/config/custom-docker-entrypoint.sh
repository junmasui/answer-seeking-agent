#!/usr/bin/env sh

set -e  # Exit immediately on error.

# Volume initialization logic (must run as root)
echo "Initializing volumes..."
for VOL in /var/lib/weaviate
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
echo "Dropping privileges to weaviate (UID 999)..."
exec gosu 999:999 /custom-docker-entrypoint-nonpriv.sh "$@"
