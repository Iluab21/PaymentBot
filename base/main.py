import os
import config
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon import TelegramClient
from telethon import events
from telethon.tl.custom import Button
import telethon
import asyncio
from telethon.sessions import StringSession
import logging
from ast import literal_eval

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
token = os.getenv('TOKEN')
session = os.getenv('SESSION')
client = TelegramClient(StringSession(session), api_id, api_hash)
bot = TelegramClient('bot', api_id, api_hash)
# Пробуем подгрузить инфу с прошлых запусков
try:
    with open('back.txt', 'r', encoding='utf-8') as f:
        users_list = literal_eval(f.read())
except (EOFError, OSError, SyntaxError):
    users_list = {}
# Текстовый логгер ошибок
with open('logging.txt', 'w') as f:
    f.write('Exceptions log:')
m = 0
message = {}


async def invite_user_to_channel(users_to_add):
    # Добавление пользователя в чат

    async with TelegramClient(StringSession(session), api_id, api_hash) as client:
        try:
            await client.get_participants(config.open_channel)
            await client(InviteToChannelRequest(channel=config.channel, users=[users_to_add]))
        except ValueError:
            await bot.send_message(config.admin_id, 'Косяк ' + str(users_to_add))
            keyboard = [Button.inline('Назад', b'main')]
            await bot.send_message(users_to_add, 'Для того чтобы попасть в закрытый канал, вы должны быть подписчиком '
                                                 'канала t.me/ALGtrader', buttons=keyboard)
        except Exception as err:
            logging.error(err, exc_info=True)
            await bot.send_message(config.admin_id, str(err))


async def remove_user_from_channel(user):
    # Удаление пользователя из чата
    async with TelegramClient(StringSession(session), api_id, api_hash) as client:
        try:
            await client.get_participants(config.channel)
            await client.kick_participant(config.channel, user)
        except Exception as err:
            logging.error(err, exc_info=True)
            await bot.send_message(config.admin_id, str(err))


@bot.on(events.NewMessage(pattern='/start'))
async def starthandler(event):
    # Ответ на первый запуск бота. Добавление пользователя в базу, если его там нет.
    global m
    entity = await bot.get_entity(event.chat_id)
    if event.chat_id in users_list:
        keyboard = [Button.inline('Оплата', b'pay')], [Button.inline('Сколько дней подписки осталось?', b'check')], [
            Button.inline('Всё оплачено, добавьте меня', b'reinvite')]
        try:
            await bot.delete_messages(event.chat_id, message[event.chat_id])
        except (telethon.errors.MessageDeleteForbiddenError, KeyError):
            pass
        message[event.chat_id] = await bot.send_message(event.chat_id, 'Выбери, что ты хочешь сделать.',
                                                        buttons=keyboard)
    else:
        users_list[event.chat_id] = [config.trial_limit, entity.id, entity.first_name, entity.last_name, entity.username, 0]
        keyboard = [Button.inline('Оплата', b'pay')], [Button.inline('Сколько дней подписки осталось?', b'check')], [
            Button.inline('Всё оплачено, добавьте меня', b'reinvite')]
        try:
            await bot.delete_messages(event.chat_id, message[event.chat_id])
        except (telethon.errors.MessageDeleteForbiddenError, KeyError):
            pass
        message[event.chat_id] = await bot.send_message(event.chat_id,
                                                        'Привет! Я бот-менеджер для нашего торгового бота. Сейчас для '
                                                        'новичков есть ' +
                                                        str(users_list[event.chat_id][
                                                                0]) + 'бесплатных дней для ознакомления, мы уже '
                                                                      'добавляем тебя в чат) '
                                                                      '\nВыбери, что ты хочешь сделать.',
                                                        buttons=keyboard)
        is_participant = await asyncio.ensure_future(search_user_in_channel(event.chat_id))
        if is_participant:
            try:
                await bot.delete_messages(event.chat_id, message[event.chat_id])
            except (telethon.errors.MessageDeleteForbiddenError, KeyError):
                pass
            keyboard = [Button.inline('Назад', b'main')]
            message[event.chat_id] = await bot.send_message(event.chat_id, 'Вы уже в чате', buttons=keyboard)
        else:
            try:
                await bot.delete_messages(event.chat_id, message[event.chat_id])
            except (telethon.errors.MessageDeleteForbiddenError, KeyError):
                pass
            keyboard = [Button.inline('Оплата', b'pay')], [
                Button.inline('Сколько дней подписки осталось?', b'check')], [
                           Button.inline('Всё оплачено, добавьте меня', b'reinvite')]
            message[event.chat_id] = await bot.send_message(event.chat_id,
                                                            'Привет! Я бот-менеджер для нашего торгового бота. Сейчас '
                                                            'для '
                                                            ' новичков есть ' +
                                                            str(users_list[event.chat_id][
                                                                    0]) + 'бесплатных дней для ознакомления, мы уже '
                                                                          'добавляем тебя в чат) '
                                                                          '\nВыбери, что ты хочешь сделать.',
                                                            buttons=keyboard)
            await asyncio.ensure_future(invite_user_to_channel(event.chat_id))


@bot.on(events.CallbackQuery(data=b'check'))
async def days_left(event):
    global m
    print(users_list)
    # Проверка оставшейся подписки
    try:
        try:
            await bot.delete_messages(event.chat_id, message[event.chat_id])
        except (telethon.errors.MessageDeleteForbiddenError, KeyError):
            pass
        keyboard = [Button.inline('Назад', b'main')]
        message[event.chat_id] = await bot.send_message(event.chat_id, 'Осталось ' + str(users_list[event.chat_id][0]) + ' дней',
                                                        buttons=keyboard)
    except Exception as err:
        logging.error(err, exc_info=True)


@bot.on(events.CallbackQuery(data=b'reinvite'))
async def inviting(event):
    global m
    # Приглашение пользователя, если у него активна подписка, и его нет в чате. На случай случайного удаления
    try:
        await bot.delete_messages(event.chat_id, message[event.chat_id])
    except (telethon.errors.MessageDeleteForbiddenError, KeyError):
        pass
    if users_list[event.chat_id][0] > 0:
        is_participant = await asyncio.ensure_future(search_user_in_channel(event.chat_id))
        if is_participant:
            keyboard = [Button.inline('Назад', b'main')]
            message[event.chat_id] = await bot.send_message(event.chat_id, 'Вы уже в чате', buttons=keyboard)
        else:
            keyboard = [Button.inline('Назад', b'main')]
            message[event.chat_id] = await bot.send_message(event.chat_id, 'Добавляю', buttons=keyboard)
            await asyncio.ensure_future(invite_user_to_channel(event.chat_id))
    else:
        keyboard = [Button.inline('Назад', b'main')]
        message[event.chat_id] = await bot.send_message(event.chat_id, 'Ваша подписка неактивна', buttons=keyboard)


@bot.on(events.CallbackQuery(data=b'pay'))
async def quantity_selection(event):
    global m
    # Функция выбора количества месяцев для оплаты
    try:
        await bot.delete_messages(event.chat_id, message[event.chat_id])
    except (telethon.errors.MessageDeleteForbiddenError, KeyError):
        pass
    keyboard = [Button.inline('1', b'month_1'), Button.inline('2', b'month_2')], [Button.inline('3', b'month_3'),
                                                                                  Button.inline('6', b'month_6')], [
                   Button.inline('12', b'month_12'), Button.inline('Назад', b'main')]
    message[event.chat_id] = await bot.send_message(event.chat_id, 'Выберите количество месяцев на оплату',
                                                    buttons=keyboard)


@bot.on(events.CallbackQuery(pattern='(?i)month.+'))
async def pay_confirm(event):
    global m
    # Подтверждение от пользователя, о том что он перевел платёж
    try:
        await bot.delete_messages(event.chat_id, message[event.chat_id])
    except (telethon.errors.MessageDeleteForbiddenError, KeyError):
        pass
    keyboard = [Button.inline('Оплачено', b'payed')], [Button.inline('Назад', b'pay')]
    message[event.chat_id] = await bot.send_message(event.chat_id, "Для оплаты нужно:\n" + str(
        int(str(event.data)[8:-1]) * config.price + config.price_addition) + config.pay_message,
                                                    buttons=keyboard)
    users_list[event.chat_id][5] = int(str(event.data)[8:-1]) * 31


@bot.on(events.CallbackQuery(data=b'payed'))
async def payed(event):
    global m
    # Функция перевода на подтверждение платежа админом
    try:
        await bot.delete_messages(event.chat_id, message[event.chat_id])
    except (telethon.errors.MessageDeleteForbiddenError, KeyError):
        pass
    keyboard = [Button.inline('В главное меню', b'main')]
    message[event.chat_id] = await bot.send_message(event.chat_id,
                                                    'Сейчас мы проверим оплату и, если всё ок, в течение суток '
                                                    'добавим вас в канал',
                                                    buttons=keyboard)
    await asyncio.ensure_future(confirm(event.chat_id))


@bot.on(events.CallbackQuery(data=b'main'))
async def back(event):
    # Возвращение в главное меню
    global m
    await asyncio.ensure_future(starthandler(event))


async def confirm(userid):
    # Функция подтверждения оплаты от админа
    global m
    keyboard = [Button.inline('Подтвердить', data=str(userid))], [
        Button.inline('Не подтверждать', data='cancel' + str(userid))]
    admin_message = await bot.send_message(config.admin_id, 'Оплата ' + str(users_list[userid][5]) + ' дней\nПользователем: '
                                           + str(users_list[userid][1]) + ' ' + str(users_list[userid][2]) + ' ' +
                                           str(users_list[userid][3]) + ' ' + str(users_list[userid][4]), buttons=keyboard)

    @bot.on(events.CallbackQuery())
    async def confirmed(event):
        # Функция, вызывающаяся, после подтверждения о том, что админ увидел пришёдший платёж
        global m
        if event.chat_id == config.admin_id:
            if event.data == str(userid).encode():
                try:
                    await bot.delete_messages(userid, message[event.chat_id])
                except (telethon.errors.MessageDeleteForbiddenError, KeyError):
                    pass
                message[event.chat_id] = await bot.send_message(userid,
                                                                'Подписку подтвердили, если вас нет в канале, добавим)')
                try:
                    await bot.delete_messages(config.admin_id, admin_message)
                except (telethon.errors.MessageDeleteForbiddenError, KeyError):
                    pass
                users_list[userid][0] += users_list[userid][5]
                is_participant = await asyncio.ensure_future(search_user_in_channel(event.chat_id))
                if is_participant:
                    try:
                        await bot.delete_messages(userid, message[event.chat_id])
                    except (telethon.errors.MessageDeleteForbiddenError, KeyError):
                        pass
                    keyboard = [Button.inline('Назад', b'main')]
                    message[event.chat_id] = await bot.send_message(userid, 'Вы уже в чате', buttons=keyboard)
                else:
                    try:
                        await bot.delete_messages(userid, message[event.chat_id])
                    except (telethon.errors.MessageDeleteForbiddenError, KeyError):
                        pass
                    keyboard = [Button.inline('Назад', b'main')]
                    message[event.chat_id] = await bot.send_message(userid, 'Добавляю вас в чат', buttons=keyboard)
                    await asyncio.ensure_future(invite_user_to_channel(userid))
            if event.data == b'cancel' + str(userid).encode():
                keyboard = [Button.inline('Назад', b'main')]
                message[event.chat_id] = await bot.send_message(userid, 'Платёж не подтвеждён', buttons=keyboard)
                try:
                    await bot.delete_messages(config.admin_id, admin_message)
                except (telethon.errors.MessageDeleteForbiddenError, KeyError):
                    pass
                return False


async def search_user_in_channel(userid):
    # Функция поиска по пользователям канала
    users = await bot.get_participants(config.channel)
    participant = False
    for i in users:
        if userid == i.id:
            participant = True
        else:
            pass
    if participant:
        return True
    else:
        return False


async def main():
    # Старт бота, старт таймера
    await bot.start(bot_token=token)
    asyncio.ensure_future(timer())
    try:
        await bot.run_until_disconnected()
    except Exception as err:
        logging.error(err, exc_info=True)
        with open('logging.txt', 'a') as file:
            file.write('\n' + str(err))
    finally:
        await bot.disconnect()


async def timer():
    global users_list
    # Таймер отсчёта дней
    while True:
        await asyncio.sleep(86400)
        users = await bot.get_participants(config.channel)
        for i in users:
            try:
                if users_list[i.id][0] == 0:
                    asyncio.ensure_future(remove_user_from_channel(i.id))
                if users_list[i.id][0] > 0:
                    users_list[i.id][0] -= 1
                else:
                    pass
            except KeyError:
                pass
        # Чтобы информация сохранялась после перезапуска
        with open('back.txt', 'w') as file:
            file.write(str(users_list))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
