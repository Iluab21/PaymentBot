import telethon
import config
import os
import db
import logging
from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon import events
from telethon.tl.custom import Button
from telethon.sessions import StringSession

token = os.getenv('TOKEN')
session = os.getenv('SESSION')
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
bot = TelegramClient('bot', api_id, api_hash)
message = []


async def delete_message(event):
    try:
        await bot.delete_messages(event.chat_id, message[event.chat_id])
    except (telethon.errors.MessageDeleteForbiddenError, KeyError):
        pass


async def delete_admin_message(admin_message_id):
    try:
        await bot.delete_messages(config.admin_id, message[admin_message_id])
    except (telethon.errors.MessageDeleteForbiddenError, KeyError):
        pass


async def invite_user_to_channel(user_to_add):
    # Добавление пользователя в чат
    async with TelegramClient(StringSession(session), api_id, api_hash) as client:
        try:
            await client.get_participants(config.open_channel)
            await client(InviteToChannelRequest(channel=config.channel, users=[user_to_add]))
            keyboard = [Button.inline('Назад', b'main')]
            await bot.send_message(user_to_add, 'Вы в чате', buttons=keyboard)
        except ValueError:
            keyboard = [Button.inline('Назад', b'main')]
            await bot.send_message(user_to_add, 'Для того чтобы попасть в закрытый канал, вы должны быть подписчиком '
                                                'канала ' + str(config.open_channel_name), buttons=keyboard)


async def remove_user_from_channel(user):
    # Удаление пользователя из чата
    async with TelegramClient(StringSession(session), api_id, api_hash) as client:
        try:
            await client.get_participants(config.channel)
            await client.kick_participant(config.channel, user)
        except ValueError as err:
            logging.error(err, exc_info=True)
            await bot.send_message(config.admin_id, 'Не удалось удалить\n'
                                   + str(db.get_user_info(user)))


@bot.on(events.NewMessage(pattern='/start'))
async def starthandler(event):
    # Ответ на первый запуск бота. Добавление пользователя в базу, если его там нет.
    entity = await bot.get_entity(event.chat_id)
    db.add_user_to_db(entity)
    await delete_message(event)
    keyboard = [Button.inline('Оплата', b'pay')], [Button.inline('Сколько дней подписки осталось?', b'check')], [
        Button.inline('Меня нет в чате, добавьте меня', b'reinvite')]

    message[event.chat_id] = await bot.send_message(event.chat_id, 'Выбери, что ты хочешь сделать.',
                                                    buttons=keyboard)


@bot.on(events.CallbackQuery(data=b'check'))
async def days_left(event):
    # Проверка оставшейся подписки
    await delete_message(event)
    keyboard = [Button.inline('Назад', b'main')]
    message[event.chat_id] = await bot.send_message(event.chat_id, 'Осталось '
                                                    + str(db.how_much_days_left(event.chat_id)) + ' дней',
                                                    buttons=keyboard)


@bot.on(events.CallbackQuery(data=b'reinvite'))
async def inviting(event):
    # Приглашение пользователя, если у него активна подписка, и его нет в чате. На случай случайного удаления
    await delete_message(event)
    keyboard = [Button.inline('Назад', b'main')]
    if db.how_much_days_left(event.chat_id):
        message[event.chat_id] = await bot.send_message(event.chat_id,
                                                        'Добавляем',
                                                        )
        await invite_user_to_channel(event.chat_id)
    else:
        message[event.chat_id] = await bot.send_message(event.chat_id,
                                                        'Ваша подписка неактивна',
                                                        buttons=keyboard)


@bot.on(events.CallbackQuery(data=b'pay'))
async def quantity_selection(event):
    # Функция выбора количества месяцев для оплаты
    await delete_message(event)
    keyboard = [Button.inline('1', b'month_1'), Button.inline('2', b'month_2')], [Button.inline('3', b'month_3'),
                                                                                  Button.inline('6', b'month_6')], [
                   Button.inline('12', b'month_12'), Button.inline('Назад', b'main')]
    message[event.chat_id] = await bot.send_message(event.chat_id, 'Выберите количество месяцев на оплату',
                                                    buttons=keyboard)


@bot.on(events.CallbackQuery(pattern='(?i)month.+'))
async def pay_confirm(event):
    # Подтверждение от пользователя, о том что он перевел платёж
    await delete_message(event)
    db.choosen_amount(int(str(event.data)[8:-1]) * 31, event.chat_id)
    keyboard = [Button.inline('Оплачено', b'payed')], [Button.inline('Назад', b'pay')]
    message[event.chat_id] = await bot.send_message(event.chat_id, "Для оплаты нужно:\n" + str(
        int(str(event.data)[8:-1]) * config.price + config.price_addition) + config.pay_message,
                                                    buttons=keyboard)


@bot.on(events.CallbackQuery(data=b'payed'))
async def payed(event):
    # Функция перевода на подтверждение платежа админом
    await delete_message(event)
    keyboard = [Button.inline('В главное меню', b'main')]
    message[event.chat_id] = await bot.send_message(event.chat_id,
                                                    'Сейчас мы проверим оплату и, если всё ок, в течение суток '
                                                    'добавим вас в канал',
                                                    buttons=keyboard)
    await confirm(event.chat_id)


@bot.on(events.CallbackQuery(data=b'main'))
async def back(event):
    # Возвращение в главное меню
    await starthandler(event)


async def confirm(userid):
    # Функция подтверждения оплаты от админа
    keyboard = [Button.inline('Подтвердить', data=str(userid))], [
        Button.inline('Не подтверждать', data='cancel' + str(userid))]
    message[str(userid)] = await bot.send_message(config.admin_id, 'Оплата\n'
                                                  + str(db.get_user_info(userid)), buttons=keyboard)


@bot.on(events.CallbackQuery())
async def confirmed(event):
    # Функция, вызывающаяся, после подтверждения о том, что админ подтвердил пришёдший платёж
    if event.chat_id == config.admin_id:
        if event.data.decode().startswith('cancel'):
            await delete_admin_message(event.data[6:].decode())
            await bot.send_message(int(event.data[6:].decode()), 'Оплату вам не подтвердили')

        if db.get_user_info(event.data.decode()):
            db.add_days_to_user(event.data.decode())
            await delete_admin_message(event.data.decode())
            message[int(event.data.decode())] = await bot.send_message(int(event.data.decode()), 'Добавляем вас в чат')
            await invite_user_to_channel(int(event.data.decode()))
