import asyncio
import os

from shikimori_extended_api import Client

APPLICATION_NAME = os.environ.get('APPLICATION_NAME')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')


async def main():
    # 1) Создать приложение на https://shikimori.me/oauth/applications
    # 2) Найти client_id и client_secret этого приложения https://shikimori.me/oauth

    shiki_api = Client(
        application_name=APPLICATION_NAME,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    # 3) Запросить у пользователя код авторизации, используя auth_url этого приложения

    code = input(f"Авторизайтесь на Shikimori по [ссылке]({shiki_api.auth_url}) и введите авторизационный код:")
    print('Введён код:', code)  # печатать не обязательно, здесь - просто для демонстрации

    # 4) С этим кодом нужно получить токен доступа и токен для обновления

    tokens = await shiki_api.get_access_token(code)
    print(tokens)  # печатать не обязательно, здесь - просто для демонстрации

    # 4.1) Их можно сохранить для дальнейшего использования любым удобным способом
    # ...

    # 5) Токен нужен для получения доступа к некоторым эндпоинтам, например:
    # GET /api/users/whoami - Show current user's brief info

    try:
        print(await shiki_api.go().users.whoami.get())
    except Exception as e:
        print(e)

        print(await shiki_api.go().users.whoami.get(headers={'Authorization': f'Bearer {shiki_api.access_token}'}))

    # или что то же самое

    print(await shiki_api.get_current_user_info())


if __name__ == '__main__':
    asyncio.run(main())
