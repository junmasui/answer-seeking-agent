import os

import debugpy

if os.getenv('DEBUGGER_LISTEN', '').lower() in ['true', '1']:
    host = os.getenv('DEBUGGER_LISTEN_HOST', '127.0.0.1')
    port = int(os.getenv('DEBUGGER_LISTEN_PORT', '5678'))
    debugpy.listen((host, port))
