import logging


def setup_global_logger(rank=0):
    formatter = logging.Formatter(fmt='%(asctime)s.%(msecs).03d - %(levelname)s - %(module)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    logger = logging.getLogger()

    if rank == 0:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


log = logging.getLogger()
