import argparse

from client.config import load_config
from client.guesser import NumberGuesser


def main():
    parser = argparse.ArgumentParser(description='Клиент для эксперимента Хогвартса.')
    parser.add_argument('--config', help='Путь к конфигурационному файлу', default='client_config.ini')
    parser.add_argument('--host', help='IP-адрес сервера')
    parser.add_argument('--port', type=int, help='Порт сервера')
    args = parser.parse_args()

    config = load_config(args.config)

    host = args.host if args.host else config.get('host')
    port = args.port if args.port else config.get('port')

    try:
        if not host:
            host = input('Введите IP-адрес сервера: ')
        if not port:
            port = int(input('Введите порт сервера: '))
    except ValueError:
        print('Неверный формат')
    except KeyboardInterrupt:
        print('До встречи!')

    client = NumberGuesser(host, port)
    client.start()


if __name__ == '__main__':
    main()
