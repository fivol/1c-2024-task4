import dataclasses
import socket
import sqlite3
from threading import Thread
import threading
from loguru import logger

from server.config import COMMANDS
from server.utils import StopServer


@dataclasses.dataclass
class Client:
    socket: socket.socket
    thread: threading.Thread
    host: str
    port: str

    def __repr__(self):
        return f'{self.host}:{self.port}'


class HogwartsExperimentServer:
    def __init__(self, host: str, port: int, max_connections, db_file: str):
        self._host = host
        self._port = port
        self._max_connections = max_connections
        self._db_file = db_file
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._db_conn = sqlite3.connect(self._db_file, check_same_thread=False)
        self._clients = []
        self._secret_number = None
        self._start_event = threading.Event()
        self._server_thread = None

    def _initialize_database(self):
        with self._db_conn:
            self._db_conn.execute('''CREATE TABLE IF NOT EXISTS participants (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            addr TEXT,
                            ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(addr)
                        )''')
            self._db_conn.execute('''CREATE TABLE IF NOT EXISTS attempts (
                            participant_id INTEGER,
                            value INTEGER,
                            ts DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (participant_id) REFERENCES participants(id)
                        )''')

    @classmethod
    def _send_message(cls, client, message: str):
        client.send(message.encode())
        assert 'ACK' == cls._wait_client(client)

    @classmethod
    def _wait_client(cls, client):
        return client.recv(1024).decode()

    def _handle_client(self, client_socket, addr):
        print(f'Новое подключение: {addr[0]}:{addr[1]}')
        cursor = self._db_conn.cursor()

        addr_name = f'{addr[0]}:{addr[1]}'
        cursor.execute('INSERT INTO participants (addr) VALUES (?)', (addr_name,))
        self._db_conn.commit()
        cursor.execute('SELECT id FROM participants WHERE addr = ?', (addr_name,))
        client_id = cursor.fetchone()[0]

        try:
            self._start_event.wait()
            self._send_message(client_socket, 'start')
            guessed = False

            while not guessed:
                try:
                    guess = self._wait_client(client_socket)
                    if not guess:
                        break
                    guess = int(guess)

                    cursor.execute('INSERT INTO attempts (participant_id, value) VALUES (?, ?)', (client_id, guess))
                    self._db_conn.commit()

                    if guess < self._secret_number:
                        response = 'less'
                    elif guess > self._secret_number:
                        response = 'grater'
                    else:
                        response = 'guessed'
                        guessed = True

                    self._send_message(client_socket, response)

                except ValueError:
                    self._send_message(client_socket, 'value_error')
                except Exception as e:
                    logger.exception("Client error")
                    print(f'Ошибка с клиентом {addr}: {e}')
                    break
        except (AssertionError, KeyboardInterrupt):
            logger.debug("Client disconnected")
            pass
        finally:
            print(f'Клиент {addr} отключился.')
            self._clients = [item for item in self._clients if item.socket != client_socket]
            self._db_conn.commit()
            client_socket.close()

    def _show_table(self, title: str, sql: str):
        print(title)
        with self._db_conn:
            cursor = self._db_conn.cursor()
            cursor.execute(sql)

        for i, row in enumerate(cursor.fetchall()):
            print(f'{i + 1}. {", ".join(map(str, row))}')
        print()

    def _handle_command(self, cmd: str):
        if cmd.startswith('start'):
            if self._start_event.is_set():
                print('Эксперимент уже идет\n')
                return
            try:
                self._secret_number = int(cmd.split(' ')[1])
                self._start_event.set()
                print('Эксперимент начался!')
            except (IndexError, ValueError):
                print('Введите целое число')

        elif cmd == 'list':
            print('Адреса участников:')
            print('\n'.join(map(str, self._clients)) or 'Участников пока нет')

        elif cmd == 'count':
            print('Активных учстников:', len(self._clients))

        elif cmd == 'exit':
            raise StopServer()

        elif cmd == 'help':
            print(COMMANDS)

        elif cmd == 'table':
            with self._db_conn:
                cursor = self._db_conn.cursor()
                cursor.execute('''
                    WITH IDS AS (
                        SELECT participant_id, COUNT(*) - 1 AS best_attempts
                        FROM attempts
                        GROUP BY participant_id
                        ORDER BY best_attempts ASC
                    )
                    SELECT participants.id, participants.addr, IDS.best_attempts
                    FROM participants
                    JOIN IDS ON IDS.participant_id = participants.id
                    ORDER BY best_attempts ASC
                    LIMIT 10
                ''')

                for i, (id_, addr, best_attempts) in enumerate(cursor.fetchall()):
                    print(f'{i + 1}. {addr} попыток: {best_attempts}')

        elif cmd == 'participants':
            self._show_table('Последние участники:',
                             '''SELECT addr, ts FROM PARTICIPANTS ORDER BY ts DESC limit 10'''
                             )

        else:
            print('Неизвестная команда')
        print()

    def _user_input(self):
        print(COMMANDS)
        print()
        try:
            while True:
                cmd = input('Введите команду: ')
                self._handle_command(cmd)
        except EOFError:
            return

    def _init_server(self):
        self._server_socket.bind((self._host, self._port))
        self._server_socket.listen(self._max_connections)
        print(f'Сервер запущен на {self._host}:{self._port}, ожидание подключений...')

    def _initialize(self):
        self._initialize_database()
        self._init_server()

    def _listen_clients(self):
        try:

            while True:
                client_socket, addr = self._server_socket.accept()
                client_thread = Thread(target=self._handle_client, args=(client_socket, addr))
                client_thread.start()
                client = Client(host=addr[0], port=addr[1], socket=client_socket, thread=client_thread)
                self._clients.append(client)
        except (KeyboardInterrupt, StopServer, ConnectionAbortedError):
            print('\nОстановка сервера...')

    def start_server(self):
        try:
            self._initialize()

            self._server_thread = Thread(target=self._listen_clients)
            self._server_thread.start()
            self._user_input()

        except (KeyboardInterrupt, StopServer):
            pass

        except Exception as e:  # noqa
            print('Ошибка', e)
            logger.exception('Server error')

        finally:
            self._finalize()

    def _finalize(self):
        self._server_socket.close()
        for client in self._clients:
            client.socket.close()
            client.thread.join()

        self._db_conn.close()
        self._server_thread and self._server_thread.join()
        print('Сервер остановлен.')
