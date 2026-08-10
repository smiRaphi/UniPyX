"""
Add this to your vscode settings file to use:
  "terminal.integrated.env.windows": {
    "PYTHONSTARTUP": "${workspaceFolder}/dev/startup.py"
  },
  "python.terminal.shellIntegration.enabled": false,
"""

import sys,os
sys.path.append(os.getcwd())
from lib.dldb import DLDB
db = DLDB()

def cls(): os.system('cls')
