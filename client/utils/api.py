import json
import typing
from urllib.parse import urljoin

from requests import Session

AuthData: typing.TypeAlias = tuple[str, str]
ResponseData: typing.TypeAlias = tuple[bool, dict]


class API:
    def __init__(self, api_endpoint: str, auth: AuthData | None = None):
        self.__api_url = api_endpoint

        self.__session = Session()
        self.__session.headers.update({'Content-Type': 'application/json'})

        if auth:
            self.__session.auth = auth

    @property
    def auth(self) -> AuthData:
        return self.__session.auth

    @auth.setter
    def auth(self, value: AuthData):
        self.__session.auth = value

    def connects(self) -> ResponseData:
        return self.__request(self.__session.get, 'connect/', 200)

    def connect_to_room(self, name: str, password: str) -> ResponseData:
        return self.__request(self.__session.post, 'connect/', 204, data=json.dumps({'room': name, 'password': password}))

    def create_room(self, name: str, password: str) -> ResponseData:
        return self.__request(self.__session.post, 'rooms/', 201, data=json.dumps({'name': name, 'password': password}))

    def rooms(self) -> ResponseData:
        return self.__request(self.__session.get, 'rooms/', 200)

    def register(self) -> ResponseData:
        return self.__request(self.__session.post, 'user/new/', 201, data=json.dumps({'username': self.auth[0], 'plain_password': self.auth[1]}))

    def user(self) -> ResponseData:
        return self.__request(self.__session.get, 'user/', 200)

    def apiuser(self) -> str | None:
        ok, data = self.user()
        return f'user{data['id']}' if ok else None

    def apiroom(self, room: str) -> str | None:
        ok, data = self.connects()
        if ok:
            for item in data:
                if item['name'] == room:
                    return f'room{item['id']}'
        return None

    def __request(self, action, suburl: str, ok_code: int = 200, **kwargs) -> ResponseData:
        response = action(urljoin(self.__api_url, suburl), **kwargs)
        return response.status_code == ok_code, json.loads(response.text) if response.text else {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.__session.__exit__(*args)
