import json
from fosspay.config import _cfg, load_config

def version():
    with open('VERSION') as f:
        data = f.read()
        return data
