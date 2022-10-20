"""Configuration variables and API Tokens"""
from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher.filters.state import StatesGroup

API_TOKEN = ''
BITLY_TOKEN = ''
CONNECTION_STRING = "DRIVER={SQL Server Native Client 11.0};SERVER=;DATABASE=;\
                     UID=;PWD="
URL = "https://uszn-dobr.gov.ua"

class States(StatesGroup):
    """Bot user information input states"""
    waiting_for_jobid = State()
    waiting_for_month = State()
    waiting_for_day = State()
    waiting_for_time = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    data_accept = State()
