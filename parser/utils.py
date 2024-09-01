import os

from loguru import logger

try:
    from .consts import Regex, HOME_PATH
except ImportError:
    from consts import Regex, HOME_PATH


CONSTS_FILE = os.path.join(HOME_PATH, "parser", "consts.py")


def add_regex_to_comments():
    with open(CONSTS_FILE, mode="r") as f:
        data = f.read()
    data_start = data.find("# ---BEGIN: REGEX---") + len("# ---BEGIN: REGEX---")
    data_end = data.find("# ---END: REGEX---")
    if not (data_start and data_end):
        logger.warning("Regex comment not found")
        return
    regex_dict = dict(filter(lambda x: x[0].startswith("DOMAIN") and x[0] != "DOMAIN_BASE_REGEX", Regex.__dict__.items()))
    regex_coms = [f"    # {k} - {v}" for k, v in regex_dict.items()]
    data = data[:data_start] + "\n" + "\n".join(regex_coms) + "\n    " + data[data_end:]
    with open(CONSTS_FILE, mode="w+") as f:
        f.write(data)
    logger.info("Regex comments created")


if __name__ == '__main__':
    add_regex_to_comments()
