import getpass
import sys
from collections.abc import Callable

import config
from utils.api import API

api = API(config.API_URL)


def register():
    """ Зарегестрировать пользователя """

    ok, data = api.register()
    if ok:
        print('ID:', data['id'])
    else:
        print('Error:', data)

def login():
    """ Указать логин и пароль """

    api.auth = (input("Login: "), getpass.getpass())

def myid():
    """ Получить ID """

    ok, data = api.user()
    if ok:
        print('ID:', data['id'])
    else:
        print('Error:', data)

def rooms():
    """ Получить созданные комнаты """

    ok, data = api.rooms()
    if ok:
        for room in data['results']:
            room_id = int(room['url'].split('/')[-2])
            print(room_id, room['name'])
    else:
        print('Error:', data)

def new_room():
    """ Создать комнату """

    ok, data = api.create_room(input('Room name: '), getpass.getpass())
    if ok:
        print("Created:", data['name'])
    else:
        print('Error', data)

def connect_room():
    """ Присоединиться к чужой комнате """

    ok, data = api.connect_to_room(input('Room name: '), getpass.getpass())
    if ok:
        print("Connected")
    else:
        print('Error', data)

def connects():
    """ Получить комнаты, к которым вы присоединились """

    ok, data = api.connects()
    if ok:
        for item in data:
            print(item['id'], item['name'])
    else:
        print('Error', data)

def _help():
    """ Справка по командам """

    print(f"--- {_help.__doc__} ---")
    for cmd, func in commands.items():
        print(f'{cmd}:{func.__doc__}')

def _exit():
    """ Завершить программу """
    exit(0)


commands: dict[str, Callable[[], None]] = {
    'login': login,
    'reg': register,
    'myid': myid,
    'rooms created': rooms,
    'rooms create': new_room,
    'rooms add': connect_room,
    'rooms added': connects,
    'help': _help,
    'exit': _exit,
}

def main():
    with api:
        args = sys.argv[1:]
        if args:
            for f in args:
                if f in commands:
                    commands[f]()
                else:
                    print(f"{f}: unknown command")
            return

        _help()
        print()
        myid()

        while True:
            command = input('> ').strip()

            if command in commands:
                commands[command]()
            else:
                print('unknown command')


if __name__ == '__main__':
    if not hasattr(config, 'USER'):
        setattr(config, 'USER', input("User: "))
    if not hasattr(config, 'PASSWORD'):
        setattr(config, 'PASSWORD', getpass.getpass())

    api.auth = (config.USER, config.PASSWORD)
    main()
