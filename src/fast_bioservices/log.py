import logging

from fast_bioservices import settings

logger = logging.getLogger("fast_bioservices")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=settings.log_filepath,
)
