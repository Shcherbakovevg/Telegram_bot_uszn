"""MSSQL wiyh queue data connection"""
import uuid

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from config import CONNECTION_STRING


class MsSql():
    """MSSQL wiyh queue data connection"""

    def __init__(self):
        """DB connection init"""
        self.connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": CONNECTION_STRING})
        self.engine = create_engine(self.connection_url)
        self.connection = self.engine.connect()
        self.connection = self.connection.execution_options(isolation_level="AUTOCOMMIT")

    def max_jobs(self, job_id):
        """Return max priod records value"""
        i = self.connection.execute ("SELECT Value FROM [Qmate].[dbo].[MaxJobSettings] WHERE \
                                     JobId = ?", (job_id,))
        for row in i:
            return row[0]

    def get_free_periods(
        self,
        year,
        month,
        day,
        job_id
    ):
        """Return free time periods list"""
        max_job = self.max_jobs(job_id)
        now = datetime.now ()
        periods_list = []
        if int(day) == int(now.day) and int(month) == int(now.month):
            per = self.connection.execute ("SELECT Time FROM [Qmate].[dbo].[PreliminaryShedule] \
                                            WHERE Year = ? AND Month = ? AND Day = ? \
                                            AND [" + str(job_id) + "_count] < ?", (year, month, day, max_job))
            for row in per:
                if int(row[0][:-6]) > int(now.hour):
                    periods_list.append(row[0][:-3])
        else:
            per = self.connection.execute ("SELECT Time FROM [Qmate].[dbo].[PreliminaryShedule] \
                                           WHERE Year = ? AND Month = ? AND Day = ? \
                                           AND [" + str(job_id) + "_count] < ?", (year, month, day, max_job))
            for row in per:
                periods_list.append(row[0][:-3])
        return periods_list

    def rezerv_time(
        self,
        year,
        month,
        day,
        time,
        job_id,
        act
    ):
        """Reserving/returning time after user chosen"""
        if act:
            self.connection.execute ("UPDATE [Qmate].[dbo].[PreliminaryShedule] \
                                     SET [" + str(job_id) + "_count] = [" + str(job_id) + "_count] + 1 \
                                     WHERE Year = ? \
                                     AND Month = ? AND Day = ? \
                                     AND Time LIKE ?", (year, month, day, time,))
        else:
            self.connection.execute ("UPDATE [Qmate].[dbo].[PreliminaryShedule] \
                                     SET [" + str(job_id) + "_count] = [" + str(job_id) + "_count] - 1 \
                                     WHERE Year = ? \
                                     AND Month = ? AND Day = ? \
                                     AND Time LIKE ?", (year, month, day, time,))

    def get_days (
        self,
        year,
        month,
        job_id
    ):
        """Return free work days list"""
        max_job = self.max_jobs(job_id)
        now = datetime.now ()
        day_list = set()
        if int(month) == int(now.month):
            per = self.connection.execute ("SELECT Day FROM [Qmate].[dbo].[PreliminaryShedule] WHERE Year = ? \
                                           AND Month = ? AND Day >= ? AND IsWork = 1 \
                                           AND [" + str(job_id) + "_count] < ?", (year, month, now.day, max_job))
        else:
            per = self.connection.execute ("SELECT Day FROM [Qmate].[dbo].[PreliminaryShedule] \
                                           WHERE Year = ? AND Month = ? AND IsWork = 1 \
                                           AND [" + str(job_id) + "_count] < ?", (year, month, max_job))
        for row in per:
            day_list.add(row[0])
        if not self.get_free_periods(year, month, now.day, job_id):
            try:
                day_list.remove(int(now.day))
            except IndexError as error:
                print (error)
        return day_list

    def get_job_name(self):
        """Return jobs list"""
        job_list = []
        per = self.connection.execute ("SELECT JobName_ua FROM [Qmate].[dbo].[JobIdDic]")
        for row in per:
            job_list.append(row[0])
        return job_list

    def get_num_name(self, name):
        """Return job id by name"""
        per = self.connection.execute ("SELECT JobId FROM [Qmate].[dbo].[JobIdDic] \
                                       WHERE JobName_ua LIKE ?", (name, ))
        for row in per:
            return row[0]

    def get_client_num(
        self,
        year,
        month,
        day
    ):
        """Return last record id for day"""
        start_day = str(year) + '-' + str(month) + '-' +  str(day) + ' 00:00:01.000'
        fin_day = str(year) + '-' + str(month) + '-' +  str(day) + ' 23:59:59.000'
        res = self.connection.execute ("SELECT MAX(OrderId) FROM [Qmate].[dbo].[PreliminaryRegs] \
                                       WHERE TimeInHold BETWEEN ? AND ?", (start_day,fin_day))
        for row in res:
            if row[0]:
                return row[0]
            return 8001

    def preliminary_reg(
        self,
        order_id,
        job_id,
        year,
        month,
        day,
        time,
        name,
        phone
    ):
        """Adding prelaminary table record"""
        uid = str(uuid.uuid4())
        now_time = datetime.now()
        time_in_hold = str(year) + '-' + str(month) + '-' + str(day) + ' ' + time + '.000'
        self.connection.execute ("INSERT INTO [Qmate].[dbo].[PreliminaryRegs] (TerminalId, OrderId, \
                                 ClientId, SetTime, JobId, ResourceId, EmployeeId, TellerId, \
                                 NeadApply, LanguageId, ClientPhone, ClientEmail, Commentary, ClientName, \
                                 Information, TypeInformation, TimeInHold, SetId, \
                                 SecureCode, UniqueCode, NotificationType, NotificationEvt, SegmentId) \
                                 VALUES (1, ?, -1, ?, ?, -1, 0, -1, 0, 0, ?, '', '', \
                                 ?, '', '', ?, 9, '00000000', ?, 0, 0, -1)" , (order_id, now_time, job_id, phone, name, time_in_hold, uid))

    def get_subs(self, status = 1):
        """Return list of subscribers"""
        return self.connection.execute("SELECT * FROM [Qmate].[dbo].[subs] \
                                       WHERE status = ?", (status,)).fetchall()

    def sub_exist(self, user_id):
        """Check is user in DB"""
        result = self.connection.execute("SELECT * FROM [Qmate].[dbo].[subs] \
                                         WHERE user_id = ?", (user_id,)).fetchall()
        return bool(len(result))

    def add_sub(self, user_id, status):
        """Adding user to DB"""
        return self.connection.execute("INSERT INTO [Qmate].[dbo].[subs] (user_id, status) \
                                       VALUES (?, ?)", (user_id, status))

    def update_sub(self, user_id, status):
        """Refresh user state"""
        return self.connection.execute("UPDATE [Qmate].[dbo].[subs] \
                                       SET status = ? WHERE user_id = ?", (status, user_id))

    def get_post (self):
        """Getting last post id"""
        return self.connection.execute("SELECT post_id FROM [Qmate].[dbo].[posts]", ()).fetchall()

    def upd_post (self, post_id):
        """Update last post id"""
        return self.connection.execute("UPDATE [Qmate].[dbo].[posts] \
                                       SET post_id = ?", (post_id,))
