import re
import os.path
import requests
import logging
import logging.handlers

from bs4 import BeautifulSoup as BS
from urllib.parse import urlparse

from config import URL

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING, filename='log_application.log')
file_handler = logging.FileHandler('log_application.log')
file_handler.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

HEADERS = {'user-agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36 OPR/74.0.3911.218',
           'accept':'*/*'}
def get_html (url):
    r = requests.get(url, headers = HEADERS)
    return r

def parse():
    html = get_html(URL)
    if html.status_code == 200:
        result = get_content (html.text)
        return result
    else:
        print ('Site connection Error')
        logger.warning("Site connection Error")

def download_image(url):
    try:
    	r = requests.get(url, allow_redirects=True)
    	a = urlparse(url)
    	filename = os.path.split(a.path)[1]
    	open("img\\" + filename, 'wb').write(r.content)

    	return "img\\" + filename
    except:
        print ('CDN connection Error')
        logger.warning("CDN connection Error")


def get_content(html):
    soup = BS (html, 'html.parser')
    info = {"id": soup.find ('article', class_ = 'post-standard').get('id'),\
            "title": soup.find ('div', class_ = 'post-content').find('h2').get_text(),\
            "link": soup.find ('div', class_ = 'post-content').find('h2').find('a').get('href'),\
            "img": soup.find ('article', class_ = 'post-standard').find ('div', class_ = 'post-thumbnail').find('a').find('noscript').find('img').get('src')
           }
    try:
        excerpt = {"excerpt": soup.find ('div', class_ = 'post-content').find ('div', class_ = 'entry excerpt entry-summary').find('p').get_text()}
    except:
        excerpt = {"excerpt": ''}
    info.update(excerpt)
    return info

