from telethon.tl.functions.channels import InviteToChannelRequest
from telethon import TelegramClient
from telethon import events
from telethon.tl.custom import Button
import asyncio
import logging

api_id = 000000
api_hash = '00000000000000000000000000'
bot_token = "000000000000000000000000"
adminid = 000000000
channel = 0000000000000

client = TelegramClient('anon', api_id, api_hash)
bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)


async def invite(channel, users_to_add):
    await client(InviteToChannelRequest(
        channel,
        [users_to_add]
    ))


async def remove(channel, user):
    async with TelegramClient('anon', api_id, api_hash) as client:
        await client.kick_participant(channel, user)


# asyncio.run(invite(channel, users_to_add))
# asyncio.run(remove(channel, user))


@bot.on(events.NewMessage(pattern='/start'))
async def starthandler(event):
    global d
    # Ответ на первый запуск бота, добавление пользователя в базу
    keyboard = [Button.inline('Оплата', b'pay')], [Button.inline('Сколько дней подписки осталось?', b'check')], [
        Button.inline('Всё оплачено, добавьте меня', b'reinvite')]
    entity = await bot.get_entity(event.chat_id)
    await bot.send_message(event.chat_id, 'Привет! Я бот для оплаты подписки. \nВыбери, что ты хочешь сделать.',
                           buttons=keyboard)
    if event.chat_id in d:
        print(d)
    else:
        d[event.chat_id] = [5, entity.id, entity.first_name, entity.last_name, entity.username, 0]
        print(d)


@bot.on(events.CallbackQuery(data=b'check'))
async def checkhandler(event):
    # Проверка оставшейся подписки
    try:
        await bot.send_message(event.chat_id, 'Осталось ' + str(d[event.chat_id][0]) + ' дней')
    except Exception as err:
        logging.error(err, exc_info=True)


@bot.on(events.CallbackQuery(data=b'reinvite'))
async def inviting(event):
    # Приглашение пользователя, если у него активна подписка, и его нет в чате.
    if d[event.chat_id][0] > 0:
        isparticipant = await asyncio.ensure_future(search(event.chat_id))
        if isparticipant:
            await bot.send_message(event.chat_id, 'Вы уже в чате')
        else:
            await bot.send_message(event.chat_id, 'Добавляю')
            # invite(event.chat_id)
    else:
        await bot.send_message(event.chat_id, 'Ваша подписка неактивна')

@bot.on(events.CallbackQuery(data=b'pay'))
async def payhandler(event):
    # Функция выбора количества месяцев для оплаты
    keyboard = [Button.inline('1', b'month_1')], [Button.inline('2', b'month_2')], [Button.inline('3', b'month_3')],\
        [Button.inline('6', b'month_6')], [Button.inline('12', b'month_12')]
    await bot.send_message(event.chat_id, 'Выберите количество месяцев на оплату',
                           buttons=keyboard)

@bot.on(events.CallbackQuery(pattern='(?i)month.+'))
async def monthhandler(event):
    await bot.send_message(event.chat_id, 'Ссылка для оплаты на ' + str(int(str(event.data)[8:-1]) * 15) + '$')
    print(d[event.chat_id])
    d[event.chat_id][5] = int(str(event.data)[8:-1]) * 31
    await asyncio.ensure_future(confirm(event.chat_id))

async def confirm(userid):
    keyboard = [Button.inline('Подтвердить', b'confirm')], [Button.inline('Не подтверждать', b'cancel')]
    m = await bot.send_message(adminid, str(d[userid]), buttons=keyboard)
    @bot.on(events.CallbackQuery())
    async def payhandler(event):
        if event.chat_id == adminid:
            if event.data == b'confirm':
                await bot.send_message(userid, 'Добавляю в канал')
                await bot.delete_messages(adminid, m)
                d[userid][0] += d[userid][5]
                # await asyncio.ensure_future(inviting(userid))
            if event.data == b'cancel':
                await bot.send_message(userid, 'Платёж не подтвеждён')
                await bot.delete_messages(adminid, m)
                return False

async def search(userid):
    # Функция поиска по пользователям канала
    users = await bot.get_participants(channel)
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


d = {}
bot.start()
bot.run_until_disconnected()

# def paying():
#     @bot.message_handler(commands=["start"])
#     def start(m):
#         global userid, d
#         key = types.InlineKeyboardMarkup()
#         key.add(types.InlineKeyboardButton(text='Оплата', callback_data="butt1"))
#         key.add(types.InlineKeyboardButton(text='Количество дней до окончания подписки', callback_data="butt2"))
#         bot.send_message(m.chat.id, 'Добро пожаловать, если уже оплатили, нажмите /newlink', reply_markup=key)
#         userid = m.chat.id
#         if userid in d:
#             print(d)
#         else:
#             d[userid] = [0, m.from_user.first_name, m.from_user.last_name, m.from_user.username, day]
#             print(d)
#
#     @bot.message_handler(commands=["newlink"])
#     def newlink(m):
#         global userid, d
#         if d[userid][0] > 0:
#             bot.send_message(userid, "Добавляю вас в канал)")
#             # adding()
#         if d[userid][0] == 0:
#             bot.send_message(userid, "Подписка неактивна")
#
#     @bot.callback_query_handler(func=lambda call: True)
#     def inline(c):
#         global userid, d, add
#         if c.data == 'butt1':
#             key = types.InlineKeyboardMarkup()
#             key.add(types.InlineKeyboardButton(text='1', callback_data="b1"))
#             key.add(types.InlineKeyboardButton(text='2', callback_data="b2"))
#             key.add(types.InlineKeyboardButton(text='3', callback_data="b3"))
#             key.add(types.InlineKeyboardButton(text='6', callback_data="b6"))
#             key.add(types.InlineKeyboardButton(text='12', callback_data="b12"))
#             bot.send_message(userid, 'Выберите количество месяцев', reply_markup=key)
#
#         if c.data == 'butt2':
#             if d[userid][0] > 0:
#                 bot.send_message(userid, 'Осталось ' + str(d[userid][0]) + ' дней')
#             if d[userid][0] == 0:
#                 bot.send_message(userid, 'Подписка неактивна')
#
#         if c.data == 'b1':
#             d[userid][4] = 31
#             key = types.InlineKeyboardMarkup()
#             key.add(types.InlineKeyboardButton(text='Оплачено', callback_data="payed"))
#             bot.send_message(userid, 'Ссылка на оплату 1 мес', reply_markup=key)
#         if c.data == 'b2':
#             d[userid][4] = 62
#             key = types.InlineKeyboardMarkup()
#             key.add(types.InlineKeyboardButton(text='Оплачено', callback_data="payed"))
#             bot.send_message(userid, 'Ссылка на оплату 2 мес', reply_markup=key)
#         if c.data == 'b3':
#             d[userid][4] = 93
#             key = types.InlineKeyboardMarkup()
#             key.add(types.InlineKeyboardButton(text='Оплачено', callback_data="payed"))
#             bot.send_message(userid, 'Ссылка на оплату 3 мес', reply_markup=key)
#         if c.data == 'b6':
#             d[userid][4] = 186
#             key = types.InlineKeyboardMarkup()
#             key.add(types.InlineKeyboardButton(text='Оплачено', callback_data="payed"))
#             bot.send_message(userid, 'Ссылка на оплату 6 мес', reply_markup=key)
#         if c.data == 'b12':
#             d[userid][4] = 372
#             key = types.InlineKeyboardMarkup()
#             key.add(types.InlineKeyboardButton(text='Оплачено', callback_data="payed"))
#             bot.send_message(userid, 'Ссылка на оплату 12 мес', reply_markup=key)
#
#         if c.data == 'payed':
#             confirm()
#             bot.send_message(userid, 'Если всё оплачено, в течение суток добавим вас в канал)')
#
#         if len(c.data) > 7:
#             d[int(c.data[4:])][0] = d[int(c.data[4:])][4]
#             bot.send_message(c.data[4:], "Добавляю вас в канал)")
#             add = c.data[4:]
#
#         if c.data == 'buttn':
#             print(userid)
#             bot.send_message(userid, "Оплату не подтвердили")
#
#
#     @bot.message_handler(content_types='text')
#     def message_reply(message):
#         pass
