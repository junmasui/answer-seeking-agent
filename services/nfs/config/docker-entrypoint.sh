#!/bin/bash
set -e

echo "=== NFS Ganesha Entrypoint Diagnostics ==="
echo "Checking /exports..."
ls -ld /exports
stat /exports || echo "WARN: stat /exports failed"

echo "Checking VFS FSAL library..."
find /usr -name "libfsalvfs.so*" 2>/dev/null || echo "WARN: libfsalvfs.so not found"

echo "Checking /etc/ganesha/ganesha.conf..."
test -f /etc/ganesha/ganesha.conf && echo "Config file exists" || echo "ERROR: Config file missing"

echo ""
echo "=== NOTE: DBus errors in containers are harmless and do not affect NFS functionality ==="
echo "NFS will continue to serve over TCP port 2049"
echo ""

mkdir -p /var/run/dbus
dbus-daemon --system --fork

mkdir -p /var/log/supervisor

echo "Performing initial sync..."
# Initial sync from Staging -> Exports to ensure export is populated before starting services
if [ -d "/staging" ]; then
    echo "Initializing /exports from /staging..."
    unison -batch -owner -group -numericids /staging /exports || echo "Initial sync warning"
else
    echo "WARN: /staging directory not found. Unison sync skipped."
fi

echo "Starting Supervisord..."
exec supervisord -c /etc/supervisor/conf.d/supervisord.conf
