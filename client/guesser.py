import socket

from loguru import logger

from .utils import StopClient, ServerError


class NumberGuesser:

    def __init__(self, host: str, port: int):
        self._host: str = host
        self._port: int = port
        self._guesses: list[int] = []
        self._client_socket = None

    @staticmethod
    def _input_value() -> int:
        while True:
            message = input('Введите ваше предположение (число) или "exit" для выхода: ')
            if message.lower() == 'exit':
                raise StopClient()
            try:
                return int(message)
            except ValueError:
                print('Не верный формат. Введите целое число и нажмите Enter')
                continue

    def _wait_message(self):
        response = self._client_socket.recv(1024).decode()
        self._send_message('ACK')
        return response

    def _send_message(self, message: str):
        return self._client_socket.send(message.encode())

    def _wait_experiment(self):
        print('Ожидание начала эксперимента...')

        if self._wait_message() == 'start':
            print('Эксперимент начался! Вы можете вводить свои предположения.')
        else:
            print('Получено неизвестное сообщение от сервера. Отключение.')
            raise ServerError()

    def _guess_number(self) -> bool:
        value = self._input_value()
        self._guesses.append(value)
        self._send_message(str(value))
        response = self._wait_message()
        if response == 'value_error':
            print('Не верный формат числа')
        elif response == 'less':
            print('Ваше число меньше загаданного')
        elif response == 'grater':
            print('Ваше число больше загаданного')
        elif response == 'guessed':
            print('Вы угадали!')
            print('Ваши предыдущие попытки:', ', '.join(map(str, self._guesses)))
            return True
        else:
            print('Неизвестный ответ от сервера')
            logger.error('Unknown server answer: {}', response)
        return False

    def _start_client(self):
        self._wait_experiment()
        while not self._guess_number():
            pass

    def _terminate_client(self):
        self._client_socket.close()

    def _connect_server(self):
        self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._client_socket.connect((self._host, self._port))
            print(f'Подключен к серверу {self._host}:{self._port}')
        except Exception:
            logger.exception('Failed to connect server')
            print(f'Не удалось подключиться к серверу {self._host}:{self._port}')
            raise StopClient()

    def start(self):
        try:
            self._connect_server()
            self._start_client()
        except (StopClient, KeyboardInterrupt):
            print('Завершение сеанса. Спасибо за участие!')
        except ServerError:
            pass
        except Exception:  # noqa
            logger.exception('Client exception')
        finally:
            self._terminate_client()
