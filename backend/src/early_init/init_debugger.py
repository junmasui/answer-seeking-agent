import os
import debugpy

if os.getenv('DEBUGGER_LISTEN', '').lower() in ['true', '1']:
    debugpy.listen(('0.0.0.0', 5678))
