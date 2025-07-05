import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('bin',exist_ok=True)

from lib.dldb import DLDB

db = DLDB()

def analyze(inp:str):
    db.run(['trid'])
