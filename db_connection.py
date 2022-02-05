from datetime import datetime
from datetime import timedelta
import time
import calendar
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL

from config import connection_string

class MsSql():

    def __init__(self):
        """Подключениек БД"""
        self.connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
        self.engine = create_engine(self.connection_url)
        self.connection = self.engine.connect()
        self.connection = self.connection.execution_options(isolation_level="AUTOCOMMIT")

    #ВОЗВРАЩЕНИЕ МАКСИМАЛЬНОГО КОЛИЧЕСТВА ЗАПИСЕЙ НА ПЕРИОД
    def max_jobs(self, JobId):
        i = self.connection.execute ("SELECT Value FROM [Qmate].[dbo].[MaxJobSettings] WHERE JobId = ?", (JobId,))
        for row in i:
            return row[0]

    #ВОЗВРАЩЕНИЕ СПИСКА СВОБОДНЫХ ПЕРИОДОВ
    def get_free_periods(self, year, month, day, JobId):
        max_job = self.max_jobs(JobId)
        now = datetime.now ()
        periods_list = []
        if int(day) == int(now.day) and int(month) == int(now.month):
            now_time = str(now.hour+1) + ":" + str(now.minute) + ":00"
            per = self.connection.execute ("SELECT Time FROM [Qmate].[dbo].[PreliminaryShedule] WHERE Year = ? AND Month = ? AND Day = ? \
                                AND [" + str(JobId) + "_count] < ?", (year, month, day, max_job))
            for row in per:
                if int(row[0][:-6]) > int(now.hour):
                    periods_list.append(row[0][:-3])
        else:
            per = self.connection.execute ("SELECT Time FROM [Qmate].[dbo].[PreliminaryShedule] WHERE Year = ? AND Month = ? AND Day = ? \
                                AND [" + str(JobId) + "_count] < ?", (year, month, day, max_job))
            for row in per:
                periods_list.append(row[0][:-3])
        return periods_list

    #РЕЗЕРВИРОВАНИЕ/ОСВОБОЖДЕНИЕ ПЕРИОДА ПОСЛЕ ВЫБОРА ВРЕМЕНИ ПОЛЬЗОВАТЕЛЕМ
    def rezerv_time(self, year, month, day, time, JobId, act):
        now = datetime.now ()
        if act:
            self.connection.execute ("UPDATE [Qmate].[dbo].[PreliminaryShedule] SET [" + str(JobId) + "_count] = [" + str(JobId) + "_count] + 1 WHERE Year = ? \
                            AND Month = ? AND Day = ? AND Time LIKE ?", (year, month, day, time,))
        else:
            self.connection.execute ("UPDATE [Qmate].[dbo].[PreliminaryShedule] SET [" + str(JobId) + "_count] = [" + str(JobId) + "_count] - 1 WHERE Year = ? \
                            AND Month = ? AND Day = ? AND Time LIKE ?", (year, month, day, time,))

    #ВОЗВРАЩЕНИЕ СПИСКА СВОБОДНЫХ РАБОЧИХ ДНЕЙ
    def get_days (self, year, month, JobId):
        max_job = self.max_jobs(JobId)
        now = datetime.now ()
        day_list = set()
        if int(month) == int(now.month):
            per = self.connection.execute ("SELECT Day FROM [Qmate].[dbo].[PreliminaryShedule] WHERE Year = ? AND Month = ? AND Day >= ? AND IsWork = 1 \
                                    AND [" + str(JobId) + "_count] < ?", (year, month, now.day, max_job))
        else:
            per = self.connection.execute ("SELECT Day FROM [Qmate].[dbo].[PreliminaryShedule] WHERE Year = ? AND Month = ? AND IsWork = 1 \
                                    AND [" + str(JobId) + "_count] < ?", (year, month, max_job))
        for row in per:
            day_list.add(row[0])
        if not self.get_free_periods(year, month, now.day, JobId):
            try:
                day_list.remove(int(now.day))
            except:
                pass
        return day_list

    #ВОЗВРАЩЕНИЕ СПИСКА УСЛУГ
    def get_job_name(self):
        job_list = []
        per = self.connection.execute ("SELECT JobName_ua FROM [Qmate].[dbo].[JobIdDic]")
        for row in per:
            job_list.append(row[0])
        return job_list

    #ВОЗВРАЩЕНИЕ НОМЕР УСЛУГИ ПО НАЗВАНИЮ
    def get_num_name(self, name):
        per = self.connection.execute ("SELECT JobId FROM [Qmate].[dbo].[JobIdDic] WHERE JobName_ua LIKE ?", (name, ))
        for row in per:
            return row[0]

    #ВОЗВРАЩЕНИЕ ПОСЛЕДНЕГО НОМЕРА ЗАПИСИ НА ВЫБРАННЫЙ ДЕНЬ (NONE ЕСЛИ ЗАПИСЕЙ ЕЩЕ НЕ БЫЛО)
    def get_client_num(self, year, month, day):
        job_list = [101,102,103,104,105]
        now = datetime.now ()
        #start_day = str(year) + '-' + str(day) + '-' +  str(month) + ' 00:00:01.000'
        #fin_day = str(year) + '-' + str(day) + '-' +  str(month) + ' 23:59:59.000'
        start_day = str(year) + '-' + str(month) + '-' +  str(day) + ' 00:00:01.000'
        fin_day = str(year) + '-' + str(month) + '-' +  str(day) + ' 23:59:59.000'
        res = self.connection.execute ("SELECT MAX(OrderId) FROM [Qmate].[dbo].[PreliminaryRegs] WHERE TimeInHold BETWEEN ? AND ?", (start_day,fin_day))
        for row in res:
            if row[0]:
                return row[0]
            else:
                return 8001

    #ВНЕСЕНИЕ В ТАБЛИЦУ ПРЕДВАРИТЕЛЬНОЙ ЗАПИСИ
    def preliminary_reg(self, OrderId, JobId, year, month, day, time, name, phone):
        now = datetime.now ()
        uid = str(uuid.uuid4())
        now_time = datetime.now()
        #TimeInHold = str(year) + '-' + str(day) + '-' + str(month) + ' ' + time + '.000'
        TimeInHold = str(year) + '-' + str(month) + '-' + str(day) + ' ' + time + '.000'
        self.connection.execute ("INSERT INTO [Qmate].[dbo].[PreliminaryRegs] (TerminalId, OrderId, ClientId, SetTime, JobId, ResourceId, EmployeeId, TellerId, \
                        NeadApply, LanguageId, ClientPhone, ClientEmail, Commentary, ClientName, Information, TypeInformation, TimeInHold, SetId, \
                        SecureCode, UniqueCode, NotificationType, NotificationEvt, SegmentId) VALUES (1, ?, -1, ?, ?, -1, 0, -1, 0, 0, ?, '', '', \
                        ?, '', '', ?, 9, '00000000', ?, 0, 0, -1)", (OrderId, now_time, JobId, phone, name, TimeInHold, uid))

    def get_subs(self, status = 1):
        """Получаем активных подписчиков"""
        return self.connection.execute("SELECT * FROM [Qmate].[dbo].[subs] WHERE status = ?", (status,)).fetchall()
    
    def sub_exist(self, user_id):
        """Проверканаличия юзера в базе"""
        result = self.connection.execute("SELECT * FROM [Qmate].[dbo].[subs] WHERE user_id = ?", (user_id,)).fetchall()
        return bool(len(result))
    
    def add_sub(self, user_id, status):
        """Добавление подписчика"""
        return self.connection.execute("INSERT INTO [Qmate].[dbo].[subs] (user_id, status) VALUES (?, ?)", (user_id, status))
    
    def update_sub(self, user_id, status):
        """Обновление статуса подписки"""
        return self.connection.execute("UPDATE [Qmate].[dbo].[subs] SET status = ? WHERE user_id = ?", (status, user_id))
    
    def get_post (self):
        return self.connection.execute("SELECT post_id FROM [Qmate].[dbo].[posts]", ()).fetchall()
    
    def upd_post (self, post_id):
        return self.connection.execute("UPDATE [Qmate].[dbo].[posts] SET post_id = ?", (post_id,))