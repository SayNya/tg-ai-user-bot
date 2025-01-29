import asyncio

import telethon

from src.data import config

# Название сессии
session = 'tester_bot'
# Api ID и Api Hash полученные на my.telegram.org
api_id = config.API_ID
api_hash = config.API_HASH

client = telethon.TelegramClient(config.SESSIONS_DIR / session, api_id, api_hash)


async def main():
    await client.connect()
    # Выводим в консоль данные о текущем пользователе, для проверки
    phone = input("Enter phone: ")
    await client.send_code_request(phone, force_sms=False)
    value = input("Enter login code: ")
    try:
        me = await client.sign_in(phone, code=value)
    except telethon.errors.SessionPasswordNeededError:
        password = input("Enter password: ")
        me = await client.sign_in(password=password)
    print(me)

if __name__ == '__main__':
    asyncio.run(main())