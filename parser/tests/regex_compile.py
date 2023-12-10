import re

try:
    from ..main import INSTANCE_GROUPS
except ImportError:
    from parser.main import INSTANCE_GROUPS
from loguru import logger


if __name__ == '__main__':
    regex_instances = dict()
    for instance_group in INSTANCE_GROUPS:
        for instance in instance_group.instances:
            if hasattr(instance, "regex_pattern"):
                try:
                    re.compile(instance.regex_pattern, re.MULTILINE)
                    regex_instances[(instance_group.name, instance.relative_filepath_without_ext)] = True
                    logger.debug(f"{instance_group.name}/{instance.relative_filepath_without_ext} success!")
                except Exception as e:
                    regex_instances[(instance_group.name, instance.relative_filepath_without_ext)] = False
                    logger.error(f"{instance_group.name}/{instance.relative_filepath_without_ext} error! ({e})")
