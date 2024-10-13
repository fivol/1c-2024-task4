import configparser

from loguru import logger

COMMANDS = """
Используйте следующие команды:
- start <number> для начала эксперимента...
- count для количества участников
- list для просмотра списка участников
- exit для завершения эксперимента
- help для отображения комманд
- table для просмотра таблицы лидеров"""


logger.remove()
logger.add("server.log")


def load_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)

    server_config = {
        'host': config.get('server', 'host', fallback='127.0.0.1'),
        'port': config.getint('server', 'port', fallback=9999),
        'max_connections': config.getint('server', 'max_connections', fallback=5),
        'db_file': config.get('server', 'db_file', fallback='experiment.db')
    }

    return server_config
