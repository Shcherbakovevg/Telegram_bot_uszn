"""Additional functionality: PDF ticket creation, checking input values,\
   checking new post is exist etc."""
import re

import logging
import fpdf

import parse

from db_connection import MsSql


FONTS_PATH = r"C:\\Windows\\Fonts\\"
FONT_NAME = r"arial.ttf"
FONT_SIZE = 14
fpdf.SYSTEM_TTFONTS = FONTS_PATH
db = MsSql()

def create_pdf(
    name,
    num,
    cat,
    date,
    time
):
    """Creating PDF file with queue ID"""
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.add_font('sysfont', '', FONTS_PATH + FONT_NAME , uni=True)
    pdf.set_font('sysfont', '', FONT_SIZE)
    pdf.image('img\\pdf_gerb\\gerb_100.jpg', x=100, y=0, w=20,)
    pdf.ln(15)
    pdf.cell(200, 0, txt="УСЗН", ln=1, align="C")
    pdf.ln(7)
    pdf.cell(200, 0, txt="ДОБРОПІЛЬСЬКОЇ МІСЬКОЇ РАДИ", ln=1, align="C")
    pdf.line(30, 37, 180, 37)
    pdf.set_line_width(0.5)
    pdf.set_draw_color(255, 255, 255)
    pdf.set_font('sysfont', '', 32)
    pdf.ln(15)
    pdf.cell(200, 0, txt=num, ln=1, align="C")
    pdf.set_font('sysfont', '', 12)
    pdf.ln(12)
    pdf.cell(200, 0, txt=cat, ln=1, align="C")
    pdf.set_line_width(0.2)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(30, 66, 180, 66)
    pdf.set_xy(30,62)
    pdf.cell(ln=0, h=22.0, align='L', w=75.0, txt="Дата реєстрації: " + date, border=0)
    pdf.cell(ln=0, h=22.0, align='R', w=75.0, txt="Час реєстрації: " + time, border=0)
    pdf.set_xy(30,72)
    pdf.cell(ln=0, h=22.0, align='L', w=75.0, txt="Відвідувач: " + name.title(), border=0)
    pdf.output('pdf\\'+name + num + ".pdf")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING, filename='log_application.log')
file_handler = logging.FileHandler('log_application.log')
file_handler.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

def new_post():
    """Checkin if new posts are exist"""
    try:
        info = parse.parse()
    except EnvironmentError:
        print ("Error. Site can't parse")
        logger.warning("Error. Site can't parse")
    try:
        if db.get_post()[0][0] != info['id']:
            new_key = info['id']
            db.upd_post (new_key)
            return info
        return False
    except EnvironmentError:
        print ("Error. User DB not avaliable")
        logger.warning("Error. User DB not avaliable")
    return None

def get_key(
    input_dic,
    data
):
    """Get dictionary key by value"""
    for key, value in input_dic.items():
        if value == data:
            return key
    return None

def valid_name(name):
    """Check name value is valid"""
    pattern = r"[а-я,А-Я,і,І,ї,Ї,є,Є,',\s,-]+"
    if re.fullmatch (pattern, name):
        return True
    return False

def valid_phone(phone):
    """Check phone value is valid"""
    pattern = r"(\+380|380|80|0)\d{9}"
    if re.fullmatch (pattern, phone):
        return True
    return False
