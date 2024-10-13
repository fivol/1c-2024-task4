# Задача №4 / Системное программирование
**Реализация: Новичков Борис**

*Ученые из Хогвартса наконец-то решились на проведение масштабного научного
исследования для получения ответа на долго мучивший их вопрос - за какое
минимальное количество попыток возможно угадать некоторое число? Перед
выдвижением очередной гипотезы они решили провести несколько экспериментов,
в которых все желающие могут попробовать угадать некоторое число за как
можно меньшее количество попыток.*


## Установка
```
pip install poetry
poetry install
```

## Сервер

### Аргументы
- `--port`
- `--host`
- `--config`

### Пример запуска
```
python -m server.main --port 9090 --host 0.0.0.0
```

### Пример конфига
```ini
[server]
host = 0.0.0.0
port = 8888
max_connections = 10
db_file = experiment.db
```

## Клиент
### Пример запуска
### Аргументы
- `--port`
- `--host`
- `--config`

Все аргументы опциональные, можно ввести адрес сервера после запуска.
```
python -m client.main --port 9090 --host 0.0.0.0
```

### Пример конфига
```ini
[client]
host = 0.0.0.0
port = 8888
```