import logging
import sys


def pytest_configure(config):
    logging.basicConfig(
        level=logging.DEBUG,
        format="\n%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
