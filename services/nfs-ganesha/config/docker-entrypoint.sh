#!/bin/bash
set -e

apt update
apt-get install -y psmisc net-tools

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

echo "Starting rpcbind..."
rpcbind

echo "Starting ganesha.nfsd..."
exec ganesha.nfsd "$@"
