#!/bin/bash
exec 3<>/dev/tcp/127.0.0.1/9000
echo -e "GET /health/ready HTTP/1.1\r\nhost: 127.0.0.1\r\nConnection: close\r\n\r\n" >&3
grep '"status".*"UP"' <&3
