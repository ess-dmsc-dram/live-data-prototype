import logging


def setup_global_logger(level='debug', rank=0):
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)

    formatter = logging.Formatter(fmt='%(asctime)s.%(msecs).03d - %(levelname)s - %(module)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    logger = logging.getLogger()

    if rank == 0:
        logger.setLevel(numeric_level)
    else:
        logger.setLevel(logging.WARNING)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


log = logging.getLogger()
