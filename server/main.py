import argparse

from .config import load_config
from .experiment import HogwartsExperimentServer


def main():
    parser = argparse.ArgumentParser(description='Сервер для эксперимента Хогвартса.')
    parser.add_argument('--config', help='Путь к конфигурационному файлу', default='server_config.ini')
    parser.add_argument('--host', help='IP-адрес для запуска сервера')
    parser.add_argument('--port', type=int, help='Порт для запуска сервера')
    parser.add_argument('--max_connections', type=int, help='Максимальное количество подключений')
    parser.add_argument('--db_file', help='Путь к файлу базы данных')
    args = parser.parse_args()

    config = load_config(args.config)

    host = args.host if args.host else config['host']
    port = args.port if args.port else config['port']
    max_connections = args.max_connections if args.max_connections else config['max_connections']
    db_file = args.db_file if args.db_file else config['db_file']

    server = HogwartsExperimentServer(host=host, port=port, max_connections=max_connections, db_file=db_file)
    server.start_server()


if __name__ == '__main__':
    main()
