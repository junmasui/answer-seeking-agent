import sys
import urllib.request

u='http://localhost:3000/health?check=full'
r=urllib.request.Request(u)
try:
    resp=urllib.request.urlopen(r)
    sys.exit(0) if resp.status==200 else sys.exit(255)
except Exception:
    sys.exit(255)

