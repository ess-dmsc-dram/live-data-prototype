import logging


def setup_global_logger(rank):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    logger = logging.getLogger()

    if rank == 0:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
