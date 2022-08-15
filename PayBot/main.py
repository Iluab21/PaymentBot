import os
import server
import db
import asyncio
import logging

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)


token = os.getenv('TOKEN')
# Пробуем подгрузить инфу с прошлых запусков
m = 0
message = {}
db.init_table()


async def main():
    # Старт бота, старт таймера
    await botlogic.bot.start(bot_token=token)
    asyncio.ensure_future(timer())
    try:
        await botlogic.bot.run_until_disconnected()
    except Exception as err:
        logging.error(err, exc_info=True)
    finally:
        await botlogic.bot.disconnect()


async def timer():
    # Таймер отсчёта дней
    while True:
        db.daytimer()
        try:
            for i in db.days_are_over():
                await botlogic.remove_user_from_channel(int(i))
        except TypeError:
            pass
        await asyncio.sleep(86400)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
