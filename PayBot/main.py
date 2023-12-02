import os
import server
import d
import asyncio
import logging

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)


token os.getenv('TOKEN')
m = 0
message = {}
db.init_table()


async def main():
    await server.bot.start(bot_token=token)
    asyncio.ensure_future(timer())
    try:
        await server.bot.run_until_disconnected()
    except Exception as err:
        logging.error(err, exc_info=True)
    finally:
        await server.bot.disconnect()


async def timer():
    # Таймер отсчёта дней
    while True:
        db.daytimer()
        try:
            for i in db.days_are_over():
                await server.remove_user_from_channel(int(i))
        except TypeError:
            pass
        await asyncio.sleep(86400)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
