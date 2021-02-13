"""Configuration for kalufs-kepubify.

May be overridden by instance/config.py.
"""

import os

# The log folder location
LOG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "logs")

# Set log level to debug
DEBUG = True
TEMPLATES_AUTO_RELOAD = True

# Generate with os.urandom(24)
SECRET_KEY = "SUPERSECRETKEY"

# Needed if application is not mounted in root
APPLICATION_ROOT = ""

# kepubify config
KEPUBIFY_PATH = "/home/anne/projects/kalufs-kepubify/instance/kepubify-linux-64bit"
