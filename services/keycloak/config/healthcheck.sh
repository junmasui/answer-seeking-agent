#!/bin/bash
exec 3<>/dev/tcp/localhost/9000
echo -e "GET /health/ready HTTP/1.1\r\nhost: localhost\r\nConnection: close\r\n\r\n" >&3
grep '"status".*"UP"' <&3
