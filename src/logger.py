import logging
import sys
from config import VERBOSE, MODONLY
modDEBUG=11
logging.addLevelName(11, 'modDEBUG')

if VERBOSE and not MODONLY:
    LVL=logging.DEBUG
elif VERBOSE and MODONLY:
    LVL=11
elif not VERBOSE and MODONLY:
    LVL=logging.INFO
else:
    LVL=logging.ERROR

logging.basicConfig(stream=sys.stdout,level=LVL)
logger=logging.getLogger('Log')
logger.propagate=False

handler = logging.StreamHandler()
formatter = logging.Formatter('[%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)