import asyncio
import os

from shikimori_extended_api import Client

APPLICATION_NAME = os.environ.get('APPLICATION_NAME')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')


async def main():
    # 1) Создать приложение на https://shikimori.me/oauth/applications
    # 2) Найти `client_id` и `client_secret` этого приложения (https://shikimori.me/oauth)

    shiki_api = Client(
        application_name=APPLICATION_NAME,  # обязателен всегда
        client_id=CLIENT_ID,                # обязателен для получения токена
        client_secret=CLIENT_SECRET         # обязателен для получения токена
    )

    # 3) Запросить у пользователя код авторизации, используя auth_url этого приложения

    code = input(f"Авторизайтесь на Shikimori по [ссылке]({shiki_api.auth_url}) и введите авторизационный код:\n")

    # 4) С этим кодом нужно получить токен доступа и токен для обновления

    token = await shiki_api.get_access_token(code)
    print("Получены токены:", token)

    # 4.1) Их можно сохранить для дальнейшего использования любым удобным способом
    # ...

    # 5) Токен нужен для получения доступа к некоторым эндпоинтам, например:
    # GET /api/users/whoami - Информация о пользователе, который авторизовал приложение

    # Ничего не будет выведено, т.к. токен не указан
    print(await shiki_api.go().users.whoami.get())

    # А здесь информация будет получена успешно
    print(await shiki_api.go(token).users.whoami.get())

    # Или то же самое можно получить через встроенную функцию `get_current_user_info(token: ShikiToken)`
    print(await shiki_api.get_current_user_info(token))


if __name__ == '__main__':
    asyncio.run(main())
