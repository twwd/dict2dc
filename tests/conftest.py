import logging

LOG_FORMAT = "[%(asctime)s %(levelname)-s %(threadName)s %(name)s] %(message)s"

logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

collect_ignore = ["smoketest.py"]
