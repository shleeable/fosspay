import logging
import signal

try:
    from configparser import ConfigParser
except ImportError:
    # Python 2 support
    from ConfigParser import ConfigParser

logger = logging.getLogger("fosspay")
logger.setLevel(logging.DEBUG)

sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)

logger.addHandler(sh)

# scss logger
logging.getLogger("scss").addHandler(sh)

env = 'dev'
config = None

def load_config():
    global config
    config = ConfigParser()
    config.readfp(open('config.ini'))
    try:
        signal.signal(signal.SIGHUP, lambda *args: load_config())
    except ValueError as e:
        logger.warn(e)

load_config()

_cfg = lambda k: config.get(env, k)
_cfgi = lambda k: int(_cfg(k))
