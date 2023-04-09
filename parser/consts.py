import os

HOME_PATH = os.path.dirname(os.path.dirname(__file__))


class Network:
    CLEARNET = "instances"
    ONION = "onion"
    I2P = "i2p"
    LOKI = "loki"


class MirrorHeaders:
    ONION = "onion-location"
    I2P = "x-i2p-location"


INST_FOLDER = "instances"
