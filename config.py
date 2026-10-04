"""Configuration for kalufs-kepubify.

May be overridden by instance/config.py.
"""

from pathlib import Path

# The log folder location
LOG_DIR = Path(__file__).parent / "logs"

# Set log level to debug
DEBUG = True

# Set to True to reload templates on every request
TEMPLATES_AUTO_RELOAD = True

# Generate with os.urandom(24)
SECRET_KEY = "SUPERSECRETKEY"

# Needed if application is not mounted in root
APPLICATION_ROOT = ""

# kepubify binary
KEPUBIFY_PATH = Path(__file__).parent / "instance" / "kepubify-linux-64bit"

# Dir for temporary file storage
TMP_DIR = Path(__file__).parent / "instance" / "tmp"
