import logging
import asyncio
import aioschedule
import bitlyshortener
import calendar
import logging.handlers

from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils import exceptions
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand, InputFile

import parse
import messages
from db_connection import MsSql
from config import States, API_TOKEN, BITLY_TOKEN
from additional_func import new_post, get_key, valid_name, valid_phone, create_pdf

#Подключение bitly_api
tokens_pool = [BITLY_TOKEN]
shortener = bitlyshortener.Shortener(tokens=tokens_pool, max_cache_size=256)

# создаем обработчики логов
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.handlers.RotatingFileHandler(filename="log_application.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# добавляем обработчики логов
logger.addHandler(file_handler)

# инициализируем бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# инициализируем соединение с БД
db = MsSql()

@dp.message_handler(state=States.waiting_for_month)
async def month_chosen(message: types.Message, state: FSMContext):
    """logger.error('Warning!')"""
    try:
        job_list = db.get_job_name()
    except Exception as exc:
        print(exc)
        print ("SQL connection error. Can't get data (job_list)")
        await message.answer (messages.Err_msg, reply_markup=types.ReplyKeyboardRemove())
        await message.answer(messages.btn_main_menu, reply_markup=inl_keyboard)
        await state.finish()
        logger.warning("SQL connection error. Can't get data (job_list)")
        return
    if message.text.lower() == messages.btn_main_menu:
        await state.finish()
        await message.answer(messages.menu_back, reply_markup=types.ReplyKeyboardRemove())
        await message.answer (messages.Start_msg, reply_markup=inl_keyboard)
        return
    elif message.text not in job_list:
        await message.answer("Будь ласка, оберіть послугу, за допомогою клаіватури")
        return
    now = datetime.now()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if now.month == 12:
        keyboard.row(get_key(messages.MonthId, str(now.month)), get_key(messages.MonthId, "1"))
    else:
            keyboard.row(get_key(messages.MonthId, str(now.month)), get_key(messages.MonthId, str(now.month + 1)))
    keyboard.row (messages.back)
    await message.answer('Оберіть місяць:', reply_markup=keyboard)
    await States.waiting_for_day.set()
    await state.update_data(chosen_job=message.text.lower())
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

@dp.message_handler(state=States.waiting_for_day)
async def day_chosen(message: types.Message, state: FSMContext):
    now = datetime.now()
    if now.month == 12:
        month_list = [(get_key(messages.MonthId, str(now.month))).lower(), (get_key(messages.MonthId, "1").lower())]
    else:
        month_list = [(get_key(messages.MonthId, str(now.month))).lower(), (get_key(messages.MonthId, str(now.month + 1)).lower())]
    if message.text.lower() == messages.back:
        try:
            job_list = db.get_job_name()
        except Exception as exc:
            print(exc)
            print ("SQL connection error. Can't get data (job_list)")
            await message.answer (messages.Err_msg, reply_markup=types.ReplyKeyboardRemove())
            await message.answer(messages.menu_back, reply_markup=inl_keyboard)
            await state.finish()
            logger.warning("SQL connection error. Can't get data (job_list)")
            return
        await States.waiting_for_month.set()
        await state.update_data(chosen_month=message.text.lower())
        if now.month == 12 and int(messages.MonthId[(user_data['chosen_month'])]) == 1:
            await state.update_data(chosen_year=now.year + 1)
        else:
            await state.update_data(chosen_year=now.year)
        await message.answer(messages.back_msg)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for i in job_list:
            keyboard.insert(i)
        keyboard.row (messages.btn_main_menu)
        await message.answer("Оберіть тему візиту:", reply_markup=keyboard)
        return
    elif message.text.lower() not in month_list:
        await message.answer("Будь ласка, оберіть місяць, за допомогою клаіватури")
        return    
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row (messages.back)
        await state.update_data(chosen_month=message.text.lower())
        if now.month == 12 and int(messages.MonthId[(user_data['chosen_month'])]) == 1:
            await state.update_data(chosen_year=now.year + 1)
        else:
            await state.update_data(chosen_year=now.year)
        user_data = await state.get_data()
        try:
            await state.update_data(day_list=db.get_days(user_data['chosen_year'], messages.MonthId[(user_data['chosen_month']).title()],\
                                db.get_num_name(user_data['chosen_job'])))
        except Exception as exc:
            print(exc)
            print ("SQL connection error. Can't get data (day_list)")
            await message.answer (messages.Err_msg, reply_markup=types.ReplyKeyboardRemove())
            if now.month == 12:
                keyboard.row(get_key(messages.MonthId, str(now.month)), get_key(messages.MonthId, "1"))
            else:
                    keyboard.row(get_key(messages.MonthId, str(now.month)), get_key(messages.MonthId, str(now.month + 1)))
            await state.finish()
            logger.warning("SQL connection error. Can't get data (day_list)")
            return
        user_data = await state.get_data()
        await message.answer("Оберіть день у діапазоні від " + str(min(user_data['day_list'])) + " до " \
                         + str(max(user_data['day_list'])), reply_markup=keyboard)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row (messages.back)
        await States.waiting_for_time.set()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

@dp.message_handler(state=States.waiting_for_time)
async def time_chosen(message: types.Message, state: FSMContext):
    now = datetime.now()
    user_data = await state.get_data()
    if message.text.lower() == messages.back:
        await States.waiting_for_day.set()
        await message.answer(messages.back_msg)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if now.month == 12:
            keyboard.row(get_key(messages.MonthId, str(now.month)), get_key(messages.MonthId, "1"))
        else:
                keyboard.row(get_key(messages.MonthId, str(now.month)), get_key(messages.MonthId, str(now.month + 1)))
        keyboard.row (messages.back)
        await message.answer("Оберіть місяць:", reply_markup=keyboard)
    elif message.text.lower() == messages.btn_main_menu:
            await state.finish()
            await message.answer(messages.menu_back, reply_markup=types.ReplyKeyboardRemove())
            await message.answer (messages.Start_msg ,reply_markup=inl_keyboard)
            return
    elif int(message.text.lower()) not in user_data['day_list']:
        if int(message.text.lower()) > max(user_data['day_list']):
            await message.answer("Будь ласка, оберіть день у діапазоні від " + str(min(user_data['day_list'])) + " до "\
                                 + str(max(user_data['day_list'])))
        for i in sorted(list(user_data['day_list'])):
            if i > int (message.text.lower()):
                next_day = i
                break
        await message.answer("Обраний день вихідний, або повністю зайнятий. Наступний вільний день "\
                             + str(next_day) + " " + get_key(messages.MonthId_text, messages.MonthId[(user_data['chosen_month']).title()])\
                             + ". Будь ласка, оберіть день у діапазоні від " + str(min(user_data['day_list'])) + " до "\
                             + str(max(user_data['day_list'])))
        return  
    else:
        await state.update_data(chosen_day=message.text.lower())
        user_data = await state.get_data()
        try:
            await state.update_data(periods_list=db.get_free_periods (user_data['chosen_year'],\
                                    messages.MonthId[(user_data['chosen_month']).title()],\
                                    user_data['chosen_day'], db.get_num_name(user_data['chosen_job'])))
        except Exception as exc:
            print(exc)
            print ("SQL connection error. Can't get data (periods_list)")
            await message.answer (messages.Err_msg, reply_markup=types.ReplyKeyboardRemove())
            await message.answer(messages.menu_back, reply_markup=inl_keyboard)
            await state.finish()
            logger.warning("SQL connection error. Can't get data (periods_list)")
            return 
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=6)
        user_data = await state.get_data()
        for period in user_data['periods_list']:
            keyboard.insert(period)
        keyboard.row (messages.back)
        await message.answer("Оберіть час візиту:", reply_markup=keyboard)
        await States.waiting_for_name.set()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

@dp.message_handler(state=States.waiting_for_name)
async def name_chosen(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    now = datetime.now()
    last_day = calendar.monthrange(now.year, now.month)[1]
    if message.text.lower() == messages.back:
        await States.waiting_for_time.set()
        await message.answer(messages.back_msg)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row (messages.back)
        await message.answer("Оберіть день у діапазоні від " + str(min(user_data['day_list'])) + " до " +\
                             str(max(user_data['day_list'])), reply_markup=keyboard)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row (messages.back)
    elif message.text.lower() not in user_data['periods_list']:
        await message.answer("Будь ласка, Оберіть час візиту за допомогою клавіатури")
        return
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row (messages.back)
        await message.answer(
        "Введіть, будь ласка, прізвище, ім'я, по батькові", reply_markup=keyboard)
        await States.waiting_for_phone.set()
        await state.update_data(chosen_time=message.text.lower())
        user_data = await state.get_data()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        try:
            await state.update_data(job_id=db.get_num_name(user_data['chosen_job']))
        except Exception as exc:
            print(exc)
            print ("SQL connection error. Can't get data (job_id)")
            await message.answer (messages.Err_msg, reply_markup=types.ReplyKeyboardRemove())
            await message.answer(messages.menu_back, reply_markup=inl_keyboard)
            await state.finish()
            logger.warning("SQL connection error. Can't get data (job_id)")
            return
        try:
            user_data = await state.get_data()
            db.rezerv_time(user_data['chosen_year'], messages.MonthId[(user_data['chosen_month']).title()], user_data['chosen_day'],\
                           user_data['chosen_time'] + ':00', user_data['job_id'], True)
        except Exception as exc:
            print(exc)
            print ("SQL connection error. Can't update data (rezerv_time)")
            await message.answer (messages.Err_msg, reply_markup=types.ReplyKeyboardRemove())
            await message.answer(messages.menu_back, reply_markup=inl_keyboard)
            await state.finish()
            logger.warning("SQL connection error. Can't update data (rezerv_time)")
            return

@dp.message_handler(state=States.waiting_for_phone)
async def phone_chosen(message: types.Message, state: FSMContext):
    if message.text.lower() == messages.back:
        user_data = await state.get_data()
        await States.waiting_for_name.set()
        await message.answer(messages.back_msg)
        try:
            db.rezerv_time(user_data['chosen_year'], messages.MonthId[(user_data['chosen_month']).title()], user_data['chosen_day'],\
                           user_data['chosen_time'] + ':00', user_data['job_id'], False)
        except Exception as exc:
            print(exc)
            print ("SQL connection error. Can't update data (delete_rezerv_time)")
            await message.answer (messages.Err_msg, reply_markup=types.ReplyKeyboardRemove())
            await message.answer(messages.menu_back, reply_markup=inl_keyboard)
            await state.finish()
            logger.warning("SQL connection error. Can't update data (delete_rezerv_time)")
            return
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=6)
        for period in user_data['periods_list']:
            keyboard.insert(period)
        keyboard.row (messages.back)
        await message.answer("Оберіть час візиту:", reply_markup=keyboard)
    elif not valid_name (message.text):
        await message.answer("Введено некоректні дані. Введіть, будь ласка, прізвище, ім'я, по батькові")
        return
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row (messages.back)
        await message.answer(
        "Вкажіть, будь ласка, Ваш номер телефону", reply_markup=keyboard)
        await States.data_accept.set()
        await state.update_data(chosen_name=message.text.lower())
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
@dp.message_handler(state=States.data_accept)
async def data_accept(message: types.Message, state: FSMContext):
    if message.text.lower() == messages.back:
        await States.waiting_for_phone.set()
        await message.answer(messages.back_msg)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.row (messages.back)
        await message.answer("Введіть, будь ласка, прізвише, ім'я, по батькові", reply_markup=keyboard)
    elif not valid_phone (message.text):
        await message.answer("Введено некоректні дані. Вкажіть, будь ласка, Ваш номер телефону у форматі 0951234567")
        return
    else:
        await state.update_data(chosen_phone=message.text.lower())
        user_data = await state.get_data()
        try:
            await state.update_data(OrderId=db.get_client_num(user_data['chosen_year'],\
                                    messages.MonthId[(user_data['chosen_month']).title()],\
                                    user_data['chosen_day']) + 1)
        except Exception as exc:
            print(exc)
            print ("SQL connection error. Can't get data (order_id)")
            await message.answer (messages.Err_msg, reply_markup=types.ReplyKeyboardRemove())
            await message.answer(messages.menu_back, reply_markup=inl_keyboard)
            await state.finish()
            logger.warning("SQL connection error. Can't get data (order_id)")
            return
        try:
            user_data = await state.get_data()
            db.preliminary_reg (user_data['OrderId'], db.get_num_name(user_data['chosen_job']), user_data['chosen_year'],\
                                messages.MonthId[(user_data['chosen_month']).title()], user_data['chosen_day'],\
                                user_data['chosen_time'], user_data['chosen_name'], user_data['chosen_phone'])
            await message.answer("Вітаємо❗ Ви записані на прийом! Ваш номер талону " + str(user_data['OrderId'])\
                                 + " ✅\n Чекаємо Вас в Управлінні соціального захисту населення "\
                                 + user_data['chosen_day'] + " " + get_key(messages.MonthId_text,\
                                 messages.MonthId[(user_data['chosen_month']).title()]) + " в " +\
                                 user_data['chosen_time']\
                                 + " ⏰ за адресою м. Добропілля, пр-т Шевченка 15. Не забудьте взяти документи та захисну маску😷",\
                                 reply_markup=types.ReplyKeyboardRemove())
            try:
                create_pdf(str(user_data['chosen_name']), str(user_data['OrderId']),\
                               str(user_data['chosen_job']), str(user_data['chosen_day'] + " "\
                               + get_key(messages.MonthId_text, messages.MonthId[(user_data['chosen_month']).title()])),\
                               str(user_data['chosen_time']))
            except Exception as exc:
                print(exc)
                logger.warning("PDF creation error.")
            try:
                            path = "pdf\\"+str(user_data['chosen_name'])+str(user_data['OrderId'])+".pdf"
                            with open(path, 'rb') as pdf:
                                    await bot.send_document(message.chat.id, pdf, caption="Завантажити талон електронної черги")
            except Exception as exc:
                print(exc)
                logger.warning("PDF sending error.")
            await message.answer(messages.menu_back, reply_markup=inl_keyboard)
            await state.finish()
        
        except Exception as exc:
            print(exc)
            print ("SQL connection error. Can't update data (order_data)")
            await message.answer (messages.Err_msg, reply_markup=types.ReplyKeyboardRemove())
            await message.answer(messages.menu_back, reply_markup=inl_keyboard)
            await state.finish()
            logger.warning("SQL connection error. Can't update data (order_data)")
            return

inl_keyboard = types.InlineKeyboardMarkup(row_width=2)
sub = types.InlineKeyboardButton(text = '✅ Підписатись на новини', callback_data = 'menu_3')
unsub = types.InlineKeyboardButton(text = '❌ Відписатись від розсилки', callback_data = 'menu_4')
cont = types.InlineKeyboardButton(text = "✉ Звя'затись з нами", callback_data = 'menu_1')
prelim = types.InlineKeyboardButton(text = '📅 Записатись на прийом', callback_data = 'menu_2')
inl_keyboard.add(cont, prelim, sub, unsub)

#Команда старт
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
        await message.answer (messages.Start_msg ,reply_markup=inl_keyboard)

#Обработка событий кнопок стартового меню
@dp.callback_query_handler(text_contains='menu_')
async def menu(call: types.CallbackQuery):
        if call.data and call.data.startswith("menu_"):
                code = call.data[-1:]
                if code.isdigit():
                        code = int(code)
                if code == 1:
                        await call.message.answer(messages.Help_msg ,disable_web_page_preview = True,\
                                                  reply_markup=inl_keyboard)
                        await call.answer()
                if code == 2:
                        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                        try:
                            job_list = db.get_job_name()
                            for i in job_list:
                                keyboard.insert(i)
                            keyboard.row (messages.btn_main_menu)
                            await call.message.answer("Оберіть тему візиту:",\
                                                      reply_markup=keyboard)
                            await States.waiting_for_month.set()
                            await call.answer()
                        except Exception as exc:
                            print(exc)
                            print ("SQL connection error. Can't get data (job_list)")
                            await call.message.answer (messages.Err_msg,\
                                                       reply_markup=types.ReplyKeyboardRemove())
                            await call.message.answer(messages.menu_back,\
                                                      reply_markup=inl_keyboard)
                            await call.answer()
                            logger.warning("SQL connection error. Can't get data (job_list)")
                if code == 3:
                        if(not db.sub_exist(call.message.chat.id)):
                                # если юзера нет в базе, добавляем его
                                db.add_sub(call.message.chat.id, 1)
                        else:
                                # если он уже есть, то просто обновляем ему статус подписки
                                db.update_sub(call.message.chat.id, 1)
                        await call.message.answer("Дякуємо, Ви успішно підписалися! Очікуйте на новини!",\
                                              reply_markup=inl_keyboard)
                        await call.answer()
                if code == 4:
                        if(not db.sub_exist(call.message.chat.id)):
                                # если юзера нет в базе, добавляем его с неактивной подпиской (запоминаем)
                                db.add_sub(call.message.chat.id, 0)
                                await call.message.answer("Ви ще не підписані на розсилку. Для того щоб отримувати останні новини використайте кнопку 'Підписатись на новини' або команду /subscribe",\
                                                          reply_markup=inl_keyboard)
                        else:
                                 # если он уже есть, то просто обновляем ему статус подписки
                                db.update_sub(call.message.chat.id, 0)
                                await call.message.answer("Ви успішно відписались від розсилки новин.",\
                                                      reply_markup=inl_keyboard)
                        await call.answer()

#Команда помощи
@dp.message_handler(commands=['help'])
async def help(message: types.Message):
        logger.critical("Situation is critical")
        logger.info("Information message")
        await message.answer (messages.Help_msg ,disable_web_page_preview = True, reply_markup=inl_keyboard)
        logger.critical("Situation is critical")
        logger.info("Information message")

@dp.message_handler()
async def msg(message: types.Message):
    await message.answer("Скористайтесь клавіатурою, щоб обрати команду", reply_markup=inl_keyboard)

# Рассылка новостей с сайта
async def scheduled(wait_for):
        while True:
            await asyncio.sleep(wait_for)
            # проверяем наличие новых постов
            nfo = new_post()
            if(nfo):
                try:
                    short_link = shortener.shorten_urls([nfo['link']])
                except Exception as exc:
                    print(exc)
                    print ("Bitly API connection error. Can't short link")
                    logger.warning("Bitly API connection error. Can't short link")
                # получаем список подписчиков бота
                subscriptions = db.get_subs()
                # отправляем всем новость
                for s in subscriptions:
                    with open(parse.download_image(nfo['img']), 'rb') as photo:
                        try:
                            await bot.send_photo(
                                s[1],
                                photo,
                                caption = "<b>" + nfo['title'] + "</b>" + "\n\n"\
                                          + nfo['excerpt'] + "\n\n" + short_link[0],
                                disable_notification = True,
                                parse_mode="HTML",
                                reply_markup=inl_keyboard
                                )
                        except:
                            exceptions.BotBlocked(message='Warning. Bot blocked one of the users')
                            logger.warning("Warning. Bot blocked one of the users")
                nfo = False
        
async def on_startup(_):
        asyncio.create_task(scheduled(10))

async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()
      
# запускаем лонг поллинг
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup, on_shutdown=shutdown)

