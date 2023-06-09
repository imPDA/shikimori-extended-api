from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from urllib.parse import urlencode

import aiohttp
from aiohttp.web_exceptions import HTTPUnauthorized, HTTPTooManyRequests

from .limiter import Limiter
from .enums import Status
from .datatypes import ShikiToken

SHIKIMORI_URL = 'https://shikimori.me'

AUTH_ENDPOINT = SHIKIMORI_URL + '/oauth/authorize'
GET_TOKEN_ENDPOINT = SHIKIMORI_URL + '/oauth/token'
API_ROOT = SHIKIMORI_URL + '/api'


class ShikimoriExtendedAPI:
    limiter_5rps = Limiter(5, 1, name="5rps")
    limiter_90rpm = Limiter(90, 60, name="90rpm")

    def __init__(
            self,
            *,
            application_name: str,
            client_id: str = None,
            client_secret: str = None,
            redirect_uri: str = 'urn:ietf:wg:oauth:2.0:oob'
    ):
        self.application_name = application_name
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @property
    def auth_url(self):
        q = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': ''
        }
        return f"{AUTH_ENDPOINT}?{urlencode(q)}"

    @limiter_5rps
    @limiter_90rpm
    async def request(
            self,
            method: str,
            url: str,
            *,
            session: aiohttp.ClientSession = None,
            headers: dict = None,
            **kwargs,
    ):
        # print(f"[{datetime.now()}] {method} {url} {headers} {kwargs}")  # TODO logging
        headers_ = {'User-Agent': self.application_name}
        headers and headers_.update(headers)  # ...IS THIS LEGAL... ?
        session = session or aiohttp.ClientSession(headers=headers_)
        async with session:
            async with session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()

                # 429 Too Many Requests
                response.raise_for_status()

    def go(self, token: ShikiToken = None):
        return Builder(self, API_ROOT)(headers=token and {'Authorization': f'Bearer {token.access_token}'})

    async def get_access_token(self, auth_code: str) -> ShikiToken:
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': auth_code,
            'redirect_uri': self.redirect_uri
        }
        json_response = await self.request('POST', GET_TOKEN_ENDPOINT, data=data)

        return ShikiToken(
            access_token=json_response['access_token'] if isinstance(json_response['access_token'], str) else json_response['access_token'][0],
            refresh_token=json_response['refresh_token'],
            expires_in=timedelta(days=1),
            expires_at=datetime.now() + timedelta(days=1)
        )

    async def get_current_user_info(self, token: ShikiToken) -> dict:
        try:
            info = await self.go(token).users.whoami.get()
        except HTTPUnauthorized:
            await self.refresh_tokens()
            info = await self.go(token).users.whoami.get()

        return info

    async def get_user_info(self, user_id: int) -> dict:
        return await self.go().users.id(user_id).info.get()

    async def get_all_user_anime_rates(
            self,
            user_id: int,
            *,
            status: Status | str = None,
            censored: bool = None
    ) -> list:
        if isinstance(status, str):
            status = Status(status)

        L, p, rates = 100, 1, []  # limit per request, current page, list of rates
        while True:
            r_ = await self.go().users.id(user_id).anime_rates(limit=L, status=status.value, censored=censored, page=p)\
                .get()
            rates.extend(r_[:L])
            if len(r_) <= L:
                return rates
            p += 1

    async def get_anime(self, anime_id: int):
        return await self.go().animes.id(anime_id)

    async def __request_again_on_2_many_requests_ex(self, request, retries: int = 0) -> dict:
        MAX_RETRIES = 3
        if retries >= MAX_RETRIES:
            raise Exception(f"Too Many Requests: {MAX_RETRIES} retries")

        try:
            return await request()
        except HTTPTooManyRequests:
            return await self.__request_again_on_2_many_requests_ex(request, retries + 1)

    # WATCH OwUT !!! IT TAKES a SUwUPER LOwONG TIME
    async def fetch_total_watch_time(self, user_id: int) -> float:
        titles = await self.get_all_user_anime_rates(user_id)
        tasks = []
        async with asyncio.TaskGroup() as group:
            for title in titles:
                anime_info = group.create_task(
                    self.__request_again_on_2_many_requests_ex(self.go().animes.id(title['anime']['id']).get),
                    name=f"ID{title['anime']['id']}"
                )
                tasks.append(anime_info)

        durations = [task.result()['duration'] or 23 for task in tasks]  # 23  <_<?
        amount_of_episodes = [title['episodes'] for title in titles]
        return sum([duration * episodes for duration, episodes in zip(durations, amount_of_episodes)])

    def log_in(self, login: str, password: str):
        raise NotImplementedError

    async def refresh_tokens(self):
        raise NotImplementedError


Client = ShikimoriExtendedAPI


class Builder:
    def is_endpoint_exists(self) -> bool:
        resources = {
            'achievements': None,
            'animes': {
                False: {
                    '': {},
                },
                True: {
                    '': {},
                    'roles': {},
                    'similar': {},
                    'related': {},
                    'screenshots': {},
                    'franchise': {},
                    'external_links': {},
                    'topics': {},
                },
            },
            'users': {
                False: {
                    '': {},
                    'whoami': {},
                    'sign_out': {},
                },
                True: {
                    '': {},
                    'info': {},
                    'friends': {},
                    'clubs': {},
                    'anime_rates': {},
                    'manga_rates': {},
                    'favourites': {},
                    'messages': {},
                    'unread_messages': {},
                    'history': {},
                    'bans': {},
                }
            }
        }

        pattern = r'https:\/\/shikimori\.me\/api\/([a-z_]*)(?:\/(\d+))?(?:\/([a-z_]*))?'
        groups = re.match(pattern, self.url).groups()
        resource = groups[0]
        id_ = bool(groups[1])
        path = groups[2] if groups[2] else ''
        try:
            flag = path in resources[resource][id_]
        except KeyError as e:
            raise KeyError(f'Не найдено пути: {e}')
        else:
            if not flag:
                raise KeyError(f'Не найдено пути: {path}')

        return True

    def __init__(self, client: Client, root: str = None):
        self.client = client
        self.url = root
        self.params = {}
        self.headers = {}
        self.method: str = ''

    def __getattr__(self, item: str):
        match item.lower():
            case 'get' | 'post' | 'patch' | 'put' | 'delete':  # HEAD, CONNECT, OPTIONS, TRACE
                self.method = item.upper()
            case 'id':
                pass
            case _:
                self.url += f'/{item}'

        return self.__dict__.get(item, self)

    def __call__(self, some_id: int = None, **params) -> Client.request:
        if some_id:
            if not isinstance(some_id, int):
                return ValueError("ID must be an integer!")
            self.url += f'/{some_id}'

        params = {k: v for k, v in params.items() if v}  # delete empty params first

        session = params.pop('session', None)
        self.headers.update(params.pop('headers', {}))
        self.params.update(params)

        if self.method:
            # if not self.is_endpoint_exists():
            #     raise
            return self.client.request(
                self.method,
                self.url,
                session=session or None,
                headers=self.headers or None,
                params=self.params or None,
            )
        else:
            return self
