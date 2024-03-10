import os
import logging

# retrieve the logging level from an environment variable
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()

# create a logger
logger = logging.getLogger(__name__)
logger.setLevel(log_level)

# create a console handler
handler = logging.StreamHandler()
handler.setLevel(log_level)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(pathname)s:%(lineno)d - %(funcName)s - %(levelname)s - %(message)s')
# formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)
