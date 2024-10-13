import configparser

from loguru import logger

logger.remove()
logger.add('client.log')


def load_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    try:
        client_config = {
            'host': config.get('client', 'host'),
            'port': config.getint('client', 'port')
        }
    except configparser.NoSectionError:
        client_config = {}

    return client_config
