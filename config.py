from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = ''
BITLY_TOKEN = ''
connection_string = "DRIVER={SQL Server Native Client 11.0};SERVER=;DATABASE=;\
                     UID=;PWD="
URL = "https://uszn-dobr.gov.ua"

class States(StatesGroup):

    waiting_for_jobid = State()
    waiting_for_month = State()
    waiting_for_day = State()
    waiting_for_time = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    data_accept = State()

    
