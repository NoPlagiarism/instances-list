import os
from loguru import logger

HOME_PATH = os.path.dirname(os.path.dirname(__file__))


def get_bool_from_env(name: str, default: bool, log_value=True):
    val = os.environ.get(name, default=str(default)).lower() in ("1", "true", "t", "y", "yes", "ok", "on")
    if log_value:
        logger.info(name + "=" + str(val))
    return val


class Network:
    CLEARNET = "instances"
    ONION = "onion"
    I2P = "i2p"
    LOKI = "loki"


class MirrorHeaders:
    ONION = "onion-location"
    I2P = "x-i2p-location"


class Retries:
    max_ = 2
    sleep = 5
    sleep_multiplier = 0

    trace_errors = get_bool_from_env("FIL_TRACE_ERRORS", True)


INST_FOLDER = "instances"
